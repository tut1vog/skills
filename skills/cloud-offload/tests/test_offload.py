"""Offline tests for offload.py using fake aws/ssh/rsync shims on PATH.

Run:  python3 -m unittest discover -s skills/cloud-offload/tests -v
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "scripts" / "offload.py"
BIN = HERE / "bin"


class OffloadTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "home"
        self.home.mkdir()
        (self.home / "id_ed25519").write_text("PRIVATE")
        (self.home / "id_ed25519.pub").write_text("ssh-ed25519 AAAA fake@test")
        (self.home / "config.json").write_text(json.dumps({"provider": "aws", "aws": {"profile": "cloud-offload"}}))
        self.log = Path(self.tmp.name) / "calls.log"
        self.work = Path(self.tmp.name) / "work"
        self.work.mkdir()
        for f in BIN.iterdir():
            f.chmod(0o755)

    def tearDown(self):
        self.tmp.cleanup()

    def run_offload(self, *args, env=None, expect=0):
        e = {**os.environ, "PATH": f"{BIN}:{os.environ['PATH']}", "CLOUD_OFFLOAD_HOME": str(self.home),
             "OFFLOAD_FAKE_LOG": str(self.log)}
        e.update(env or {})
        p = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, env=e, cwd=self.work)
        if expect is not None:
            self.assertEqual(p.returncode, expect, f"stdout={p.stdout}\nstderr={p.stderr}")
        return p

    def calls(self):
        if not self.log.exists():
            return []
        return [json.loads(l) for l in self.log.read_text().splitlines()]

    def aws_calls(self, op):
        return [c for c in self.calls() if c and c[0] != "ssh" and op in c]

    def state(self):
        return json.loads((self.home / "instances.json").read_text())

    def seed_state(self):
        (self.home / "instances.json").write_text(json.dumps({"instances": {"default": {
            "provider": "aws", "id": "i-fake001", "ip": "203.0.113.10", "type": "c7i.xlarge",
            "pricing": "spot", "created": "2026-01-01T00:00:00Z", "deadline": "2026-01-01T08:00:00Z",
            "ssh_user": "ubuntu", "region": "ap-southeast-1"}}}))

    # -- up

    def test_up_spot_default_tags_ttl_and_state(self):
        p = self.run_offload("up")
        out = json.loads(p.stdout)
        self.assertEqual(out["id"], "i-fake001")
        self.assertEqual(out["ip"], "203.0.113.10")
        self.assertEqual(out["pricing"], "spot")
        self.assertTrue(out["ssh_ready"])
        run = self.aws_calls("run-instances")[0]
        self.assertIn("--instance-market-options", run)
        self.assertIn("--instance-initiated-shutdown-behavior", run)
        self.assertIn("terminate", run)
        tags = run[run.index("--tag-specifications") + 1]
        self.assertIn("cloud-offload:managed", tags)
        self.assertIn("cloud-offload:deadline", tags)
        self.assertEqual(self.state()["instances"]["default"]["id"], "i-fake001")
        self.assertTrue(self.aws_calls("import-key-pair"), "public key should be imported when missing")

    def test_up_spot_fallback_to_on_demand(self):
        p = self.run_offload("up", env={"OFFLOAD_FAKE_SPOT_FAIL": "1"})
        self.assertEqual(json.loads(p.stdout)["pricing"], "on-demand (spot fallback)")
        runs = self.aws_calls("run-instances")
        self.assertEqual(len(runs), 2)
        self.assertIn("--instance-market-options", runs[0])
        self.assertNotIn("--instance-market-options", runs[1])

    def test_up_on_demand_flag(self):
        p = self.run_offload("up", "--on-demand")
        self.assertEqual(json.loads(p.stdout)["pricing"], "on-demand")
        self.assertNotIn("--instance-market-options", self.aws_calls("run-instances")[0])

    def test_up_refuses_large_and_gpu_without_flag(self):
        p = self.run_offload("up", "--type", "m7i.8xlarge", expect=1)
        self.assertIn("safety cap", p.stderr)
        p = self.run_offload("up", "--type", "g5.xlarge", expect=1)
        self.assertIn("safety cap", p.stderr)
        self.assertEqual(self.aws_calls("run-instances"), [])
        self.run_offload("up", "--type", "m7i.8xlarge", "--allow-large")
        self.assertEqual(len(self.aws_calls("run-instances")), 1)

    def test_up_refuses_duplicate_name(self):
        self.seed_state()
        p = self.run_offload("up", expect=1)
        self.assertIn("already exists", p.stderr)

    def test_up_skips_key_import_when_present(self):
        self.run_offload("up", env={"OFFLOAD_FAKE_KEY_EXISTS": "1"})
        self.assertEqual(self.aws_calls("import-key-pair"), [])

    # -- run / status / logs

    def test_run_inline_writes_script_and_returns_job(self):
        self.seed_state()
        p = self.run_offload("run", "--", "echo", "hi", ">", "$OUT/x.txt")
        out = json.loads(p.stdout)
        self.assertTrue(out["job"].startswith("j-"))
        self.assertEqual(out["state"], "running")
        ssh = [c for c in self.calls() if c[0] == "ssh"][-1]
        script = ssh[-1]["stdin"]
        self.assertIn("echo hi > $OUT/x.txt", script)
        self.assertIn("nohup setsid", script)
        self.assertIn("ubuntu@203.0.113.10", ssh)

    def test_run_script_file(self):
        self.seed_state()
        f = self.work / "job.sh"
        f.write_text("apt-get install -y foo\nfoo --run\n")
        self.run_offload("run", "--script", str(f))
        script = [c for c in self.calls() if c[0] == "ssh"][-1][-1]["stdin"]
        self.assertIn("#!/usr/bin/env bash\napt-get install -y foo\nfoo --run", script)

    def test_run_requires_exactly_one_input(self):
        self.seed_state()
        p = self.run_offload("run", expect=1)
        self.assertIn("exactly one", p.stderr)

    def test_run_wait_returns_exit_code_and_tail(self):
        self.seed_state()
        p = self.run_offload("run", "--wait", "--", "true", env={"OFFLOAD_FAKE_JOB_STATE": "exited"})
        out = json.loads(p.stdout)
        self.assertEqual(out["state"], "exited")
        self.assertEqual(out["exit_code"], 0)
        self.assertEqual(out["tail"]["stdout"], "hello world\n")
        self.assertEqual(out["tail"]["stderr"], "some warning\n")

    def test_status_job_running(self):
        self.seed_state()
        p = self.run_offload("status", "j-x")
        out = json.loads(p.stdout)
        self.assertEqual(out["state"], "running")
        self.assertEqual(out["elapsed_seconds"], 60)
        self.assertEqual(out["out_files"], 1)

    def test_status_reports_interrupted_when_instance_gone(self):
        self.seed_state()
        gone = json.dumps([{"id": "i-fake001", "state": "terminated", "name": "default"}])
        p = self.run_offload("status", "j-x", env={"OFFLOAD_FAKE_SSH_RC": "255", "OFFLOAD_FAKE_INSTANCES": gone})
        self.assertEqual(json.loads(p.stdout)["state"], "interrupted")

    def test_status_instance_level(self):
        self.seed_state()
        p = self.run_offload("status", env={"OFFLOAD_FAKE_SSH_OUT": "j-a exited 0\nj-b running\n"})
        out = json.loads(p.stdout)
        self.assertEqual(out["instance_state"], "running")
        self.assertEqual(out["jobs"], [{"job": "j-a", "state": "exited", "exit_code": 0},
                                       {"job": "j-b", "state": "running"}])

    def test_logs(self):
        self.seed_state()
        p = self.run_offload("logs", "j-x", "--tail", "5")
        out = json.loads(p.stdout)
        self.assertEqual(out["stdout"], "hello world\n")
        self.assertIn("tail -n 5", [c for c in self.calls() if c[0] == "ssh"][-1][-1]["stdin"])

    # -- fetch / down / list / extend

    def test_fetch_default_path(self):
        self.seed_state()
        p = self.run_offload("fetch", "j-x")
        out = json.loads(p.stdout)
        self.assertEqual(out["files"], 1)
        self.assertTrue(out["local"].endswith("offload-results/j-x"))
        rs = [c for c in self.calls() if c[0] == "rsync"][0]
        self.assertIn("ubuntu@203.0.113.10:jobs/j-x/out/", rs)

    def test_down_terminates_and_clears_state(self):
        self.seed_state()
        p = self.run_offload("down")
        self.assertEqual(json.loads(p.stdout)["terminated"][0]["id"], "i-fake001")
        self.assertIn("i-fake001", self.aws_calls("terminate-instances")[0])
        self.assertEqual(self.state()["instances"], {})

    def test_down_all_uses_cloud_tags(self):
        many = json.dumps([{"id": "i-1", "state": "running", "name": "a"}, {"id": "i-2", "state": "running", "name": "b"}])
        p = self.run_offload("down", "--all", env={"OFFLOAD_FAKE_INSTANCES": many})
        self.assertEqual({t["id"] for t in json.loads(p.stdout)["terminated"]}, {"i-1", "i-2"})
        self.assertIn("tag:cloud-offload:managed,Values=true", " ".join(self.aws_calls("describe-instances")[0]))

    def test_list_reconciles_orphans_and_stale(self):
        self.seed_state()
        cloud = json.dumps([{"id": "i-orphan", "state": "running", "name": "x", "ip": "1.2.3.4"}])
        p = self.run_offload("list", env={"OFFLOAD_FAKE_INSTANCES": cloud})
        out = json.loads(p.stdout)
        self.assertEqual(out["removed_stale_local_entries"], ["default"])
        self.assertEqual(out["instances"][0]["id"], "i-orphan")
        self.assertTrue(out["instances"][0]["orphan"])
        self.assertEqual(self.state()["instances"], {})

    def test_extend_reschedules_and_tags(self):
        self.seed_state()
        p = self.run_offload("extend", "--ttl", "2", env={"OFFLOAD_FAKE_SSH_OUT": "ok\n"})
        self.assertIn("deadline", json.loads(p.stdout))
        self.assertIn("shutdown -h +120", [c for c in self.calls() if c[0] == "ssh"][-1][-1]["stdin"])
        self.assertTrue(self.aws_calls("create-tags"))

    # -- doctor / policy

    def test_doctor_green(self):
        p = self.run_offload("doctor")
        out = json.loads(p.stdout)
        self.assertTrue(out["ok"], out)
        self.assertTrue(any("dry run" in c["check"] for c in out["checks"]))

    def test_doctor_print_policy_is_valid_and_tag_scoped(self):
        p = self.run_offload("doctor", "--print-policy")
        pol = json.loads(p.stdout)
        sids = {s["Sid"]: s for s in pol["Statement"]}
        self.assertIn("ec2:TerminateInstances", sids["ManageOwnResources"]["Action"])
        self.assertEqual(sids["ManageOwnResources"]["Condition"]["StringEquals"]["aws:ResourceTag/cloud-offload:managed"], "true")
        self.assertIn("ssm:GetParameter", sids["ReadPublicAmiParameters"]["Action"])

    def test_no_aws_string_outside_provider(self):
        src = SCRIPT.read_text()
        head, _, tail = src.partition("class AwsProvider(Provider):")
        _, _, after = tail.partition("PROVIDERS = {")
        core = head + after
        core = core.replace('PROVIDERS = {"aws": AwsProvider}', "").replace("make_provider", "")
        offenders = [l for l in core.splitlines() if "aws" in l.lower()
                     and "provider" not in l.lower() and "cloud-offload" not in l and not l.strip().startswith("#")
                     and '"--profile"' not in l and '"--region"' not in l]
        self.assertEqual(offenders, [], "aws-specific code leaked outside AwsProvider")


if __name__ == "__main__":
    unittest.main()
