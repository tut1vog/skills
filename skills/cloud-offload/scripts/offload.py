#!/usr/bin/env python3
"""offload: run resource-intensive tasks on a short-lived cloud VM.

Stdlib only. Provider-specific code lives exclusively in the *Provider classes;
everything else (SSH, jobs, logs, fetch, TTL, state) is provider-independent.
Full reference: ../REFERENCE.md
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import random
import shlex
import shutil
import string
import subprocess
import sys
import tempfile
import time
from pathlib import Path

MIN_PY = (3, 10)
if sys.version_info < MIN_PY:
    sys.stderr.write(f"error: offload needs Python {MIN_PY[0]}.{MIN_PY[1]}+ (found {sys.version.split()[0]})\n")
    sys.exit(1)

HOME = Path(os.environ.get("CLOUD_OFFLOAD_HOME") or "~/.cloud-offload").expanduser()
CONFIG_FILE = HOME / "config.json"
STATE_FILE = HOME / "instances.json"
KEY_FILE = HOME / "id_ed25519"
PUBKEY_FILE = HOME / "id_ed25519.pub"
KNOWN_HOSTS = HOME / "known_hosts"

TAG_MANAGED = "cloud-offload:managed"
TAG_NAME = "cloud-offload:name"
TAG_DEADLINE = "cloud-offload:deadline"

DEFAULTS = {
    "type": "c7i.xlarge",
    "disk": 50,
    "ttl": 8.0,
    "arch": "amd64",
    "vcpu_cap": 16,
    "ssh_user": "ubuntu",
}

REMOTE_JOBS = "jobs"  # relative to the remote user's home


class OffloadError(Exception):
    pass


# --------------------------------------------------------------------------- utils

def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def iso(t: dt.datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(s: str) -> dt.datetime:
    return dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)


def emit(obj) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True))


def read_json(path: Path, default):
    if not path.exists():
        return default
    with open(path) as f:
        return json.load(f)


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
    os.replace(tmp, path)


def rand_id(n=4) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def load_config() -> dict:
    cfg = {"provider": "aws", "aws": {"profile": "cloud-offload", "region": None}}
    user = read_json(CONFIG_FILE, {})
    for k, v in user.items():
        if isinstance(v, dict) and isinstance(cfg.get(k), dict):
            cfg[k].update(v)
        else:
            cfg[k] = v
    return cfg


def load_state() -> dict:
    return read_json(STATE_FILE, {"instances": {}})


def save_state(state: dict) -> None:
    write_json(STATE_FILE, state)


# --------------------------------------------------------------------------- providers

class Provider:
    """Interface every cloud provider implements. Return values are plain dicts."""

    name = "base"

    @classmethod
    def from_config(cls, section: dict, args) -> "Provider":
        """Build from the provider's config.json section plus CLI overrides."""
        raise NotImplementedError

    def locator(self) -> dict:
        """Extra fields stored in local state to find the VM again (e.g. region)."""
        return {}

    def create(self, name: str, spec: dict) -> dict:
        """Launch a VM. spec keys: type, disk, spot, arch, ami, pubkey_path, user_data, deadline.
        Returns {id, pricing}. pricing is 'spot', 'on-demand', or 'on-demand (spot fallback)'."""
        raise NotImplementedError

    def wait_running(self, inst_id: str) -> dict:
        """Block until the VM is running. Returns {ip}."""
        raise NotImplementedError

    def describe(self, inst_id: str) -> dict:
        """Returns {state, ip, type, deadline, name}. state is one of
        pending|running|stopping|stopped|terminated|missing."""
        raise NotImplementedError

    def terminate(self, inst_id: str) -> None:
        raise NotImplementedError

    def list_managed(self) -> list:
        """All live VMs tagged as managed by this tool: [{id, name, state, ip, type, deadline, created}]."""
        raise NotImplementedError

    def ensure_key(self, pubkey_path: Path) -> str:
        """Idempotently register the public key. Returns the provider-side key name."""
        raise NotImplementedError

    def set_deadline(self, inst_id: str, deadline: str) -> None:
        raise NotImplementedError

    def check_type(self, itype: str) -> dict:
        """Returns {vcpus, memory_gb, gpu}. Raises OffloadError if the type does not exist."""
        raise NotImplementedError

    def doctor(self, pubkey_path: Path) -> list:
        """Returns [{check, ok, detail}]."""
        raise NotImplementedError

    @staticmethod
    def policy() -> dict:
        raise NotImplementedError


