# AI agents: a beginner's guide

<!-- Single flowing guide document, not a dated/entry-based log like ledger.md or
playbook.md. Rendered as one page by parser.parse_agents_guide() -- the whole body
after this H1 is treated as one piece of prose, not split into separate entries. -->

If you've never built one of these before and just want to know what people mean
when they say "AI agent" and how to make your own, start here. Everything else on
this site assumes you already know this; this page doesn't.

## What is an agent?

Ask Claude a question in a chat window and you get one answer. Close the tab, and
it has no memory of who it's supposed to be or how it's supposed to behave next
time — you have to re-explain yourself every time.

An **agent** is Claude given a standing job description, a fixed toolbox, and
permission to keep working across several steps on its own, instead of one
question in and one answer out. Think of the difference between asking a friend a
one-off favor and actually hiring someone: you give the hire a written job
description (what they're for, what "done" looks like), a set of keys to exactly
the rooms they need and no others, and then you let them get on with it without
supervising every single move.

In **Claude Code** specifically (the tool that built this whole site), an agent
like this is called a **subagent**: a small Markdown file that lives in a
project's `.claude/agents/` folder. It has a name, a description, a list of tools
it's allowed to use, and a body of plain-English instructions. Claude Code reads
that file and, when the description matches what you're asking for, hands the
task to that agent instead of handling it in the default, generic way.

## How do you create one?

1. **Decide the one job it does.** Not three jobs — one. "Reviews code" is a job.
   "Reviews code, writes the docs, and deploys it" is three agents wearing a
   trench coat.
2. **Create the file**: `.claude/agents/<name>.md` in your project (or
   `~/.claude/agents/<name>.md` for one that works across *every* project, not
   just this one).
3. **Write the frontmatter** at the top of the file:
   ```yaml
   ---
   name: quiz-maker
   description: Writes a short quiz on a subject the user names. Use PROACTIVELY
     when the user asks for a quiz, test, or practice questions on a topic.
   tools: Read, Write
   ---
   ```
   The `description` matters more than anything else in the file — it's the only
   thing Claude Code reads *before* deciding whether to use this agent at all. A
   vague description ("helps with stuff") means the agent either never gets
   picked, or gets picked for the wrong task. Say exactly what it does and when to
   reach for it.
4. **Write the instructions** below the frontmatter, in plain English: who it is,
   the exact steps it follows every time, and what "finished" actually looks
   like. Be concrete — "write good tests" is a hope, not an instruction; "write at
   least one test that covers the failure case, then run the suite and don't stop
   until it's green" is an instruction.
5. **Test it on something small and low-stakes** before you trust it with
   anything that matters. Read what it actually produced. Don't assume a
   well-worded instruction file means well-behaved output — see
   [Treat every governing instruction as advisory until regression-tested](playbook.md#instructions-are-not-controls)
   in the Playbook tab.

You can also just ask Claude Code itself — "write me an agent that does X" — and
it will draft the file for you. That's a perfectly good starting point. Read what
it wrote and edit it before trusting it, the same as you would with any other
code someone handed you.

## What to make sure you add

- **A specific, trigger-worthy description.** This is the single most common way
  a first agent fails silently — not because the instructions were bad, but
  because Claude Code never picked it in the first place.
- **A tight, least-privilege tool list.** Only grant what the job actually needs.
  A summarizer that only ever reads and writes text doesn't need `Bash`; a code
  reviewer that's supposed to be an independent check doesn't need `Edit` (see the
  third example below).
- **A clear definition of "done."** Something you or the agent can actually check
  — a file that exists, a test that passed, a specific output shape — not just a
  feeling that it probably went fine.
- **A real verification step**, not just an instruction to be careful. "Double
  check your work" is advisory. "Run the test suite and quote the actual output"
  is a control. This is the difference this whole site's Playbook was built
  around — see
  [instructions-are-not-controls](playbook.md#instructions-are-not-controls).
- **An explicit boundary on what it can't do without asking you.** Especially:
  editing its own instructions, taking an action it can't undo, or touching
  something outside the one job it was given. See
  [air-gap-governing-writes](playbook.md#air-gap-governing-writes).

## What to make sure you leave out

- **Every tool "just in case."** More access than the task needs isn't harmless —
  it's the single most common ingredient in the real incidents recorded in this
  site's [Findings](ledger.md) tab.
- **Vague trust instead of a real check.** "Always ask before doing X" only works
  if something actually stops it when it forgets. If nothing structurally
  enforces the boundary, it's a suggestion, not a rule.
- **Several unrelated jobs crammed into one file.** If you're writing "and also"
  more than once in an agent's description, it's probably two or three agents,
  not one. Small, single-purpose agents are also easier to test, reuse, and trust
  — the same reasoning behind this site's own
  [agent/skill factory](playbook.md) thinking.
- **Blind trust in content it reads.** Anything it fetches from the web, or reads
  from a file it didn't write itself, should be treated as data to look at — never
  as an instruction to obey. See
  [untrusted-content-is-data-not-instructions](playbook.md#untrusted-content-is-data-not-instructions).

## Three agents worth building first

### 1. A report-writer — turns notes or code into a polished PDF

**Job:** point it at a repo, a folder of notes, or a chat transcript, and it reads
the real content and produces an actual PDF write-up — not a guess at what's
probably in there.

**Tools:** `Read`, `Write`, `Bash` (to actually render the PDF).

**The trap to avoid:** letting it invent a number, date, or fact it didn't
verify. The single most important line you can put in an agent like this is
something close to: *"every fact, number, and file path must come from something
you actually read — if you don't know, say so, don't guess."* A polished-looking
report with a made-up statistic in it is worse than no report at all.

### 2. A quiz-maker — turns any subject you name into a short test

**Job:** given a topic and (optionally) a difficulty level, produce a handful of
questions plus an answer key.

**Tools:** none required for general-knowledge subjects; add `WebSearch` only if
it needs to check current facts first.

**The trap to avoid:** an ambiguous question with more than one defensible right
answer, or a wrong answer key it never double-checked against its own questions.
Worth instructing it explicitly to re-read each question and confirm exactly one
answer is correct before finalizing — the same "verify, don't just assert"
principle as everywhere else on this page.

### 3. A code-review agent — an independent second look at a change

**Job:** given a diff or a specific set of files, it reports what's wrong —
correctness bugs, missed edge cases, convention violations — without touching
anything itself.

**Tools:** `Read`, `Grep`, `Bash` (for `git diff`) — deliberately **no** `Write`
or `Edit`.

**The trap to avoid:** giving it the ability to fix what it finds. The moment a
reviewer can also edit the code, it stops being an independent check — it's just
a second author. Keeping review and implementation as two separate agents (one
that writes, one that only looks) is a small, cheap pattern that shows up
throughout real multi-agent setups, including ones this site's own agent audits
have reviewed.

## Where to go deeper

The [Playbook](playbook.md) tab has the full, evidence-backed list this page
draws from, each entry with its reasoning, sources, and a bad/good instruction
example. You can also download the current list as a single Markdown file from
the link at the top of this site (**Agent best practices (.md)**) and drop it
straight into another project's `CLAUDE.md`.
