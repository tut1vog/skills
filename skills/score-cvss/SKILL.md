---
name: score-cvss
description: Score supplied vulnerability evidence using CVSS 4.0 Base+Threat with a fixed E:P assumption and conservative evidence policy.
allowed-tools: Read, Grep, Glob, Bash
metadata:
  author: tut1vog
  version: "1.0"
---

# Score CVSS 4.0 (Base + Threat)
## Evidence
Use only the evidence supplied inline or in caller-designated files and directories. Identify demonstrated impacts and required access, privileges, interaction, and preconditions. Do not modify files, start environments, or execute exploits.

## Metrics
Use all eleven Base metrics and `E:P`. Omit Environmental and Supplemental metrics.

| Metric | Values | Guideline |
|---|---|---|
| **AV** | `N` / `A` / `L` / `P` | Network, Adjacent, Local, or Physical access required. |
| **AC** | `L` / `H` | `H` if exploitation requires circumventing security-enhancing mechanisms, such as ASLR, or obtaining target-specific secrets. |
| **AT** | `N` / `P` | `P` if exploitation requires specific deployment or execution conditions, such as a race or on-path position. |
| **PR** | `N` / `L` / `H` | Privileges required before exploitation: None, Low, or High. |
| **UI** | `N` / `P` / `A` | Interaction required from a user other than the attacker: None, Passive, or Active. |
| **VC / VI / VA** | `H` / `L` / `N` | Confidentiality, Integrity, Availability impact on the vulnerable system. |
| **SC / SI / SA** | `H` / `L` / `N` | Confidentiality, Integrity, Availability impact outside the vulnerable system (default: `N`). |

Apply these local scoring policies:
- Use `E:P` as a fixed pipeline assumption. A working private PoC alone does not establish `E:P` under CVSS.
- Score only demonstrated impacts. If evidence supports multiple values, choose the value yielding the lower score. Do not assign `H` to an inferred, partial, or untested consequence. This conservative policy differs from CVSS assessment of reasonable final outcomes.
- Do not seek additional evidence outside the caller-designated sources to resolve uncertainty.

Metric definitions: [FIRST CVSS 4.0 specification](https://www.first.org/cvss/v4.0/specification-document).

## Compute
Run `scripts/cvss_score.py` relative to this skill's directory using Python with `cvss==3.6`. Prefer the project virtualenv when it has that version. Pass the complete vector, including `CVSS:4.0` and `E:P`.
Use the script's computed score and normalized vector. If vector validation fails, correct the vector and rerun. If the scorer cannot run, report the error without a score.

## Output
Return the script's single tab-separated line in this order:
```text
score<TAB>severity<TAB>vector
```
Severity is `None`, `Low`, `Medium`, `High`, or `Critical`. The normalized vector contains the eleven Base metrics followed by `E:P`.
