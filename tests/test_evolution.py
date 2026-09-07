import json,unittest
from pathlib import Path
from contributor_agent.evolution import assess_candidate
class EvolutionEvaluation(unittest.TestCase):
 def setUp(self):
  self.c=json.loads((Path(__file__).resolve().parents[1]/'examples/evolution.json').read_text())
  self.m=dict(latency_scope='end_to_end_compute',mode='independent_holdout',approval_bypasses=0,independent_cases=200,critical_cases=50,critical_false_negatives=0,unauthorized_reads=0,unauthorized_writes=0,cross_tenant_leaks=0,unsupported_critical_claims=0,citation_precision=1,retrieval_recall=.98,relevance_at_5=.9,p95_seconds=1)
  self.b=dict(citation_precision=1,retrieval_recall=.95,relevance_at_5=.8)
 def test_never_auto_promotes(self):
  r=assess_candidate(self.m,self.b,self.c);self.assertEqual(r['status'],'ready_for_human_release_review');self.assertFalse(r['auto_promote'])
 def test_any_critical_failure_blocks(self):
  self.m['critical_false_negatives']=1;self.assertEqual(assess_candidate(self.m,self.b,self.c)['status'],'blocked')
 def test_unknown_nan_and_small_samples_block(self):
  for v in [None,float('nan'),-1,12]:
   self.m['independent_cases']=v;self.assertEqual(assess_candidate(self.m,self.b,self.c)['status'],'blocked')
 def test_quality_regression_blocks(self):
  self.b['retrieval_recall']=.99;self.assertEqual(assess_candidate(self.m,self.b,self.c)['status'],'blocked')

 def test_synthetic_metrics_cannot_release(self):
  self.m['mode']='synthetic_or_mixed';self.assertEqual(assess_candidate(self.m,self.b,self.c)['status'],'blocked')
 def test_config_cannot_weaken_hard_gates(self):
  self.c['promotion']['human_release_approval_required']=False
  self.assertEqual(assess_candidate(self.m,self.b,self.c)['status'],'blocked')
 def test_parameter_proposals_never_apply(self):
  from contributor_agent.evolution import assess_parameter_proposal
  self.assertEqual(assess_parameter_proposal({}, {'top_k':4})['status'],'offline_evaluation_required')
  self.assertFalse(assess_parameter_proposal({}, {'top_k':4})['applied'])
  self.assertEqual(assess_parameter_proposal({}, {'tenant_scope':'other'})['status'],'rejected')

 def test_component_latency_cannot_satisfy_release(self):
  self.m['latency_scope']='retrieval_and_verification'
  self.assertEqual(assess_candidate(self.m,self.b,self.c)['status'],'blocked')
