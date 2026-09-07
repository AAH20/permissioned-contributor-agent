# Loop engineering and AI agent evolution parameters

The implemented loop checks permission, retrieves bounded context, verifies citations and domain coverage, then either retries, abstains or pauses for a human. It has no model tools or external write authority. Optimization proposes offline experiments; it does not modify a running agent.

## Effective parameters

| Parameter | Default | Allowed range / behavior | Enforcement |
|---|---:|---|---|
| `max_iterations` | 2 | Integer 1–3 | Stop retrying; unresolved evidence abstains |
| `max_seconds` | 30 | >0 and ≤60 for local experiments | Cooperative checks at analysis boundaries and each finding |
| `top_k` | 3 | Integer 1–5 | Bound retrieved document count |
| `graph_hops` | 1 | 0 or 1 | Disable graph expansion for lexical baseline, or expand one curated hop |
| `max_context_chars` | 12,000 | 100–20,000 | Reject oversized replay batches and retrieved text |
| `max_model_calls` | 0 | Must remain 0 | No model dispatcher in the shipped implementation |
| `max_external_writes` | 0 | Must remain 0 | No external-effect executor |
| Graph recursion limit | 16 | Internal graph setting | Additional graph-run bound |
| Findings per replay batch | 18 | Maximum | Reject oversized input |
| Human approval lifetime | 3,600 seconds | Also limited by consent expiry | Recheck grant, payload digest and one-use review state |

The runtime allows up to 60 seconds for a local experiment, while the proposed production p95 gate is 30 seconds. A cooperative check cannot interrupt a blocked CPU or network operation. A production worker needs an enforced deadline, resource isolation and cancellation; those controls are not supplied here.

Authorization failure stops immediately. Invalid citations or missing domains use at most the retry budget. A second supplied fixture can repair an error; the implementation does not invent missing evidence. An exact quote supports provenance, not the meaning of a conclusion.

## Offline evolution

`examples/evolution.json` records the baseline. `assess_parameter_proposal(current, proposed)` accepts only `top_k`, `graph_hops` and `max_iterations` within their bounds. It returns an unapplied candidate for offline evaluation. Unknown fields and permission changes are rejected.

Future ranking/prompt changes require separately reviewed code. Tenant scope, member identity, source allowlists, consent, human approval and external-action restrictions must never be optimized away.

1. Freeze a versioned dataset by organization and document family: 60% training, 20% development, 20% holdout.
2. Propose one change; record code, source, prompt/model and dataset hashes where applicable.
3. Evaluate lexical-only versus graph-assisted retrieval and the incumbent versus candidate under the same budgets.
4. Inspect false negatives, unsupported claims, abstentions and latency rather than optimizing a single aggregate score.
5. Require independent holdout evidence and human release approval. Roll back on any scope violation, critical miss, citation regression or reviewer stop.

Dataset split/audit and deployed rollback are process requirements, not implemented automation. `max_calls_per_case=12`, `token_ceiling_per_case=24000` and `cost_ceiling_usd_per_case=2` appear only in a **disabled future model-trial configuration**. They are not active provider metering. Before adding models, reserve budget before dispatch, account for concurrency, reject overruns and verify actual usage receipts.

## LangGraph limitations

[LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) pause and resume execution, but replay can re-execute earlier node code. Keep pre-interrupt operations idempotent. This example uses `InMemorySaver`; it does not survive restarts and is not a multi-user authorization service. The local caller and injected objects are trusted. Production requires authenticated reviewer identity, durable atomic review consumption and transactional revocation checks.
