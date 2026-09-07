---
name: score-exposure
description: Classify supplied vulnerability evidence into six configuration exposure tiers, identifying required conditions and the basis for the classification.
allowed-tools: Read, Grep, Glob, Bash
metadata:
  author: tut1vog
  version: "1.0"
---

# Score Exposure Tier
## Evidence
Use only evidence supplied inline or in caller-designated files and directories, including supplied source code and packaging configurations. Do not modify files, start environments, or execute exploits.
Identify the evaluated product, version, distribution, and claimed impact. Separate the required conditions:
- **Code:** affected versions, required modules, and transitive or opt-in dependencies.
- **Configuration:** flags, properties, and runtime modes.
- **Network:** listeners, bindings, and exposure paths.
- **Services:** required external services or integrations.
- **Application:** exported interfaces, registered handlers, and API usage.

## Tiers
This is a local classification rubric for configuration exposure. Tiers describe how the required configuration is adopted; they do not establish measured deployment prevalence, exploitability, or impact severity, or determine whether a vulnerability is valid.

| Tier | Classification | Criterion |
|---|---|---|
| **1** | Intrinsic / Invariant | The condition is inherent to the evaluated target and cannot be disabled without removing its core function. |
| **2** | Out-of-the-Box Default | The condition is enabled in the evaluated target's shipped configuration. |
| **3** | Template & Tutorial Driven | The condition is off by default but enabled by a supplied quickstart, template, or deployment example. |
| **4** | Enterprise / Architectural Flag | The condition requires an optional architecture, license tier, or integration. |
| **5** | Workaround & Debug Residual | The condition requires a testing, debugging, or workaround setting retained in production. |
| **6** | Synthetic / Pathological | The condition requires an artificial or unsupported combination established by the evidence. |

Apply these local rules:
- **Evaluation scope**: Evaluate the named distribution's effective configuration and the conditions required for the claimed impact. Classify differing impacts separately unless the caller specifies a headline impact.
- **Condition combinations**: For jointly required conditions (AND), take the highest tier number. For alternative supported, viable paths (OR), take the lowest. Mutually exclusive conditions do not form a viable path.
- **Configuration evidence**: Prefer source constants, fallback values, and packaging manifests for configuration claims. Supplied tutorials and templates establish Tier 3, not shipped defaults.
- **Tier ambiguity**: If evidence supports two adjacent tiers, choose the higher number. Tier 6 always requires affirmative evidence of an artificial or unsupported combination; missing evidence, age, or rarity alone is insufficient.
- **Insufficient evidence**: When required conditions cannot be classified from supplied evidence, report the missing information rather than inventing a tier.

## Output
For each classification, return:
- **`tier`:** an integer from 1 to 6, or `null` when supplied evidence is insufficient to classify the required conditions.
- **`description`:** a short explanation naming the evaluated target, claimed impact, required conditions, and the condition or packaging default that determined the tier. Identify any unresolved ambiguity that affected the choice, or the missing information when `tier` is `null`.

Make the description self-contained. Name relevant versions, flags, defaults, manifests, or deployment shapes supported by the evidence. Refer to product behavior and configuration directly; omit local repository paths and references to the PoC or test run.
