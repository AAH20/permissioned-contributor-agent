import unittest
from contributor_agent.metrics import compute_kpis


def case(**changes):
    r = dict(case_id='one', mode='synthetic', independent_group=None,
             unauthorized_reads=0, unauthorized_writes=0, cross_tenant_leaks=0,
             approval_bypasses=0, external_writes=0, model_calls=0, tokens=0,
             latency_scope='retrieval_and_verification',latency_seconds=1.2, cost_usd=0, iterations=2,
             relevant_documents=['a','b'], retrieved_documents=['a','x'],
             critical_gold=['risk'], critical_detected=[],
             relevant_opportunities=['o1','o2'], recommended_opportunities=['o1'],
             abstained=True, completed=False, citations=[{'supported':True,'critical':False}])
    r.update(changes)
    return r


class MetricEvaluation(unittest.TestCase):
    def test_measured_denominators(self):
        m=compute_kpis([case()])
        self.assertEqual(m['retrieval_recall'],.5)
        self.assertEqual(m['relevance_at_5'],.2)
        self.assertEqual(m['critical_false_negatives'],1)
        self.assertEqual(m['independent_cases'],0)
    def test_empty_is_not_perfect(self):
        m=compute_kpis([])
        self.assertIsNone(m['citation_precision'])
        self.assertIsNone(m['unauthorized_reads'])
    def test_duplicate_and_nonfinite_rejected(self):
        for records in [[case(),case()],[case(latency_seconds=float('nan'))],[case(tokens=-1)]]:
            with self.assertRaises(ValueError):compute_kpis(records)
    def test_zero_denominator_is_null(self):
        m=compute_kpis([case(citations=[],relevant_documents=[],relevant_opportunities=[])])
        self.assertIsNone(m['citation_precision'])
        self.assertIsNone(m['retrieval_recall'])
        self.assertIsNone(m['relevance_at_5'])
    def test_independent_units_deduplicated(self):
        m=compute_kpis([case(mode='independent_holdout',independent_group='family1'),
                        case(case_id='two',mode='independent_holdout',independent_group='family1')])
        self.assertEqual(m['independent_cases'],1)
        self.assertEqual(m['critical_cases'],1)
