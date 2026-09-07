---
name: score-alignment
description: Classify supplied vulnerability evidence into six threat-model alignment tiers using the vendor's published policies, advisories, and shipped controls.
allowed-tools: Read, Grep, Glob, Bash, WebSearch, WebFetch
metadata:
  author: tut1vog
  version: "1.0"
---

# Score Threat-Model Alignment
## Evidence
Use vulnerability evidence supplied inline or in caller-designated files and directories. Use the supplied impact as the basis for classification. Do not modify files, start environments, or execute exploits.
Identify the evaluated product, version, vendor, and claimed impact. Establish the attacker model:
- **Privileges:** permissions or access the attacker already holds.
- **Position:** required network access, deployment context, and other preconditions.
- **Boundary:** the security boundary crossed by the demonstrated behavior.

Retrieve relevant evidence from the vendor's own sources in this session:
- Security policy at the evaluated version and published threat-model documentation.
- Hardening and security guidance.
- Advisories addressing comparable attacker privileges, boundaries, or vulnerability classes.
- Shipped controls and their stated security purpose, identified by commit SHA and source path.

## Tiers
Tiers classify the vendor's documented security commitments, not severity, prevalence, or likely submission acceptance.

| Tier | Classification | Criterion |
|---|---|---|
| **1** | Precedent | A vendor advisory establishes precedent for the evaluated attacker model or vulnerability class. |
| **2** | Explicit Policy | Published policy covers the attacker or boundary, and no applicable advisory precedent was found. |
| **3** | Committed by Implementation | No applicable policy or advisory precedent was found, but a shipped control has the stated purpose of defending against this attacker. |
| **4** | Unaddressed | Reviewed policy is silent on the attacker model, and no applicable precedent or defensive intent was found. |
| **5** | Discouraged by Guidance | Published guidance assigns prevention of the evaluated condition to the operator. |
| **6** | Explicitly Excluded | Published policy explicitly treats the evaluated actor as trusted or excludes the vulnerability class. |

Apply these local rules:
- **Evaluation scope**: Classify the attacker model against the vendor that would receive the finding. Treat dependency vendors' positions as supporting context; assign a separate tier only when a separate upstream filing is intended.
- **Conflicting evidence**: Advisory precedent can establish coverage absent from policy, but does not erase a conflicting restriction. When applicable sources support conflicting tiers, choose the higher number and describe both positions with citations.
- **Insufficient evidence**: If the attacker model is unclear or vendor evidence is insufficient, report the missing information rather than inventing a tier. Failed retrieval does not establish Tier 4.

## Output
For each classification, return:
- **`tier`:** an integer from 1 to 6, or `null` when evidence is insufficient to classify the attacker model.
- **`description`:** a short explanation naming the vendor, evaluated target, claimed impact, attacker privileges, boundary crossed, and evidence that determined the tier. Identify conflicting evidence or the missing information when `tier` is `null`.
- **`citations`:** the supporting sources, each with `id` (policy title, advisory ID, or commit SHA and source path), `url`, `retrieved` (YYYY-MM-DD), and `quote` (a short verbatim excerpt retrieved in this session).

Refer to product behavior and the vendor's documented position directly; omit local repository paths and references to the PoC or test run.
