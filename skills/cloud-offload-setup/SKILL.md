---
name: cloud-offload-setup
description: Walks the user through the prerequisites for the cloud-offload skill on AWS: aws CLI, a least-privilege IAM identity behind the `cloud-offload` profile, an SSH key, the config file, and a passing `offload doctor`. Use when the user asks to set up, configure, or fix cloud-offload, or when `offload doctor` reports a failing check.
disable-model-invocation: true
---
# cloud-offload-setup
Interactive. Do every step with the user watching, print each mutating command before running it, and get an explicit yes before any command that touches IAM. Never paste an access key into the conversation.

## Steps
1. **Locate the tool.** `OFFLOAD` is the first existing path of `.claude/skills/cloud-offload/scripts/offload.py` (project) or `~/.claude/skills/cloud-offload/scripts/offload.py`. If neither exists, tell the user to install the `cloud-offload` skill first and stop. Everywhere below, `offload` means `python3 "$OFFLOAD"`.

2. **aws CLI.** `aws --version`. If missing: macOS `brew install awscli`, Linux `curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o awscliv2.zip && unzip awscliv2.zip && sudo ./aws/install`, Windows `winget install Amazon.AWSCLI`.

3. **Existing profile?** `aws configure list-profiles`. If `cloud-offload` is listed and `aws sts get-caller-identity --profile cloud-offload` succeeds, skip to step 7.

4. **Choose the path.** Ask which listed profile has IAM admin rights, offering the manual path if none.
   - Automated (preferred): continue with step 5.
   - Manual: `offload doctor --print-policy > /tmp/cloud-offload-policy.json`, then tell the user to create IAM user `cloud-offload` in the console with an inline policy pasted from that file, create an access key, and run `aws configure --profile cloud-offload`. Wait for them to say it is done, then go to step 6.

5. **Automated IAM creation.** With `ADMIN=<their profile>`, print these, get a yes, then run them in order:
   ```bash
   offload doctor --print-policy > /tmp/cloud-offload-policy.json
   aws iam create-user --user-name cloud-offload --profile "$ADMIN" \
     --tags Key=purpose,Value=cloud-offload
   aws iam put-user-policy --user-name cloud-offload --policy-name cloud-offload \
     --policy-document file:///tmp/cloud-offload-policy.json --profile "$ADMIN"
   aws iam create-access-key --user-name cloud-offload --profile "$ADMIN" --output json \
     | python3 -c 'import json,sys,subprocess as s; k=json.load(sys.stdin)["AccessKey"]; \
       [s.run(["aws","configure","set",a,b,"--profile","cloud-offload"],check=True) \
        for a,b in (("aws_access_key_id",k["AccessKeyId"]),("aws_secret_access_key",k["SecretAccessKey"]))]; print("stored")'
   rm /tmp/cloud-offload-policy.json
   ```
   `EntityAlreadyExists` on create-user means a previous attempt: continue with put-user-policy. If the user already has two access keys, ask which to delete before creating a new one.

6. **Region and output.** Default the region to the admin profile's (`aws configure get region --profile "$ADMIN"`), confirm with the user, then:
   ```bash
   aws configure set region <region> --profile cloud-offload
   aws configure set output json --profile cloud-offload
   ```

7. **SSH key and config file.**
   ```bash
   mkdir -p ~/.cloud-offload
   [ -f ~/.cloud-offload/id_ed25519 ] || ssh-keygen -t ed25519 -N '' -C cloud-offload -f ~/.cloud-offload/id_ed25519
   [ -f ~/.cloud-offload/config.json ] || printf '{"provider":"aws","aws":{"profile":"cloud-offload","region":null}}\n' > ~/.cloud-offload/config.json
   ```

8. **Verify.** `offload doctor`. Every check must be `"ok": true`. IAM changes can take up to a minute to propagate, so retry once after 30 s before diagnosing. Common failures:
   - `profile authenticates` false: step 5 or the manual configure did not complete; re-run `aws configure --profile cloud-offload`.
   - `default VPC` false: `aws ec2 create-default-vpc --profile cloud-offload` needs admin; run it with `$ADMIN` after a yes.
   - `run-instances permitted (dry run)` false with `UnauthorizedOperation`: policy not attached; re-run put-user-policy.
   - `key pair registered` false: the local key changed; nothing to do, `offload up` imports it.

Finish by telling the user setup is complete and that the `cloud-offload` skill is now usable, and that removing everything later is `aws iam delete-user-policy`, `delete-access-key`, `delete-user` under the admin profile plus `rm -r ~/.cloud-offload`.
