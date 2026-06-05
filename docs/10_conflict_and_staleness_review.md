# Conflict and Staleness Review

This document checks whether the uploaded papers conflict with each other or introduce outdated assumptions for this project.

---

## 1. Current Project Thesis

The project thesis after integrating the new survey is:

> Build a harness-engineered multi-agent system that can use CLI and Browser tools safely, package capabilities as testable skills, and optimize not only success but also cost under explicit budgets.

The current architecture remains:

```text
Harness Engineering
+ Skill Packages
+ CLI / Browser Agents
+ Safety Gate
+ Trace Logging
+ Verifier
+ Auto Repair Loop
+ Efficiency Metrics
```

---

## 2. No Direct Conflict: Efficient Agents Survey vs Meta-Harness

The efficient-agents survey says an efficient agent must optimize memory, tool use, and planning costs. Meta-Harness says harness code determines what information is stored, retrieved, and presented to the model.

These are compatible:

```text
Efficient Agents Survey = what to measure and optimize
Meta-Harness = how to iteratively improve the harness that controls those costs
```

Project decision:

- keep Meta-Harness as the outer-loop improvement idea,
- add efficiency metrics to every candidate harness comparison.

---

## 3. Tension: More Planning vs Budgeted Planning

ReCAP and GraSP improve long-horizon reliability through structured planning and graph execution. The efficient-agents survey warns that planning itself has cost and must be budget-aware.

Resolution:

```text
Use structured planning, but bound it.
```

Implementation rule:

- ReCAP-style parent plan reinjection is allowed.
- Recursive depth must be limited.
- Replanning count must be logged.
- If local repair is available, prefer local repair over global replan.
- If task is simple, do not invoke multi-agent planning.

---

## 4. Tension: Tool-Integrated Reasoning vs Tool Overuse

Tool-integrated reasoning is important for CLI/browser tasks, but the survey warns that tools add latency, environment complexity, and tool-call overhead.

Resolution:

```text
Tool calls require expected value.
```

A tool call is justified when it:

- reduces uncertainty,
- obtains external evidence,
- verifies a claim,
- changes the environment toward the goal,
- is required by the benchmark success criteria.

A tool call is suspicious when it:

- repeats a recent failed action,
- fetches information already present in pinned evidence,
- is triggered only by untrusted browser text,
- tries broad exploration without a concrete subgoal.

---

## 5. Tension: Skill Packages vs Strategy Genes

MUSE-Autoskill and SkillX support rich skill packages. Strategy Gene argues that documentation-heavy skills can be inefficient or harmful at runtime.

Resolution:

```text
Use full skill packages for maintenance.
Use gene.yaml for runtime context.
```

Do not inject full `SKILL.md` unless the agent is explicitly maintaining or repairing a skill.

---

## 6. Tension: LightMem Compression vs Critical Debug Data

LightMem supports compression and topic-aware memory. However, CLI/browser tasks contain critical identifiers that must not be compressed away.

Protected data:

- file paths,
- line numbers,
- stack traces,
- exit codes,
- ports,
- URLs,
- selectors,
- environment variable names,
- error signatures,
- security alerts.

Project rule:

```text
Compress explanations, not identifiers.
```

---

## 7. Tension: Adaptive Multi-Agent Topology vs MVP Simplicity

OFA-MAS and the efficient-agents survey both discuss topology optimization. This project should not begin with learned topology generation.

Resolution:

```text
MVP uses fixed topology.
Later versions may evaluate adaptive topology.
```

MVP topology:

```text
Orchestrator -> CLI Agent / Browser Agent -> Verifier -> Logger -> Repair Loop
```

Later topology experiments:

- planner only,
- planner + verifier,
- planner + CLI + browser,
- planner + CLI + browser + code reviewer,
- role-play single model vs true multi-model deployment.

---

## 8. Potentially Outdated or Risky Assumptions

### A. External paper dates are future / preprint-heavy

Many uploaded papers are dated 2026 and are likely preprints or early conference versions. Treat them as design inspiration, not settled facts.

### B. Benchmarks differ from this project

ALFWorld, WebShop, LongMemEval, LoCoMo, and BrowseComp are useful references but do not directly validate CLI/browser harness behavior.

### C. Tool environments differ

SkillX and many tool-learning methods assume stable tool schemas. Real web browsing is less stable. For MVP, use local fixtures and localhost apps.

### D. LLM-as-judge is not enough

Several papers use LLM judges. This project should prefer executable checks:

- pytest pass/fail,
- browser console errors,
- file diff,
- safety violation detection,
- explicit eval YAML success criteria.

---

## 9. Final Conflict Resolution Matrix

| Topic | Papers in Tension | Project Decision |
|---|---|---|
| Planning depth | ReCAP / GraSP vs Efficient Agents Survey | Structured but budgeted planning |
| Tool use | TIR methods vs cost-aware tool learning | Tool calls require expected value |
| Skill detail | MUSE / SkillX vs Strategy Gene | Full package for maintenance, gene for runtime |
| Context size | ReCAP continuity vs AgentSwing / LightMem compression | Preserve parent plan and pinned evidence; compress noise |
| Multi-agent design | OFA-MAS vs MVP practicality | Fixed topology first, adaptive topology later |
| Evaluation | Benchmark papers vs project needs | Executable local benchmarks first |

---

## 10. Review Result

No major contradiction invalidates the project. The main update is that the project must explicitly report efficiency, not just success. The strongest revised claim is:

> This project builds a safety-aware, traceable, skill-centric agent harness and evaluates it on both task success and cost efficiency.