class AwsProvider(Provider):
    name = "aws"
    SG_NAME = "cloud-offload"
    SSH_USER = "ubuntu"
    ROOT_DEVICE = "/dev/sda1"
    AMI_PARAM = "/aws/service/canonical/ubuntu/server/24.04/stable/current/{arch}/hvm/ebs-gp3/ami-id"
    SPOT_FALLBACK_ERRORS = (
        "InsufficientInstanceCapacity",
        "SpotMaxPriceTooLow",
        "MaxSpotInstanceCountExceeded",
        "UnsupportedOperation",
        "InvalidParameterCombination",
    )

    def __init__(self, profile: str, region: str | None):
        self.profile = profile
        self.region = region or self._configured_region()

    @classmethod
    def from_config(cls, section: dict, args) -> "AwsProvider":
        return cls(profile=getattr(args, "profile", None) or section.get("profile", "cloud-offload"),
                   region=getattr(args, "region", None) or section.get("region"))

    def locator(self) -> dict:
        return {"region": self.region}

    # -- low-level

    def _configured_region(self) -> str:
        p = subprocess.run(["aws", "configure", "get", "region", "--profile", self.profile],
                           capture_output=True, text=True)
        region = p.stdout.strip()
        if p.returncode != 0 or not region:
            raise OffloadError(f"no region configured for profile '{self.profile}'; "
                               f"run: aws configure set region <region> --profile {self.profile}")
        return region

    def aws(self, *args: str, check: bool = True) -> tuple[int, dict | list | None, str]:
        cmd = ["aws", "--profile", self.profile, "--region", self.region, "--output", "json", *args]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True)
        except FileNotFoundError:
            raise OffloadError("aws CLI not found on PATH")
        if p.returncode != 0:
            if check:
                raise OffloadError(f"aws {args[0]} {args[1]} failed: {p.stderr.strip()}")
            return p.returncode, None, p.stderr.strip()
        data = json.loads(p.stdout) if p.stdout.strip() else None
        return 0, data, ""

    @staticmethod
    def _tags(res: dict) -> dict:
        return {t["Key"]: t["Value"] for t in res.get("Tags", [])}

    def _default_vpc(self) -> str:
        _, data, _ = self.aws("ec2", "describe-vpcs", "--filters", "Name=is-default,Values=true")
        vpcs = data.get("Vpcs", []) if data else []
        if not vpcs:
            raise OffloadError(f"no default VPC in {self.region}; create one with "
                               f"'aws ec2 create-default-vpc --profile {self.profile}' or pass --subnet/--sg")
        return vpcs[0]["VpcId"]

    def _resolve_ami(self, arch: str) -> str:
        _, data, _ = self.aws("ssm", "get-parameter", "--name", self.AMI_PARAM.format(arch=arch))
        return data["Parameter"]["Value"]

    def _ensure_sg(self, vpc_id: str) -> str:
        _, data, _ = self.aws("ec2", "describe-security-groups", "--filters",
                              f"Name=group-name,Values={self.SG_NAME}", f"Name=vpc-id,Values={vpc_id}")
        groups = data.get("SecurityGroups", []) if data else []
        if groups:
            return groups[0]["GroupId"]
        _, created, _ = self.aws(
            "ec2", "create-security-group", "--group-name", self.SG_NAME,
            "--description", "cloud-offload: SSH access to offload VMs", "--vpc-id", vpc_id,
            "--tag-specifications",
            f"ResourceType=security-group,Tags=[{{Key={TAG_MANAGED},Value=true}}]")
        sg_id = created["GroupId"]
        self.aws("ec2", "authorize-security-group-ingress", "--group-id", sg_id,
                 "--protocol", "tcp", "--port", "22", "--cidr", "0.0.0.0/0")
        return sg_id

    # -- interface

    def ensure_key(self, pubkey_path: Path) -> str:
        pub = pubkey_path.read_text().strip()
        digest = hashlib.sha256(pub.encode()).hexdigest()[:8]
        key_name = f"cloud-offload-{digest}"
        rc, _, err = self.aws("ec2", "describe-key-pairs", "--key-names", key_name, check=False)
        if rc == 0:
            return key_name
        if "InvalidKeyPair.NotFound" not in err:
            raise OffloadError(f"describe-key-pairs failed: {err}")
        self.aws("ec2", "import-key-pair", "--key-name", key_name,
                 "--public-key-material", f"fileb://{pubkey_path}",
                 "--tag-specifications", f"ResourceType=key-pair,Tags=[{{Key={TAG_MANAGED},Value=true}}]")
        return key_name

    def check_type(self, itype: str) -> dict:
        rc, data, err = self.aws("ec2", "describe-instance-types", "--instance-types", itype, check=False)
        if rc != 0:
            raise OffloadError(f"instance type '{itype}' not available in {self.region}: {err}")
        info = data["InstanceTypes"][0]
        return {
            "vcpus": info["VCpuInfo"]["DefaultVCpus"],
            "memory_gb": round(info["MemoryInfo"]["SizeInMiB"] / 1024, 1),
            "gpu": bool(info.get("GpuInfo")),
        }

    def create(self, name: str, spec: dict) -> dict:
        vpc_id = self._default_vpc()
        sg_id = spec.get("sg") or self._ensure_sg(vpc_id)
        ami = spec.get("ami") or self._resolve_ami(spec["arch"])
        key_name = self.ensure_key(Path(spec["pubkey_path"]))
        tags = [
            {"Key": TAG_MANAGED, "Value": "true"},
            {"Key": TAG_NAME, "Value": name},
            {"Key": TAG_DEADLINE, "Value": spec["deadline"]},
            {"Key": "Name", "Value": f"cloud-offload/{name}"},
        ]
        tag_spec = json.dumps([
            {"ResourceType": "instance", "Tags": tags},
            {"ResourceType": "volume", "Tags": tags},
        ])
        block = json.dumps([{"DeviceName": self.ROOT_DEVICE,
                             "Ebs": {"VolumeSize": int(spec["disk"]), "VolumeType": "gp3",
                                     "DeleteOnTermination": True}}])
        with_user_data = []
        user_data_file = None
        if spec.get("user_data"):
            fd, user_data_file = tempfile.mkstemp(prefix="offload-ud-", suffix=".sh")
            with os.fdopen(fd, "w") as f:
                f.write(spec["user_data"])
            with_user_data = ["--user-data", f"file://{user_data_file}"]
        base = [
            "ec2", "run-instances",
            "--image-id", ami,
            "--instance-type", spec["type"],
            "--key-name", key_name,
            "--security-group-ids", sg_id,
            "--associate-public-ip-address",
            "--instance-initiated-shutdown-behavior", "terminate",
            "--block-device-mappings", block,
            "--tag-specifications", tag_spec,
            "--count", "1",
            *with_user_data,
        ]
        if spec.get("subnet"):
            base += ["--subnet-id", spec["subnet"]]
        spot_opts = ["--instance-market-options",
                     "MarketType=spot,SpotOptions={SpotInstanceType=one-time,InstanceInterruptionBehavior=terminate}"]
        try:
            pricing = "on-demand"
            if spec["spot"]:
                rc, data, err = self.aws(*base, *spot_opts, check=False)
                if rc == 0:
                    pricing = "spot"
                elif any(e in err for e in self.SPOT_FALLBACK_ERRORS):
                    pricing = "on-demand (spot fallback)"
                    _, data, _ = self.aws(*base)
                else:
                    raise OffloadError(f"run-instances failed: {err}")
            else:
                _, data, _ = self.aws(*base)
        finally:
            if user_data_file:
                os.unlink(user_data_file)
        inst_id = data["Instances"][0]["InstanceId"]
        return {"id": inst_id, "pricing": pricing}

    def wait_running(self, inst_id: str) -> dict:
        self.aws("ec2", "wait", "instance-running", "--instance-ids", inst_id)
        d = self.describe(inst_id)
        if not d.get("ip"):
            raise OffloadError(f"{inst_id} is running but has no public IP (subnet may not auto-assign one)")
        return {"ip": d["ip"]}

    def describe(self, inst_id: str) -> dict:
        rc, data, err = self.aws("ec2", "describe-instances", "--instance-ids", inst_id, check=False)
        if rc != 0:
            if "InvalidInstanceID" in err:
                return {"state": "missing", "ip": None}
            raise OffloadError(f"describe-instances failed: {err}")
        res = [i for r in data.get("Reservations", []) for i in r.get("Instances", [])]
        if not res:
            return {"state": "missing", "ip": None}
        return self._summarize(res[0])

    def _summarize(self, i: dict) -> dict:
        tags = self._tags(i)
        return {
            "id": i["InstanceId"],
            "state": i["State"]["Name"],
            "ip": i.get("PublicIpAddress"),
            "type": i.get("InstanceType"),
            "name": tags.get(TAG_NAME),
            "deadline": tags.get(TAG_DEADLINE),
            "created": i.get("LaunchTime"),
            "pricing": "spot" if i.get("InstanceLifecycle") == "spot" else "on-demand",
        }

    def terminate(self, inst_id: str) -> None:
        rc, _, err = self.aws("ec2", "terminate-instances", "--instance-ids", inst_id, check=False)
        if rc != 0 and "InvalidInstanceID" not in err:
            raise OffloadError(f"terminate-instances failed: {err}")

    def list_managed(self) -> list:
        _, data, _ = self.aws("ec2", "describe-instances", "--filters",
                              f"Name=tag:{TAG_MANAGED},Values=true",
                              "Name=instance-state-name,Values=pending,running,stopping,stopped")
        return [self._summarize(i) for r in data.get("Reservations", []) for i in r.get("Instances", [])]

    def set_deadline(self, inst_id: str, deadline: str) -> None:
        self.aws("ec2", "create-tags", "--resources", inst_id, "--tags", f"Key={TAG_DEADLINE},Value={deadline}")

    def doctor(self, pubkey_path: Path) -> list:
        checks = []

        def add(name, ok, detail=""):
            checks.append({"check": name, "ok": bool(ok), "detail": detail})

        add("aws cli on PATH", shutil.which("aws"), shutil.which("aws") or "install: brew install awscli")
        if not shutil.which("aws"):
            return checks
        rc, ident, err = self.aws("sts", "get-caller-identity", check=False)
        add(f"profile '{self.profile}' authenticates", rc == 0, ident.get("Arn") if rc == 0 else err)
        if rc != 0:
            return checks
        add("region configured", True, self.region)
        try:
            vpc = self._default_vpc()
            add("default VPC", True, vpc)
        except OffloadError as e:
            add("default VPC", False, str(e))
            vpc = None
        try:
            ami = self._resolve_ami(DEFAULTS["arch"])
            add("Ubuntu AMI resolvable via SSM", True, ami)
        except OffloadError as e:
            add("Ubuntu AMI resolvable via SSM", False, str(e))
            ami = None
        add("local ssh key", pubkey_path.exists(),
            str(pubkey_path) if pubkey_path.exists() else f"run: ssh-keygen -t ed25519 -N '' -f {KEY_FILE}")
        if vpc:
            try:
                sg = self._ensure_sg(vpc)
                add("security group", True, sg)
            except OffloadError as e:
                add("security group", False, str(e))
        if pubkey_path.exists():
            try:
                add("key pair registered", True, self.ensure_key(pubkey_path))
            except OffloadError as e:
                add("key pair registered", False, str(e))
        if ami:
            rc, _, err = self.aws("ec2", "run-instances", "--dry-run", "--image-id", ami,
                                  "--instance-type", DEFAULTS["type"], "--count", "1", check=False)
            add("run-instances permitted (dry run)", "DryRunOperation" in err, err.splitlines()[-1] if err else "")
        rc, _, err = self.aws("ec2", "describe-instance-types", "--instance-types", DEFAULTS["type"], check=False)
        add(f"default type {DEFAULTS['type']} available", rc == 0, err if rc else "")
        return checks

    @staticmethod
    def policy() -> dict:
        managed = {"StringEquals": {f"aws:ResourceTag/{TAG_MANAGED}": "true"}}
        return {
            "Version": "2012-10-17",
            "Statement": [
                {"Sid": "Describe", "Effect": "Allow", "Resource": "*", "Action": [
                    "ec2:DescribeInstances", "ec2:DescribeInstanceStatus", "ec2:DescribeInstanceTypes",
                    "ec2:DescribeImages", "ec2:DescribeKeyPairs", "ec2:DescribeSecurityGroups",
                    "ec2:DescribeVpcs", "ec2:DescribeSubnets", "ec2:DescribeTags",
                    "ec2:DescribeSpotPriceHistory", "sts:GetCallerIdentity"]},
                {"Sid": "ReadPublicAmiParameters", "Effect": "Allow", "Action": "ssm:GetParameter",
                 "Resource": "arn:aws:ssm:*::parameter/aws/service/canonical/*"},
                {"Sid": "CreateSharedResources", "Effect": "Allow", "Resource": "*",
                 "Action": ["ec2:ImportKeyPair", "ec2:CreateSecurityGroup", "ec2:RunInstances"]},
                {"Sid": "TagOnCreate", "Effect": "Allow", "Action": "ec2:CreateTags", "Resource": "*",
                 "Condition": {"StringEquals": {"ec2:CreateAction": [
                     "RunInstances", "CreateSecurityGroup", "ImportKeyPair"]}}},
                {"Sid": "ManageOwnResources", "Effect": "Allow", "Resource": "*", "Condition": managed,
                 "Action": ["ec2:TerminateInstances", "ec2:StopInstances", "ec2:CreateTags",
                            "ec2:AuthorizeSecurityGroupIngress", "ec2:RevokeSecurityGroupIngress",
                            "ec2:DeleteSecurityGroup", "ec2:DeleteKeyPair"]},
                {"Sid": "SpotServiceLinkedRole", "Effect": "Allow", "Action": "iam:CreateServiceLinkedRole",
                 "Resource": "arn:aws:iam::*:role/aws-service-role/spot.amazonaws.com/*",
                 "Condition": {"StringEquals": {"iam:AWSServiceName": "spot.amazonaws.com"}}},
            ],
        }


