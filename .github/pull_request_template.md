<!-- Risk lives in the risk:<level> label. Only for high or critical, start the body with one line
"Risk high: <what can break>" (or "Risk critical: ..."), one concrete sentence.
Stacked PR only: add "Stacked on #<n>: merge it first." -->

## Summary
<!-- 1-2 sentences: what changes and why; it must stand alone. Only if something important was not
verified (CI not run, behaviour against a real service), say so in the last sentence. -->
<what changes, and why>

<!-- ONE visual, never several, or none when the summary already says everything (docs, bump, one-liner).
Rule or behaviour: this table, max 3 rows, max 12 plain words per cell, no file, function or test names.
Flow or state: a small Mermaid diagram. Numbers or limits: a before/after values table. Contract or config: a ```diff of max 15 lines. -->
| What | Before | After |
|---|---|---|
| <rule, in plain words> | <before> | <after> |

<!-- Only with a real step (migration, env var or secret, flag, merge order, external config); otherwise delete it.
Mention rollback only when it is not a plain revert. If the diff contradicts the handoff notes, add one **Mismatch:** line. -->
**Deploy:** <the step>
