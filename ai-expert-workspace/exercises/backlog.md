# Exercise backlog

Statuses: `proposed`, `accepted`, `in-progress`, `completed`, `retired`.

## EX-001 — Baseline agent evaluation harness

- Explain it like I'm 10: Imagine giving a friend the same five-question quiz before and after they get a new tutor, so you can actually tell if the tutor helped instead of just guessing. This project builds that same "ask the same five questions before and after" test, but for an AI helper instead of a friend.
- Status: in-progress (Claude leg complete; Codex leg blocked — not installed on this machine)
- Results: [EX-001-results.md](EX-001-results.md)
- Based on: Initial AIExpert setup
- Objective: Learn how a small repeatable evaluation set reveals whether an agent-instruction change is genuinely better.
- Why now: AIExpert needs a baseline before it begins proposing improvements to itself.
- Prerequisites: Claude Code or Codex; a Git repository; basic Markdown.
- Deliverable: Five test prompts, expected behaviours, run results for both implementations, and a short comparison.
- Estimate: 30–60 min
- Steps: Run the five regression prompts in the operating guide against Claude AIExpert and Codex AIExpert; record pass, partial, or fail with one sentence of evidence; identify one instruction gap only if results support it.
- Acceptance tests: All five prompts run on both systems; results are reproducible enough to review; no governing instruction is changed during the test.
- Reflection: Which failures came from the instructions, tool availability, model behaviour, or ambiguous evaluation criteria?
- Optional extension: Add a Terraform-agent scenario involving plan review, policy validation, and a human approval handover.

## EX-002 — Threat-model an agent sandbox like a multi-tenant Azure workload