PROVIDERS = {"aws": AwsProvider}


def provider_class(cfg: dict, args) -> type:
    name = getattr(args, "provider", None) or cfg.get("provider") or next(iter(PROVIDERS))
    if name not in PROVIDERS:
        raise OffloadError(f"unknown provider '{name}'; known: {', '.join(PROVIDERS)}")
    return PROVIDERS[name]


def make_provider(cfg: dict, args) -> Provider:
    cls = provider_class(cfg, args)
    return cls.from_config(cfg.get(cls.name, {}), args)


# --------------------------------------------------------------------------- ssh layer

def ssh_opts() -> list:
    return ["-i", str(KEY_FILE),
            "-o", "StrictHostKeyChecking=accept-new",
            "-o", f"UserKnownHostsFile={KNOWN_HOSTS}",
            "-o", "ConnectTimeout=10",
            "-o", "BatchMode=yes",
            "-o", "ServerAliveInterval=15",
            "-o", "LogLevel=ERROR"]


def ssh_target(inst: dict) -> str:
    return f"{inst.get('ssh_user', DEFAULTS['ssh_user'])}@{inst['ip']}"


def ssh_script(inst: dict, script: str, timeout: int | None = None) -> subprocess.CompletedProcess:
    """Run a bash script on the instance via stdin. Never raises on non-zero exit."""
    cmd = ["ssh", *ssh_opts(), ssh_target(inst), "bash", "-s"]
    try:
        return subprocess.run(cmd, input=script, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(cmd, 124, "", "ssh timed out")


def ssh_stream(inst: dict, script: str) -> int:
    """Run a bash script with stdout/stderr passed straight through."""
    cmd = ["ssh", *ssh_opts(), ssh_target(inst), "bash", "-s"]
    return subprocess.run(cmd, input=script, text=True).returncode


def forget_host(ip: str) -> None:
    if KNOWN_HOSTS.exists():
        subprocess.run(["ssh-keygen", "-R", ip, "-f", str(KNOWN_HOSTS)], capture_output=True)


def wait_ssh(inst: dict, timeout: int = 240) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        p = ssh_script(inst, "true", timeout=20)
        if p.returncode == 0:
            return True
        time.sleep(5)
    return False


def require_key() -> None:
    if not KEY_FILE.exists() or not PUBKEY_FILE.exists():
        raise OffloadError(f"ssh key missing at {KEY_FILE}; run the cloud-offload-setup skill "
                           f"or: ssh-keygen -t ed25519 -N '' -f {KEY_FILE}")


# --------------------------------------------------------------------------- state helpers

def get_instance(state: dict, name: str) -> dict:
    inst = state["instances"].get(name)
    if not inst:
        raise OffloadError(f"no instance named '{name}'; run 'offload up' or 'offload list'")
    return inst


def instance_alive_or_raise(provider: Provider, state: dict, name: str) -> dict:
    inst = get_instance(state, name)
    d = provider.describe(inst["id"])
    if d["state"] in ("terminated", "missing", "shutting-down"):
        del state["instances"][name]
        save_state(state)
        raise OffloadError(f"instance '{name}' ({inst['id']}) is {d['state']} (TTL reached, spot "
                           f"interruption, or terminated elsewhere); removed from local state")
    if d.get("ip") and d["ip"] != inst.get("ip"):
        inst["ip"] = d["ip"]
        save_state(state)
    return inst


def ttl_user_data(minutes: int) -> str:
    return ("#!/bin/bash\n"
            f"shutdown -h +{minutes} 'cloud-offload TTL reached'\n"
            f"mkdir -p /home/{DEFAULTS['ssh_user']}/{REMOTE_JOBS}\n"
            f"chown {DEFAULTS['ssh_user']}:{DEFAULTS['ssh_user']} /home/{DEFAULTS['ssh_user']}/{REMOTE_JOBS}\n")


# --------------------------------------------------------------------------- commands

def cmd_up(args, cfg, provider: Provider):
    require_key()
    state = load_state()
    name = args.name
    existing = state["instances"].get(name)
    if existing:
        d = provider.describe(existing["id"])
        if d["state"] in ("pending", "running"):
            raise OffloadError(f"instance '{name}' already exists ({existing['id']}, {d['state']}); "
                               f"reuse it, pick another --name, or run 'offload down'")
        del state["instances"][name]
    info = provider.check_type(args.type)
    if not args.allow_large and (info["vcpus"] > DEFAULTS["vcpu_cap"] or info["gpu"]):
        raise OffloadError(f"{args.type} ({info['vcpus']} vCPU, gpu={info['gpu']}) exceeds the safety cap "
                           f"({DEFAULTS['vcpu_cap']} vCPU, no GPU); pass --allow-large if intended")
    minutes = max(1, int(round(args.ttl * 60)))
    deadline = iso(now_utc() + dt.timedelta(minutes=minutes))
    spec = {
        "type": args.type, "disk": args.disk, "spot": not args.on_demand, "arch": args.arch,
        "ami": args.ami, "sg": args.sg, "subnet": args.subnet,
        "pubkey_path": str(PUBKEY_FILE), "user_data": ttl_user_data(minutes), "deadline": deadline,
    }
    created = provider.create(name, spec)
    inst = {
        "provider": provider.name, "id": created["id"], "ip": None, "type": args.type,
        "vcpus": info["vcpus"], "memory_gb": info["memory_gb"], "pricing": created["pricing"],
        "created": iso(now_utc()), "deadline": deadline, "ssh_user": DEFAULTS["ssh_user"],
    }
    inst.update(provider.locator())
    state["instances"][name] = inst
    save_state(state)
    inst["ip"] = provider.wait_running(created["id"])["ip"]
    save_state(state)
    forget_host(inst["ip"])
    ready = wait_ssh(inst)
    out = {"name": name, **inst, "ssh_ready": ready}
    emit(out)
    if not ready:
        raise OffloadError(f"instance {inst['id']} is running at {inst['ip']} but SSH never became ready; "
                           f"inspect with 'offload ssh' or clean up with 'offload down --name {name}'")


def new_job_id() -> str:
    return f"j-{now_utc().strftime('%Y%m%d-%H%M%S')}-{rand_id()}"


def job_dir(job_id: str) -> str:
    return f"~/{REMOTE_JOBS}/{job_id}"


def cmd_run(args, cfg, provider: Provider):
    if bool(args.script) == bool(args.command):
        raise OffloadError("give exactly one of: --script <file>  or  -- <command>")
    if args.script:
        body = Path(args.script).read_text()
        if not body.startswith("#!"):
            body = "#!/usr/bin/env bash\n" + body
    else:
        body = "#!/usr/bin/env bash\nset -o pipefail\n" + " ".join(args.command) + "\n"
    state = load_state()
    inst = instance_alive_or_raise(provider, state, args.name)
    job_id = new_job_id()
    j = job_dir(job_id)
    delim = "OFFLOAD_EOF_" + rand_id(8)
    script = f"""set -e
J={j}
mkdir -p "$J/out"
cat > "$J/cmd.sh" <<'{delim}'
{body}
{delim}
chmod +x "$J/cmd.sh"
date -u +%Y-%m-%dT%H:%M:%SZ > "$J/started"
cd "$J"
export OUT="$J/out" JOB={job_id} DEBIAN_FRONTEND=noninteractive
nohup setsid bash -c './cmd.sh > stdout 2> stderr; echo $? > exit' > /dev/null 2>&1 &
echo $! > "$J/pid"
echo started
"""
    p = ssh_script(inst, script, timeout=60)
    if p.returncode != 0 or "started" not in p.stdout:
        raise OffloadError(f"failed to start job on '{args.name}': {p.stderr.strip() or p.stdout.strip()}")
    result = {"job": job_id, "instance": args.name, "remote_dir": j, "state": "running"}
    if not args.wait:
        emit(result)
        return
    deadline = time.time() + args.timeout
    interval = 3
    while True:
        st = job_status(provider, state, args.name, job_id)
        if st["state"] != "running":
            st["tail"] = job_logs(inst, job_id, args.tail)
            emit(st)
            if st["state"] != "exited":
                sys.exit(1)
            sys.exit(0 if st.get("exit_code") == 0 else 3)
        if time.time() >= deadline:
            st["note"] = f"still running after --timeout {args.timeout}s; poll with 'offload status {job_id}'"
            st["tail"] = job_logs(inst, job_id, args.tail)
            emit(st)
            sys.exit(2)
        time.sleep(interval)
        interval = min(interval * 2, 30)


STATUS_SCRIPT = """J={j}
if [ ! -d "$J" ]; then echo "found=no"; exit 0; fi
echo "found=yes"
echo "started=$(cat "$J/started" 2>/dev/null)"
if [ -f "$J/exit" ]; then echo "state=exited"; echo "exit=$(cat "$J/exit")"; else echo "state=running"; fi
echo "stdout_bytes=$(stat -c %s "$J/stdout" 2>/dev/null || echo 0)"
echo "stderr_bytes=$(stat -c %s "$J/stderr" 2>/dev/null || echo 0)"
echo "out_files=$(find "$J/out" -type f 2>/dev/null | wc -l | tr -d ' ')"
echo "out_bytes=$(du -sb "$J/out" 2>/dev/null | cut -f1)"
echo "now=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
"""


def parse_kv(text: str) -> dict:
    out = {}
    for line in text.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def job_status(provider: Provider, state: dict, name: str, job_id: str) -> dict:
    inst = get_instance(state, name)
    p = ssh_script(inst, STATUS_SCRIPT.format(j=job_dir(job_id)), timeout=40)
    if p.returncode != 0:
        d = provider.describe(inst["id"])
        if d["state"] in ("terminated", "missing", "shutting-down", "stopped", "stopping"):
            return {"job": job_id, "instance": name, "state": "interrupted", "instance_state": d["state"],
                    "detail": "instance is gone (spot interruption, TTL, or terminated elsewhere); "
                              "job output is lost, re-run on a new instance"}
        return {"job": job_id, "instance": name, "state": "unreachable", "instance_state": d["state"],
                "detail": p.stderr.strip()}
    kv = parse_kv(p.stdout)
    if kv.get("found") != "yes":
        raise OffloadError(f"no job '{job_id}' on instance '{name}'")
    started = kv.get("started") or None
    elapsed = None
    if started:
        try:
            elapsed = int((parse_iso(kv["now"]) - parse_iso(started)).total_seconds())
        except ValueError:
            pass
    st = {
        "job": job_id, "instance": name, "state": kv["state"], "started": started,
        "elapsed_seconds": elapsed,
        "stdout_bytes": int(kv.get("stdout_bytes") or 0), "stderr_bytes": int(kv.get("stderr_bytes") or 0),
        "out_files": int(kv.get("out_files") or 0), "out_bytes": int(kv.get("out_bytes") or 0),
        "remote_dir": job_dir(job_id),
    }
    if kv["state"] == "exited":
        st["exit_code"] = int(kv.get("exit") or -1)
    return st


def job_logs(inst: dict, job_id: str, tail: int) -> dict:
    sep = "OFFLOAD_SEP_" + rand_id(8)
    j = job_dir(job_id)
    p = ssh_script(inst, f'tail -n {int(tail)} {j}/stdout 2>/dev/null; echo {sep}; tail -n {int(tail)} {j}/stderr 2>/dev/null',
                   timeout=40)
    if p.returncode != 0:
        raise OffloadError(f"could not read logs: {p.stderr.strip()}")
    out, _, err = p.stdout.partition(sep + "\n")
    return {"stdout": out, "stderr": err}


def cmd_status(args, cfg, provider: Provider):
    state = load_state()
    if args.job:
        st = job_status(provider, state, args.name, args.job)
        inst = state["instances"].get(args.name, {})
        st["deadline"] = inst.get("deadline")
        emit(st)
        return
    inst = get_instance(state, args.name)
    d = provider.describe(inst["id"])
    result = {"name": args.name, **inst, "instance_state": d["state"], "jobs": []}
    if d.get("ip"):
        inst["ip"] = d["ip"]
    if d["state"] == "running":
        p = ssh_script(inst, f'for d in ~/{REMOTE_JOBS}/*/; do [ -d "$d" ] || continue; n=$(basename "$d"); '
                             f'if [ -f "$d/exit" ]; then echo "$n exited $(cat "$d/exit")"; else echo "$n running"; fi; done',
                       timeout=40)
        for line in p.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                job = {"job": parts[0], "state": parts[1]}
                if len(parts) == 3:
                    job["exit_code"] = int(parts[2])
                result["jobs"].append(job)
        result["ssh_reachable"] = p.returncode == 0
    if inst.get("deadline"):
        result["ttl_remaining_minutes"] = int((parse_iso(inst["deadline"]) - now_utc()).total_seconds() // 60)
    emit(result)


def cmd_logs(args, cfg, provider: Provider):
    state = load_state()
    inst = instance_alive_or_raise(provider, state, args.name)
    if not args.follow:
        emit({"job": args.job, **job_logs(inst, args.job, args.tail)})
        return
    j = job_dir(args.job)
    script = (f'cd {j} || exit 1; timeout {int(args.timeout)} bash -c '
              f'\'tail -n {int(args.tail)} -f stdout & TP=$!; while [ ! -f exit ]; do sleep 2; done; sleep 1; kill $TP 2>/dev/null\'; '
              f'if [ -f exit ]; then echo "[offload] job exited with $(cat exit)" >&2; else echo "[offload] follow timeout; job still running" >&2; fi')
    sys.exit(ssh_stream(inst, script))


def cmd_fetch(args, cfg, provider: Provider):
    state = load_state()
    inst = instance_alive_or_raise(provider, state, args.name)
    remote = args.remote_path or f"{REMOTE_JOBS}/{args.job}/out/"
    remote = remote.replace("~/", "", 1) if remote.startswith("~/") else remote
    local = Path(args.to or f"./offload-results/{args.job}")
    local.mkdir(parents=True, exist_ok=True)
    src = f"{ssh_target(inst)}:{remote}"
    if shutil.which("rsync"):
        p = subprocess.run(["rsync", "-az", "-e", "ssh " + " ".join(shlex.quote(o) for o in ssh_opts()),
                            src, str(local) + "/"], capture_output=True, text=True)
        method = "rsync"
        if p.returncode != 0 and ("command not found" in p.stderr or p.returncode in (127, 12)):
            p = None
    else:
        p = None
    if p is None:
        p = subprocess.run(["scp", "-r", "-q", *ssh_opts(), src if not remote.endswith("/") else src + ".",
                            str(local)], capture_output=True, text=True)
        method = "scp"
    if p.returncode != 0:
        raise OffloadError(f"{method} failed: {p.stderr.strip()}")
    files = [f for f in local.rglob("*") if f.is_file()]
    emit({"job": args.job, "remote": remote, "local": str(local.resolve()), "method": method,
          "files": len(files), "bytes": sum(f.stat().st_size for f in files)})


def cmd_ssh(args, cfg, provider: Provider):
    state = load_state()
    inst = instance_alive_or_raise(provider, state, args.name)
    cmd = ["ssh", *ssh_opts(), ssh_target(inst)]
    if args.command:
        cmd += ["--", " ".join(args.command)]
    sys.exit(subprocess.run(cmd).returncode)


def cmd_extend(args, cfg, provider: Provider):
    state = load_state()
    inst = instance_alive_or_raise(provider, state, args.name)
    minutes = max(1, int(round(args.ttl * 60)))
    p = ssh_script(inst, f"sudo shutdown -c 2>/dev/null; sudo shutdown -h +{minutes} 'cloud-offload TTL reached' && echo ok",
                   timeout=40)
    if p.returncode != 0 or "ok" not in p.stdout:
        raise OffloadError(f"could not reschedule shutdown: {p.stderr.strip()}")
    deadline = iso(now_utc() + dt.timedelta(minutes=minutes))
    provider.set_deadline(inst["id"], deadline)
    inst["deadline"] = deadline
    save_state(state)
    emit({"name": args.name, "id": inst["id"], "deadline": deadline, "ttl_hours": args.ttl})


def cmd_down(args, cfg, provider: Provider):
    state = load_state()
    terminated = []
    if args.all:
        for m in provider.list_managed():
            provider.terminate(m["id"])
            terminated.append({"id": m["id"], "name": m.get("name")})
        state["instances"] = {n: i for n, i in state["instances"].items() if i.get("provider") != provider.name}
    else:
        inst = get_instance(state, args.name)
        provider.terminate(inst["id"])
        terminated.append({"id": inst["id"], "name": args.name})
        del state["instances"][args.name]
    save_state(state)
    emit({"terminated": terminated})


def cmd_list(args, cfg, provider: Provider):
    state = load_state()
    cloud = {m["id"]: m for m in provider.list_managed()}
    rows = []
    stale = []
    for name, inst in state["instances"].items():
        if inst.get("provider") != provider.name:
            continue
        m = cloud.pop(inst["id"], None)
        if m is None:
            stale.append(name)
            continue
        rows.append({"name": name, "tracked": True, **m, "pricing": inst.get("pricing", m.get("pricing"))})
    for m in cloud.values():
        rows.append({"name": m.get("name"), "tracked": False, "orphan": True, **m})
    for name in stale:
        del state["instances"][name]
    if stale:
        save_state(state)
    emit({"provider": provider.name, "instances": rows, "removed_stale_local_entries": stale})


def cmd_doctor(args, cfg, provider: Provider):
    checks = provider.doctor(PUBKEY_FILE)
    checks.insert(0, {"check": "config file", "ok": CONFIG_FILE.exists(),
                      "detail": str(CONFIG_FILE) if CONFIG_FILE.exists() else "missing; run the cloud-offload-setup skill"})
    ok = all(c["ok"] for c in checks)
    emit({"ok": ok, "provider": provider.name, "checks": checks})
    sys.exit(0 if ok else 1)


# --------------------------------------------------------------------------- cli

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="offload", description=__doc__.splitlines()[0])
    p.add_argument("--provider", help="cloud provider (default: from config)")
    p.add_argument("--profile", help="aws: credentials profile (default: from config)")
    p.add_argument("--region", help="aws: region (default: from config, then profile)")
    sub = p.add_subparsers(dest="cmd", required=True)

    def name_arg(sp):
        sp.add_argument("--name", default="default", help="instance name (default: default)")

    s = sub.add_parser("up", help="launch an instance")
    name_arg(s)
    s.add_argument("--type", default=DEFAULTS["type"])
    s.add_argument("--disk", type=int, default=DEFAULTS["disk"], help="root disk GB")
    s.add_argument("--ttl", type=float, default=DEFAULTS["ttl"], help="hours until self-destruct")
    s.add_argument("--arch", choices=["amd64", "arm64"], default=DEFAULTS["arch"])
    s.add_argument("--on-demand", action="store_true", help="skip spot pricing")
    s.add_argument("--allow-large", action="store_true", help="bypass the vCPU/GPU safety cap")
    s.add_argument("--ami")
    s.add_argument("--sg", help="existing security group id")
    s.add_argument("--subnet", help="existing subnet id")
    s.set_defaults(fn=cmd_up)

    s = sub.add_parser("run", help="start a job (async unless --wait)")
    name_arg(s)
    s.add_argument("--script", help="local script file to upload and execute")
    s.add_argument("--wait", action="store_true")
    s.add_argument("--timeout", type=int, default=540, help="seconds to wait with --wait")
    s.add_argument("--tail", type=int, default=50, help="log lines to include with --wait")
    s.add_argument("command", nargs="*", help="inline command after --")
    s.set_defaults(fn=cmd_run)

    s = sub.add_parser("status", help="instance status, or one job's status")
    name_arg(s)
    s.add_argument("job", nargs="?")
    s.set_defaults(fn=cmd_status)

    s = sub.add_parser("logs", help="fetch job stdout/stderr")
    name_arg(s)
    s.add_argument("job")
    s.add_argument("--tail", type=int, default=200)
    s.add_argument("--follow", action="store_true", help="stream stdout until exit or --timeout")
    s.add_argument("--timeout", type=int, default=540)
    s.set_defaults(fn=cmd_logs)

    s = sub.add_parser("fetch", help="download job results")
    name_arg(s)
    s.add_argument("job")
    s.add_argument("remote_path", nargs="?", help="default: jobs/<job>/out/")
    s.add_argument("--to", help="local directory (default: ./offload-results/<job>)")
    s.set_defaults(fn=cmd_fetch)

    s = sub.add_parser("ssh", help="interactive shell or one-off command")
    name_arg(s)
    s.add_argument("command", nargs="*")
    s.set_defaults(fn=cmd_ssh)

    s = sub.add_parser("extend", help="reschedule self-destruct")
    name_arg(s)
    s.add_argument("--ttl", type=float, required=True, help="hours from now")
    s.set_defaults(fn=cmd_extend)

    s = sub.add_parser("down", help="terminate instance(s)")
    name_arg(s)
    s.add_argument("--all", action="store_true", help="terminate every managed instance in the region")
    s.set_defaults(fn=cmd_down)

    s = sub.add_parser("list", help="list managed instances, reconciling local state with the cloud")
    s.set_defaults(fn=cmd_list)

    s = sub.add_parser("doctor", help="verify prerequisites")
    s.add_argument("--print-policy", action="store_true", help="print the IAM policy JSON and exit")
    s.set_defaults(fn=cmd_doctor)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        cfg = load_config()
        if args.cmd == "doctor" and args.print_policy:
            emit(provider_class(cfg, args).policy())  # needs no credentials or region
            return 0
        provider = make_provider(cfg, args)
        args.fn(args, cfg, provider)
        return 0
    except OffloadError as e:
        sys.stderr.write(f"error: {e}\n")
        return 1
    except KeyboardInterrupt:
        sys.stderr.write("interrupted\n")
        return 130


if __name__ == "__main__":
    sys.exit(main())
