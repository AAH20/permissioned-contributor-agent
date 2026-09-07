# AI agent evaluation: KPIs, measurement and release gates

This scorecard separates software regression tests, synthetic component measurements and independent real-world evaluation. A test count measures tested behavior, not the probability of a correct answer. The machine-readable report records its measurement scope and retains `null` when a KPI has no denominator.

## Quality and safety scorecard

| KPI | Definition / denominator | Proposed gate or objective | Current measurement | Accountable owner |
|---|---|---|---|---|
| Citation precision | Supported accepted citations / all accepted citations | 1.00 | Exact substring and salience checks on synthetic quotes; not semantic entailment | Evaluation maintainer |
| Retrieval recall | Sum of relevant retrieved documents / sum of gold relevant documents (micro average) | ≥0.95 | Known synthetic document IDs | Retrieval maintainer |
| Recommendation precision@5 | Relevant IDs in first five recommendations / 5, averaged over queries with eligible gold opportunities | ≥0.80 | Not measured; absent positions count as misses | Member + evaluator |
| Critical false negatives | Gold critical finding IDs absent from detected IDs | 0 observed | Fixture labels only; never inferred from a model's confidence | Domain expert |
| Unsupported critical claims | Accepted citations labeled critical and unsupported | 0 observed | Synthetic exact-quote verification | Domain expert |
| Unauthorized reads | Content reads occurring without effective consent and policy authority | 0 observed | Adversarial regression checks; fixture counters | Security maintainer |
| Unauthorized writes | Disallowed external mutations executed | 0 observed | No write implementation; negative tests | Security maintainer |
| Cross-tenant leaks | Unauthorized tenant records reaching retrieval/output | 0 observed | Synthetic isolation tests | Security maintainer |
| Approval bypasses | Review-required results released without matching approval | 0 observed | Payload, expiry, grant and replay tests | Security maintainer |
| Abstention rate | Cases with abstention / all evaluated cases | Report with recall; no universal optimum | Computed from explicit case outcomes | Product + evaluator |
| Completion rate | Cases meeting defined outcome / all evaluated cases | Report by case type | Component verification only | Evaluation maintainer |
| Independent holdout units | Unique adjudicated organization/document-family groups in holdout | ≥200 | 0 | Independent evaluator |
| Critical holdout units | Unique holdout groups with ≥1 gold critical finding | ≥50 | 0 | Qualified domain reviewer |
| Dataset leakage | Train/development units overlapping holdout groups | 0 | Requires external dataset audit; not auto-verified here | Dataset owner |
| Evidence freshness | Evidence within policy TTL / all evidence considered for release | 1.00 | GitHub timestamp policy tests; no field rate | Data owner |
| Duplicate result rate | Repeated source URLs / all result positions | 0 | Deduplication test; no field rate | Retrieval maintainer |
| Reviewer agreement | Matching independent human labels / dual-reviewed labels | Establish per-use-case baseline | Not measured | Domain expert |

## Runtime and economic KPIs

| KPI | Definition | Target or reporting rule | Current status |
|---|---|---|---|
| Compute latency p95 | Nearest-rank 95th percentile of end-to-end compute seconds, excluding human wait | ≤30 seconds for the proposed pilot scope | The bundled timing measures retrieval+verification only; not end-to-end |
| Mean iterations | Total executed analysis passes / cases | ≤2 default; maximum 3 configurable | Workflow demonstrates two passes; component metric records one verification pass |
| Model calls | Count dispatched per case and total | 0 in shipped demo | Zero by construction; no model integration |
| Tokens | Observed provider input+output tokens | 0 in shipped demo | Zero by construction; no metering claim for a future provider |
| Cost per case | Recorded provider cost / cases | 0 in shipped demo | Excludes host CPU, engineering, and human time |
| Budget breaches | Dispatches exceeding reserved call/token/cost budget | 0 | Only local loop/context checks implemented; future model budget reservation not implemented |
| Approval lead time | Decision timestamp minus review-request timestamp | Measure p50/p95; agree human SLA separately | Not measured |
| Consent-revocation latency | Last permitted access minus effective revocation time | Recheck at every boundary; no later access | Local regression tests; distributed latency unmeasured |
| Recovery time / data loss | Recovery duration / lost acknowledged records after failure | Set only after durable infrastructure exists | Not implemented; memory checkpoints disappear at exit |

`contributor_agent.metrics.compute_kpis` validates types, finite numbers, unique IDs and denominators. It does not establish whether evaluator labels are truthful or representative. Independent grouping must be curated and audited outside the process. Do not feed a model's self-reported success into release gates as ground truth.

## Release decision

`assess_candidate` requires independent holdout mode, minimum sample counts, all zero-tolerance observations, quality thresholds, no regression, bounded latency and human release review. It rejects weakened safety configuration. A passing result is only `ready_for_human_release_review`; the function cannot publish, deploy or alter consent.

The public OSS code can be released as an experimental reference while the **production-use gate remains blocked**. These are separate decisions.

Run:

```sh
python scripts/evaluate.py
```

Read `evidence/evaluation.json`, `evidence/kpi-cases.json`, and the explicit `measurement_scope`. The nine examples are synthetic and use source quotes as retrieval queries, making them easy plumbing checks; they cannot demonstrate real question-answering accuracy or justify a regulatory use case.

## Statistical interpretation

Zero observed failures is not a zero error margin. Under independent representative sampling, the rough 95% upper bound after zero failures is 3/n. Correlated cases, changing sources, model drift and distribution shift invalidate simplistic extrapolation. No fixed sample size alone certifies a high-consequence application. For governance context, see [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework).

## Adoption and documentation KPIs

Track voluntarily supplied aggregate measures: successful fresh-install reproductions / attempted reproductions; accepted external bug fixes; time to reproduce a report; and documentation task completion. Website search impressions, query clicks and click-through rate require authorized site analytics. GitHub stars, forks and clone counts are adoption signals, not quality evidence. No analytics or automatic outreach is embedded in the package.