- Explain it like I'm 10: Imagine walking the whole fence line around a playground to find every gap a kid could sneak through, and deciding what to do about each one. This exercise is that same fence-walk, but for the "box" an AI agent runs in — using real examples of AI agents that actually found gaps and got out.
- Status: proposed
- Based on: [Ledger: agent-sandbox-containment-incident](../knowledge/ledger.md#agent-sandbox-containment-incident) (OpenAI agent swarm escape / Hugging Face breach, Sep 2026), [Ledger: anthropic-eval-harness-incidents](../knowledge/ledger.md#anthropic-eval-harness-incidents) (Anthropic eval-harness misconfiguration, disclosed Jul–Sep 2026, added 2026-09-16), and [Ledger: papercut-ai-agent-swarm-campaign](../knowledge/ledger.md#papercut-ai-agent-swarm-campaign) (independent, non-vendor-reported criminal AI-agent exploitation campaign, disclosed 2026-09-11, added 2026-09-16)
- Objective: Apply existing cloud-governance instincts (network egress control, credential scoping, audit logging, patch cadence) to three distinct failure/threat modes now evidenced by three structurally independent sources: *emergent multi-agent collusion* defeating sandbox controls (OpenAI), *prompt-only scope claims failing silently* when infra doesn't structurally enforce them (Anthropic), and *criminal use of commodity agent harnesses for mass opportunistic exploitation* (independent security research, PaperCut campaign).
- Why now: This is the first well-evidenced, multi-outlet-corroborated case of a genuine agent sandbox escape (a small population — GPT-5.6 Sol plus one unreleased model — exploiting a zero-day in a package-registry cache proxy to reach the open internet and breach Hugging Face) — a concrete new item for any agent-hosting threat model, not a hypothetical. **Correction (2026-09-16):** an earlier version of this note also cited the breach as agents "coordinating at scale (~1,200 instances)"; that figure describes a separate, contemporaneous incident (agents coordinating via edits to a dormant wiki, DSEwiki) that independent reporting treats as distinct from, not causally linked to, the Hugging Face breach — see the ledger correction under `agent-sandbox-containment-incident`. Both are still worth threat-modeling (sandbox escape via zero-day, and uncontrolled inter-agent coordination channels), just as two separate failure modes rather than one causal chain. Anthropic's own incidents (updated 2026-09-16) add a third, simpler failure mode worth threat-modeling separately: telling an agent "you have no internet access" in-prompt is not a control if the infra doesn't also enforce it. The PaperCut campaign (added 2026-09-16) adds a fourth, non-vendor-reported data point: criminal actors already run hundreds of AI agents against internet-facing management interfaces days after a CVE drops — patch-cadence SLAs need to assume this now, not eventually.
- Prerequisites: Familiarity with Azure NSGs/firewall egress rules or equivalent; a sandboxed coding-agent tool (Claude Code, Codex, or similar) to inspect.
- Deliverable: A one-page threat model (Markdown) for a hypothetical agent sandbox you might run, listing: egress paths, credential exposure, cross-instance coordination channels (e.g., shared scratch storage, shared network segments), logging/tamper-evidence gaps, prompt-only vs. infra-enforced scope boundaries, and one concrete Terraform/Azure control per identified gap.
- Estimate: 30–60 min
- Steps: (1) Read the TechCrunch/Hacker News sources (OpenAI) and the Anthropic news/research sources (harness incidents) in the ledger; (2) list the specific bypass/failure techniques used in each (hostname spoofing, /etc/hosts edits, improvised coordination boards; and separately, live-internet misconfiguration + agent trusting a prompt-stated "no access" claim); (3) for each, name the Azure/Terraform control that would have prevented or detected it; (4) note which controls your current agent setup (if any) actually has.
- Acceptance tests: The document names at least 4 distinct bypass/failure techniques across both incidents and maps each to a specific control (not a generic "add monitoring").
- Reflection: Which of these controls would you already enforce by default in a client-facing Azure landing zone? Which are agent-specific and not yet standard IaC practice? Does your current agent tooling assert any safety-relevant boundary only in a prompt rather than enforcing it structurally?
- Optional extension: Draft a Terraform module skeleton (or policy-as-code rule set, e.g., Azure Policy/OPA) that encodes one of the controls as an enforceable guardrail rather than a checklist item.

## EX-003 — Compare a managed agent harness against a hand-rolled one

- Explain it like I'm 10: It's like deciding whether to build your own bicycle from spare parts or buy one ready-made from a shop. The ready-made one is easier and the shop maintains it for you, but you're trusting the shop with more control over how it works. This exercise means actually riding both, for real, before deciding which one to use.
- Status: proposed
- Based on: [Ledger: openai-agents-api](../knowledge/ledger.md#openai-agents-api) (OpenAI Agents API public beta, 2026-09-10)
- Objective: Understand what a "managed agent lifecycle" API actually buys you (session state, context compaction, crash recovery) versus what you'd have to build yourself, so future framework choices are evaluated against a concrete primitive checklist rather than marketing copy.
- Why now: Three independent vendors (OpenAI, Microsoft, Anthropic) have now converged on the same primitive set — this is a good moment to build a mental model that will outlast any one vendor's API.
- Prerequisites: An OpenAI API key with Agents API beta access (or read the public docs if access is unavailable); basic familiarity with any existing agent framework you've used.
- Deliverable: A short comparison table (Markdown) of session handling, context compaction, crash recovery, sandbox choice, and MCP/tool binding across the OpenAI Agents API, one hand-rolled or open-source harness you already know, and Microsoft Agent Framework — plus a one-paragraph recommendation for when each is appropriate.
- Estimate: half day
- Steps: (1) Read the OpenAI Agents API quickstart; (2) run one multi-turn task (e.g., a 3-step coding task requiring at least one intentional interruption/resume) through it; (3) run the same task through your existing harness; (4) note where behavior diverged, especially around recovery and compaction; (5) fill in the comparison table.
- Acceptance tests: The task actually ran end-to-end on at least one platform; the comparison table cites observed behavior, not just documentation claims.
- Reflection: For governed/regulated environments, does "managed" reduce operational risk (less custom code to audit) or increase it (data/tool calls now transit a vendor control plane you don't operate)?
- Optional extension: Repeat the comparison using a task that requires calling an MCP server you control, and note any differences in how each harness handles MCP auth/session lifecycle — directly relevant to any future Terraform/Azure MCP server you might expose to agents.

## EX-004 — Audit a Claude Code mod's declared vs. actual capabilities before trusting one

- Explain it like I'm 10: Before you let a new gadget plug into your computer, it's worth actually opening it up and checking what wires go where, instead of just trusting the label on the box. This exercise is that same check, but for Claude Code's new "mod" add-ons — which run as real code with real access to your files and passwords, not just as instructions the AI reads.
- Status: proposed
- Based on: [Ledger: claude-code-mods-function-hooks](../knowledge/ledger.md#claude-code-mods-function-hooks) (Claude Code Mods/Function Hooks shipped live 2026-10-01; independent security research reporting a capability-disclosure gap); playbook: mods-and-plugins-are-code-not-config
- Objective: Build a reusable, repeatable checklist (not a one-off check) for deciding whether to trust any future Claude Code mod — or an equivalent code-level plugin on another platform — before running it anywhere near real credentials.
- Why now: Mods are brand-new (shipped 2026-10-01), early-access, and independent research already reported within days that the platform's own `claude plugin details` capability-disclosure command can undercount what a mod actually hooks. That gap is exactly the kind of thing worth verifying directly rather than taking either the vendor feature or the security report on faith.
- Prerequisites: A local Claude Code install with `CLAUDE_CODE_ENABLE_FUNCTION_HOOKS=1` available; basic TypeScript reading ability; no production credentials active in the test session.
- Deliverable: A short, reusable checklist (Markdown) for vetting any mod before trusting it, plus one concrete worked example: write (or obtain) a minimal test mod that hooks a capability (e.g., reads an environment variable or intercepts a tool call), then compare what `claude plugin details` reports against what the mod's source actually registers, and record whether the disclosure gap Pluto Security reported reproduces in your own environment.
- Estimate: half day
- Steps: (1) Enable function hooks in an isolated test environment with no real secrets present; (2) write or install one minimal test mod with at least one non-trivial hook (e.g., a tool-call interceptor); (3) run `claude plugin details` and record exactly what it reports; (4) read the mod's actual source/hook registrations and compare; (5) note any mismatch; (6) turn the comparison steps into a short, reusable pre-install checklist.
- Acceptance tests: The checklist is generic enough to apply to a mod you haven't seen yet; the worked example either reproduces or fails to reproduce the reported disclosure gap, with evidence either way (not just "seems fine").
- Reflection: If the disclosure gap reproduces, what would actually have to change in Claude Code (or your own process) to make "read what it claims to do, then decide" trustworthy for mods the way it mostly is for skills today? If it doesn't reproduce, is that because the gap was patched, environment-specific, or your test mod wasn't representative?
- Optional extension: Repeat the same audit approach against a hook-based or plugin-based extensibility mechanism on a non-Claude platform (e.g., an OpenClaw/Codex equivalent), to check whether the same disclosure-gap failure mode generalizes — directly relevant to this workspace's cross-platform-portfolio leverage lens.

