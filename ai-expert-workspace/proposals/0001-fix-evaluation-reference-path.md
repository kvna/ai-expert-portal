# AIExpert improvement proposal: Fix broken `references/evaluation.md` pointer

- Explain it like I'm 10: Imagine a recipe that says "see page 12 for the sauce," but the book doesn't have a page 12. This proposal is about writing the missing page 12, so the recipe (the AI's own instructions) actually works when someone follows it.
- Date: 2026-09-16
- Status: implemented (2026-09-16)
- Triggering evidence: EX-001 baseline run (see `exercises/EX-001-results.md`). `.claude/agents/ai-expert.md` instructs AIExpert to "run the regression prompts in `references/evaluation.md`" after an approved change, but that file does not exist in the kit or workspace. The actual regression prompts live only in `ai-expert-kit/codex/.agents/skills/ai-expert/references/operating-guide.md`, a Codex-scoped file not shipped alongside the Claude Code install.
- Current limitation: A future AIExpert run trying to follow its own post-change validation step literally cannot find its evaluation suite. The Claude Code install has no `references/` directory at all.
- Proposed change: Either (a) copy the "Regression prompts" section from `ai-expert-kit/codex/.agents/skills/ai-expert/references/operating-guide.md` into a new `ai-expert-workspace/references/evaluation.md` shared by both platforms, and repoint both agent definitions at that shared path; or (b) correct the path in `.claude/agents/ai-expert.md` to point at the existing Codex-side operating guide. Option (a) is preferred since it keeps the eval suite platform-neutral and in the cumulative workspace rather than duplicated per platform.
- Expected benefit: Self-improvement changes can actually be regression-tested per AIExpert's own stated workflow; removes a broken cross-reference.
- Risks and possible regressions: None identified — this only adds/corrects a reference path, no behavior change.
- Permission/tool implications: None — no new tools, permissions, or access.
- Rollback: Delete the new file / revert the path edit; trivial single-file change.
- Validation plan: Re-run the EX-001 regression prompts after the change and confirm the agent can locate and follow `references/evaluation.md` without being told where it is.
- Files affected: `ai-expert-workspace/references/evaluation.md` (new), `.claude/agents/ai-expert.md`, `ai-expert-kit/claude/.claude/agents/ai-expert.md` (kit copy, for future installs), `ai-expert-kit/codex/.agents/skills/ai-expert/SKILL.md` (if it points elsewhere)

## Proposed patch

```diff
# Option (a), sketch — not applied:
+ ai-expert-workspace/references/evaluation.md
    (copy of the "Regression prompts" section currently only in
     ai-expert-kit/codex/.agents/skills/ai-expert/references/operating-guide.md)

  .claude/agents/ai-expert.md
    (already correctly says "references/evaluation.md" — no edit needed
     once the file above exists)
```

## Decision

Approved by user (2026-09-16). Implemented as option (a): created `ai-expert-workspace/references/evaluation.md` and `ai-expert-kit/shared/references/evaluation.md` (so future installs of the starter kit also have it) containing the five regression prompts. No agent definition needed editing — `.claude/agents/ai-expert.md` and the kit's Codex `SKILL.md` already pointed at the correct paths once the target files existed. Validated: see `knowledge/changelog.md` entry and the follow-up regression check.
