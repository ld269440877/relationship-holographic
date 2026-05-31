# Codex Coding Rules

Use these rules for every software-engineering task in this repository.

## Andrej Karpathy Skills

- Think before coding: identify the concrete goal, verify assumptions from source, and call out risky ambiguity before editing.
- Prefer minimal working code: implement the smallest change that satisfies the goal; avoid speculative features and unnecessary abstractions.
- Make surgical edits: change only required files and lines; preserve existing comments, formatting, APIs, data, and user changes.
- Execute toward verifiable targets: turn the request into checks, run the relevant validation, and iterate until it passes or the blocker is clear.

## Work Loop

1. Read the smallest useful context.
2. Define the user-visible outcome and risk.
3. Choose the simplest local change.
4. Edit only what is needed.
5. Run focused validation.
6. Report what changed and what passed.

## Guardrails

- Do not rewrite nearby code just because it looks imperfect.
- Do not remove legacy code or comments unless your own change makes them obsolete.
- Do not add broad architecture where a local helper or direct fix is enough.
- Treat unfamiliar worktree changes as user work and leave them intact.
