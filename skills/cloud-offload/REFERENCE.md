# cloud-offload reference

Companion to [SKILL.md](SKILL.md). Everything here describes `scripts/offload.py`.

## Invocation

```
python3 <skill-dir>/scripts/offload.py [--provider P] [--profile NAME] [--region R] <subcommand> [flags]
```

Global flags precede the subcommand. Requires Python 3.10+, the `aws` CLI, `ssh`, and `rsync` (falls back
to `scp`). Stdout is always one JSON document; errors go to stderr as `error: ...` with exit code 1.
Exit codes for `run --wait`: 0 job exited 0, 3 job exited non-zero, 2 still running at timeout,
1 job interrupted or unreachable.

## Subcommands

| Command | Flags | Output |
|---|---|---|
| `up` | `--name N` `--type T` `--disk GB` `--ttl H` `--arch amd64\|arm64` `--on-demand` `--allow-large` `--ami ID` `--sg ID` `--subnet ID` | `{name,id,ip,type,vcpus,memory_gb,pricing,created,deadline,region,ssh_ready}` |
| `run` | `--name N` `--script FILE` or `-- CMD...` `--wait` `--timeout S` (540) `--tail N` (50) | `{job,instance,remote_dir,state}`; with `--wait` the job status plus `tail:{stdout,stderr}` |
| `status` | `--name N` `[JOB]` | job: `{job,state,started,elapsed_seconds,exit_code?,stdout_bytes,stderr_bytes,out_files,out_bytes,deadline}`; instance: `{name,id,ip,instance_state,ttl_remaining_minutes,jobs:[...]}` |
| `logs` | `--name N` `JOB` `--tail N` (200) `--follow` `--timeout S` (540) | `{job,stdout,stderr}`; `--follow` streams raw stdout instead |
| `fetch` | `--name N` `JOB` `[REMOTE_PATH]` `--to DIR` | `{job,remote,local,method,files,bytes}` |
| `ssh` | `--name N` `[-- CMD...]` | passthrough; no JSON |
| `extend` | `--name N` `--ttl H` | `{name,id,deadline,ttl_hours}` |
| `down` | `--name N` or `--all` | `{terminated:[{id,name}]}` |
| `list` | | `{provider,instances:[{name,id,state,ip,type,deadline,pricing,tracked,orphan?}],removed_stale_local_entries}` |
| `doctor` | `--print-policy` | `{ok,provider,checks:[{check,ok,detail}]}`; exit 1 if any check fails |

Job states: `running`, `exited` (see `exit_code`), `interrupted` (instance gone: spot reclaim, TTL, or
terminated elsewhere), `unreachable` (instance exists but SSH failed; retry).

## Defaults and guardrails

| Setting | Value | Notes |
|---|---|---|
| Image | Ubuntu 24.04 LTS | resolved from SSM public parameter `/aws/service/canonical/ubuntu/server/24.04/stable/current/<arch>/hvm/ebs-gp3/ami-id` |
| Type | `c7i.xlarge` | validated with `describe-instance-types` |
| Disk | 50 GB gp3, delete on termination | |
| Pricing | spot, one-time, terminate on interruption | falls back to on-demand on `InsufficientInstanceCapacity`, `SpotMaxPriceTooLow`, `MaxSpotInstanceCountExceeded`, `UnsupportedOperation`; reported as `"on-demand (spot fallback)"` |
| TTL | 8 h | cloud-init runs `shutdown -h +N`; instance launches with shutdown behavior `terminate` |
| Size cap | 16 vCPU, no GPU | `--allow-large` bypasses |
| Network | default VPC, public IPv4, security group `cloud-offload` with TCP 22 open to `0.0.0.0/0` | key auth only; Ubuntu disables password auth |
| SSH user | `ubuntu` | |
| Tags | `cloud-offload:managed=true`, `cloud-offload:name`, `cloud-offload:deadline`, `Name=cloud-offload/<name>` | on instance and root volume; IAM scopes mutations to `managed=true` |

## Remote job layout

```
~/jobs/<job-id>/
  cmd.sh     the uploaded script (inline commands are wrapped into one)
  started    UTC start time
  pid        pid of the detached runner
  stdout     captured stdout
  stderr     captured stderr
  exit       exit code, written when the job ends
  out/       $OUT; what `fetch` downloads by default
```

Environment inside the job: `OUT`, `JOB`, `DEBIAN_FRONTEND=noninteractive`; cwd is the job directory.
The job runs under `nohup setsid`, so it survives the SSH session and the local agent.

## Local files

```
~/.cloud-offload/            (override with $CLOUD_OFFLOAD_HOME)
  config.json                {"provider":"aws","aws":{"profile":"cloud-offload","region":null}}
  instances.json             {"instances":{"<name>":{provider,id,ip,type,vcpus,memory_gb,pricing,created,deadline,ssh_user,region}}}
  id_ed25519, id_ed25519.pub persistent key; imported to the provider as cloud-offload-<sha256[:8] of pubkey>
  known_hosts                per-tool host keys; `up` forgets the IP before first connect
```

`region: null` defers to the profile. `list` treats the cloud's tags as the source of truth: entries in
`instances.json` with no live instance are dropped, live tagged instances with no entry are reported as
`orphan` and are covered by `down --all`.

## IAM policy

`offload doctor --print-policy` prints the least-privilege policy the `cloud-offload` identity needs.
Summary: read-only `ec2:Describe*` and `sts:GetCallerIdentity`; `ssm:GetParameter` on the public canonical
Ubuntu path; `ec2:RunInstances`, `ImportKeyPair`, `CreateSecurityGroup`; `ec2:CreateTags` only during those
create actions; terminate/stop/tag/security-group mutations only on resources tagged
`cloud-offload:managed=true`; `iam:CreateServiceLinkedRole` for `spot.amazonaws.com` (needed once per account).

## Provider interface

Add a provider by subclassing `Provider` in `offload.py` and registering it in `PROVIDERS`. Provider code
must not leak outside its class; `tests/test_offload.py` greps for that.

```
from_config(section, args) -> Provider    build from config.json section plus CLI overrides
locator() -> dict                          extra state fields needed to find the VM later (e.g. region)
create(name, spec) -> {id, pricing}        spec: type, disk, spot, arch, ami, sg, subnet, pubkey_path, user_data, deadline
wait_running(id) -> {ip}
describe(id) -> {state, ip, type, name, deadline, created, pricing}   state: pending|running|stopping|stopped|terminated|missing
terminate(id)
list_managed() -> [describe-shaped dicts]
ensure_key(pubkey_path) -> key name        idempotent
set_deadline(id, iso)                      update the deadline tag/label
check_type(type) -> {vcpus, memory_gb, gpu}
doctor(pubkey_path) -> [{check, ok, detail}]
policy() -> dict                           least-privilege policy document for the provider
```

`user_data` is a cloud-init shell script the provider must pass verbatim; it carries the TTL shutdown.
A provider without terminate-on-shutdown should implement the TTL with its own scheduler in `create`.

## Tests

```
python3 -m unittest discover -s skills/cloud-offload/tests -v
```

Fake `aws`, `ssh`, `rsync`, and `ssh-keygen` live in `tests/bin/` and log every call to a file; no cloud
access or cost. Scenario knobs are documented at the top of `tests/bin/aws` and `tests/bin/ssh`.
