---
description: Cross-model verification skill. Run the VERIFY stage with a different LLM/agent than the one that authored the code or analysis. A model is blind to its own mistakes, so self-review misses errors that an independent model catches. Model-agnostic — it requires only that the verifier differ from the author, never a specific vendor or model.
category: verification
tags: [verification, cross-model, review, agentic, workflow, quality-gate, second-opinion]
requires_tools: [terminal, delegate_task]
requires_env_vars: []
python_dependencies:
  - pytest
---

# Cross-Model Verification Skill

Use this skill at the VERIFY stage of any explore–plan–code–verify workflow. Its
single rule: **the model or agent that verifies must be different from the model
or agent that produced the work.** It is deliberately model-agnostic. It does not
require any particular vendor or model; it only requires that author and verifier
are not the same model.

## Why

A model is weak at auditing its own output. The assumptions, omissions and biases
that let an error through generation are the same ones that let it through
self-review, so a model tends to approve its own mistakes. An independent model
does not share those blind spots and catches far more. Self-review inflates
confidence without adding evidence; cross-model review adds a genuinely
independent check.

## The rule

1. Record the **author**: the model/agent (and version) that wrote the code,
   chose the inputs, or produced the analysis.
2. Choose a **verifier**: any model/agent whose identity differs from the author.
   It may be a different vendor, a different model family, or simply a different
   model instance with no access to the author's reasoning trace. Do not let the
   author verify itself.
3. The verifier works **adversarially and independently**: it does not trust the
   author's narrative, re-derives results where feasible, and tries to break the
   work rather than confirm it.

## Procedure

1. **Hand off.** Delegate the work to a verifier that is not the author model
   (use `delegate_task` to a different agent, or re-open the artifact in a
   separate session driven by a different model). Pass only the artifact and the
   claim to be checked, not the author's chain of thought.
2. **Re-derive, do not re-read.** Recompute key numbers from first principles or
   from an independent path. If the author used library A, spot-check with method
   B. Never accept a result solely because the author's text asserts it.
3. **Run the physical and logical checks** (see below).
4. **Run the tests** with `pytest` (or the project's runner) on a clean
   environment; confirm they actually exercise the claim, not just import it.
5. **Report** with a clear verdict and the provenance of author vs verifier.

## What the verifier checks

- **First principles / physical bounds.** Conservation holds; efficiencies stay
  below their thermodynamic limit (e.g. Carnot); quantities that must be positive
  are positive; nothing is evaluated outside a model's valid range.
- **Units and dimensions.** Every equation is dimensionally consistent; SI is
  used internally; conversions are explicit.
- **Silent fallbacks.** A library that fails should raise, not quietly return a
  degraded or mixed-reference result. Flag any path that substitutes one source
  for another without saying so.
- **Inputs vs structure.** Separate "the answer is wrong because the model is
  wrong" from "the answer is sensitive to an uncertain input." Report which.
- **Tests.** Known-value checks, monotonicity, and invalid-input rejection are
  present and pass.

## Output format

```
AUTHOR:   <model/agent + version that produced the work>
VERIFIER: <different model/agent + version doing this review>
VERDICT:  PASS / NEEDS REVIEW / FAIL
FINDINGS: <bullet list; cite file and line; mark each as confirmed or unverified>
FIXES:    <numbered, specific>
```

If the verifier did not actually recompute a result, it must say "unverified"
rather than imply confirmation.

## Provenance

Record, alongside every verified result, which model authored it and which model
verified it. A result checked only by its own author is marked "self-reviewed,
not cross-verified" and treated as unverified until an independent model has
signed off.

## Anti-patterns

- The author model approving its own work ("looks correct to me").
- Re-reading the author's explanation instead of re-deriving the result.
- Requiring a specific named model — the rule is *different from the author*, not
  *a particular brand*.
- Treating passing tests written by the author as sufficient; the verifier should
  add or re-run independent checks.
