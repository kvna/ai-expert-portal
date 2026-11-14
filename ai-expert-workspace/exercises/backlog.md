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

## EX-004 — Audit an MCP server/client config against the 2026-07-28 deprecation list

- Explain it like I'm 10: MCP is the standard plug that lets an AI assistant talk to outside tools, and the plug just got redesigned with a one-year countdown sticker on a few older parts. This exercise is going through one real MCP setup you actually use and checking, part by part, whether it's leaning on any of the parts with a countdown sticker on them — like checking an old appliance against a recall notice instead of waiting for it to stop working.
- Status: proposed
- Based on: [Ledger: mcp-spec-stateless-and-deprecations](../knowledge/ledger.md#2026-07-28-mcp-spec-stateless-and-deprecations--mcps-biggest-spec-revision-yet-drops-the-session-handshake-deprecates-rootssamplinglogging-and-httpsse-with-a-12-month-removal-clock-now-running); [playbook: mcp-2026-07-28-deprecation-audit](../knowledge/playbook.md#mcp-2026-07-28-deprecation-audit--audit-every-mcp-serverclient-you-maintain-against-the-2026-07-28-specs-deprecation-list-the-clock-on-removal-is-already-running)
- Objective: Turn the abstract spec-deprecation list into a concrete pass/fail check against one real MCP server or client config you actually use (e.g., one of the `mcp__*` tool integrations active in this session), so the next MCP integration gets checked by habit rather than by memory.
- Why now: the 12-month deprecation clock on `initialize`/session-stickiness, Roots/Sampling/Logging, HTTP+SSE transport, and Dynamic Client Registration started 2026-07-28 — checking now costs an hour; checking after something breaks near the deadline costs much more.
- Prerequisites: Access to at least one MCP server/client config (this session's own `.mcp.json`/tool config is sufficient); the official spec changelog open for reference.
- Deliverable: A short Markdown checklist (one row per deprecated feature) marking each as "not used," "used — migration needed," or "unknown — needs vendor confirmation," for one real MCP integration, plus one sentence per "used" row on what the fix looks like.
- Estimate: 30–60 min
- Steps: (1) Pick one MCP server/client integration you actually use; (2) read its config/docs for session handling, auth flow, and transport; (3) check each against the four deprecated-feature categories in the playbook entry; (4) for anything unclear, check the server's own changelog or ask the maintainer rather than guessing; (5) write the checklist and one-line fixes.
- Acceptance tests: Every deprecated-feature category has an explicit mark (not left blank); at least one row cites a specific config line, doc excerpt, or changelog entry as evidence, not just an assumption.
- Reflection: Did the audit find anything actually at risk, or confirm the integration is already clean? Either way, would you have known that without checking?
- Optional extension: If you maintain or could configure an MCP server yourself (vs. only consuming one), confirm which spec version it declares and whether its SDK has adopted `2026-07-28` yet.

