# Decisions Log — Contract Intelligence & Clause-Risk Platform

This is interview-prep material as much as it is a build log. Every entry should be
something you could explain out loud, unscripted, in under 60 seconds. If you can't,
that's a sign you don't fully understand the decision yet — go back and firm it up
before moving on, don't just log it and move past it.

Format per entry:
```
## [Decision title]                                    Phase: A/B__
Date:
Options considered:
Chosen:
Why:
Trade-off accepted:
Interview angle: (the one sentence you'd say if asked "why did you do it this way")
```

---

## Example (delete once you have real entries)
Phase: B3
Date:
Options considered: trust LLM citations as-is vs. programmatically verify each citation against retrieved context
Chosen: programmatic verification
Why: LLMs will confidently cite chunks that don't actually support the claim; verification catches this before it reaches the user
Trade-off accepted: slightly more latency per query, and some correct-but-unverifiable claims get suppressed rather than shown
Interview angle: "I don't trust LLM output by default — I built a verification layer that checks every citation against the actual retrieved context before returning it, which is how I catch hallucinated claims before a user sees them."

---

<!-- Real entries below. Suggested minimum set to cover across the build:
- Phase A: tenant isolation strategy (RLS vs app-layer)
- Phase A: chunking strategy and size/overlap
- Phase A: idempotent ingestion approach
- Phase B: embedding model + vector store choice
- Phase B: hybrid retrieval (why not vector-only)
- Phase B: citation verification mechanism
- Phase B: ReAct-loop vs single-prompt agent design
- Phase B: the specific prompt injection you tested and how you defended against it
- Phase B: your eval methodology and the actual before/after numbers
- Phase B: rate-limit/cost resilience approach
Add more as they come up — anything you deliberated over for more than 5 minutes
probably belongs here. -->
