"""Compute KPIs from explicit case records; never turn missing evidence into zero."""
import math
from statistics import mean

COUNTERS = ('unauthorized_reads', 'unauthorized_writes', 'cross_tenant_leaks',
            'approval_bypasses', 'external_writes', 'model_calls', 'tokens')


def _number(value, field, integer=False):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError('invalid metric: ' + field)
    if integer and value != int(value):
        raise ValueError('noninteger count: ' + field)
    return value


def _ids(values, field):
    if not isinstance(values, list) or any(not isinstance(v, str) or not v for v in values):
        raise ValueError('invalid IDs: ' + field)
    if len(values) != len(set(values)):
        raise ValueError('duplicate IDs: ' + field)
    return set(values)


def compute_kpis(records):
    """Trusted evaluator labels are required. Counts do not authenticate their producer.

    A case's independent_group must identify an adjudicated, disjoint holdout unit;
    synthetic records never contribute to independent_cases or critical_cases.
    """
    seen = set()
    for r in records:
        if not isinstance(r.get('case_id'), str) or not r['case_id'] or r['case_id'] in seen:
            raise ValueError('missing or duplicate case_id')
        seen.add(r['case_id'])
        if r.get('mode') not in ('synthetic', 'independent_holdout'):
            raise ValueError('unknown evidence mode')
        if r.get('mode') == 'independent_holdout' and not r.get('independent_group'):
            raise ValueError('missing independent group')
        if r.get('latency_scope') not in ('retrieval_and_verification','end_to_end_compute'):
            raise ValueError('unknown latency scope')
        for key in COUNTERS:
            _number(r[key], key, integer=True)
        for key in ('latency_seconds', 'cost_usd'):
            _number(r[key], key)
        _number(r['iterations'], 'iterations', integer=True)
        for key in ('relevant_documents', 'retrieved_documents', 'critical_gold', 'critical_detected',
                    'relevant_opportunities', 'recommended_opportunities'):
            _ids(r[key], key)
        if type(r['abstained']) is not bool or type(r['completed']) is not bool:
            raise ValueError('invalid outcome')
        for c in r['citations']:
            if type(c['supported']) is not bool or type(c['critical']) is not bool:
                raise ValueError('invalid citation label')
    if not records:
        return {'case_count': 0, 'independent_cases': 0, 'critical_cases': 0,
                'mode': 'not_measured', **{k: None for k in COUNTERS},
                **{k: None for k in ('citation_precision', 'retrieval_recall', 'relevance_at_5',
                    'critical_false_negatives', 'unsupported_critical_claims', 'p95_seconds',
                    'abstention_rate', 'completion_rate', 'mean_iterations', 'cost_per_case_usd')}}
    citations = [c for r in records for c in r['citations']]
    relevant = sum(len(r['relevant_documents']) for r in records)
    retrieved_relevant = sum(len(set(r['relevant_documents']) & set(r['retrieved_documents'])) for r in records)
    opportunities = [r for r in records if r['relevant_opportunities']]
    latencies = sorted(r['latency_seconds'] for r in records)
    holdout = [r for r in records if r['mode'] == 'independent_holdout']
    return {
        'mode': 'independent_holdout' if len(holdout) == len(records) else 'synthetic_or_mixed',
        'case_count': len(records),
        'latency_scope': records[0]['latency_scope'] if len({r['latency_scope'] for r in records})==1 else 'mixed',
        'independent_cases': len({r['independent_group'] for r in holdout}),
        'critical_cases': len({r['independent_group'] for r in holdout if r['critical_gold']}),
        **{key: sum(r[key] for r in records) for key in COUNTERS},
        'critical_false_negatives': sum(len(set(r['critical_gold']) - set(r['critical_detected'])) for r in records),
        'unsupported_critical_claims': sum(c['critical'] and not c['supported'] for c in citations),
        'citation_precision': sum(c['supported'] for c in citations) / len(citations) if citations else None,
        'retrieval_recall': retrieved_relevant / relevant if relevant else None,
        # Standard P@5: absent result positions count as misses. Empty-gold queries excluded.
        'relevance_at_5': mean(len(set(r['recommended_opportunities'][:5]) & set(r['relevant_opportunities'])) / 5
                               for r in opportunities) if opportunities else None,
        'p95_seconds': latencies[math.ceil(.95 * len(latencies)) - 1],
        'abstention_rate': mean(r['abstained'] for r in records),
        'completion_rate': mean(r['completed'] for r in records),
        'mean_iterations': mean(r['iterations'] for r in records),
        'cost_per_case_usd': mean(r['cost_usd'] for r in records),
    }
