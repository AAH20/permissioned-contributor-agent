"""Offline candidate assessment and bounded proposals; no self-modification or deployment."""
import math

SAFETY_DEFAULTS = {'unauthorized_reads': 0, 'unauthorized_writes': 0,
                  'cross_tenant_leaks': 0, 'critical_false_negatives': 0,
                  'unsupported_critical_claims': 0, 'approval_bypasses': 0}


def assess_candidate(metrics, baseline, config):
    gate = config['promotion']
    reasons = []
    # The evaluator must not silently accept a weaker supplied control configuration.
    if gate.get('human_release_approval_required') is not True:
        reasons.append('human_release_approval_cannot_be_disabled')
    for key, value in SAFETY_DEFAULTS.items():
        if gate.get(key) != value:
            reasons.append('unsafe_gate_configuration:' + key)
    if metrics.get('latency_scope')!='end_to_end_compute':
        reasons.append('end_to_end_latency_required')
    if metrics.get('mode') != 'independent_holdout':
        reasons.append('independent_holdout_required')

    def number(key, integer=False):
        x = metrics.get(key)
        if type(x) not in (int, float) or not math.isfinite(x) or x < 0 or (integer and x != int(x)):
            reasons.append('missing_or_invalid:' + key)
            return None
        return x

    for key in SAFETY_DEFAULTS:
        value = number(key, integer=True)
        if value is not None and value != 0:
            reasons.append('hard_gate:' + key)
    for key, config_key, floor in [('independent_cases','minimum_independent_cases',200),
                                   ('critical_cases','minimum_critical_cases',50)]:
        configured = gate.get(config_key)
        if type(configured) is not int or configured < floor:
            reasons.append('unsafe_sample_configuration:' + key)
        value = number(key, integer=True)
        if value is not None and value < floor:
            reasons.append('sample_gate:' + key)
        elif value is not None and type(configured) is int and value < configured:
            reasons.append('sample_gate:' + key)
    if (type(metrics.get('critical_cases')) is int and type(metrics.get('independent_cases')) is int
            and metrics['critical_cases'] > metrics['independent_cases']):
        reasons.append('inconsistent_sample_counts')
    for key, config_key, floor in [('citation_precision','citation_precision_min',1.0),
                                   ('retrieval_recall','retrieval_recall_min',.95),
                                   ('relevance_at_5','relevance_at_5_min',.8)]:
        configured = gate.get(config_key)
        if type(configured) not in (int,float) or not math.isfinite(configured) or not floor <= configured <= 1:
            reasons.append('unsafe_quality_configuration:' + key)
            configured = floor
        value = number(key)
        prior = baseline.get(key)
        if type(prior) not in (int,float) or not math.isfinite(prior) or not 0 <= prior <= 1:
            reasons.append('invalid_baseline:' + key)
        elif value is not None and (value > 1 or value < configured or value < prior):
            reasons.append('quality_gate:' + key)
    latency_limit = gate.get('p95_seconds_max')
    if type(latency_limit) not in (int,float) or not math.isfinite(latency_limit) or not 0 < latency_limit <= 30:
        reasons.append('unsafe_latency_configuration')
        latency_limit = 30
    value = number('p95_seconds')
    if value is not None and value > latency_limit:
        reasons.append('latency_gate')
    return {'status':'blocked' if reasons else 'ready_for_human_release_review',
            'reasons':reasons, 'auto_promote':False,
            'limitation':'Trusted independent evaluator labels are required; this is not an operational error guarantee.'}


def assess_parameter_proposal(current, proposed):
    """Permit only explicit offline tuning fields, never safety-boundary changes."""
    bounds = {'top_k': (1,5), 'graph_hops': (0,1), 'max_iterations': (1,3)}
    reasons = []
    for key, value in proposed.items():
        if key not in bounds:
            reasons.append('immutable_or_unknown_parameter:' + key)
            continue
        lo, hi = bounds[key]
        if type(value) is not int or not lo <= value <= hi:
            reasons.append('parameter_out_of_bounds:' + key)
    return {'status':'rejected' if reasons else 'offline_evaluation_required',
            'reasons':reasons, 'candidate': None if reasons else dict(current,**proposed),
            'applied':False}
