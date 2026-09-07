import unittest,json,time
from pathlib import Path
from dataclasses import replace
from contributor_agent.core import Denied
from contributor_agent.diligence import RoomGrant,DiligenceRoom,DiligenceWorkflow,LoopParameters
ROOT=Path(__file__).resolve().parents[1]
class DiligenceEvaluation(unittest.TestCase):
 def setUp(self):
  self.x=json.loads((ROOT/'examples/diligence-room.json').read_text())
  self.g=RoomGrant('synthetic-bank','synthetic-reviewer','aster-renewal',2000,tuple(d['id'] for d in self.x['documents']))
  self.docs=[dict(d,tenant=self.g.tenant,room=self.g.room) for d in self.x['documents']]
  self.r=DiligenceRoom(self.g,self.docs,lambda:1000)
 def workflow(self,replay):
  w=DiligenceWorkflow(self.r);s=w.start(self.g.tenant,self.g.member,'r1',replay);return w,s
 def test_nine_domain_human_interrupt(self):
  w,s=self.workflow([self.x['findings']]);self.assertIn('__interrupt__',s);self.assertEqual(len(s['accepted']),9)
 def test_actual_upstream_graph(self):
  self.assertGreater(len(self.r.graph.to_serializable()['edges']),0)
  self.assertIn('msa',self.r.graph.get_document_context('msa'))
 def test_quote_fabrication(self):
  f=dict(self.x['findings'][0],quote='Termination requires 30 days notice.')
  self.assertFalse(self.r.verify(self.g.tenant,self.g.member,f)[0])
 def test_bounded_repair(self):
  bad=[dict(f) for f in self.x['findings']];bad[0]['quote']='Forged 30 days'
  w,s=self.workflow([bad,self.x['findings']]);self.assertEqual(s['iteration'],2);self.assertIn('__interrupt__',s)
 def test_missing_domain_abstains(self):
  w,s=self.workflow([self.x['findings'][:-1]]);self.assertEqual(s['status'],'abstained');self.assertEqual(s['iteration'],2)
 def test_cross_tenant_before_graph(self):
  with self.assertRaises(Denied):DiligenceRoom(self.g,[dict(self.docs[0],tenant='other')],lambda:1000)
 def test_cross_member_retrieval(self):
  with self.assertRaises(Denied):self.r.retrieve(self.g.tenant,'other','fees',LoopParameters())
 def test_revocation_before_resume(self):
  w,s=self.workflow([self.x['findings']]);self.r.grant=replace(self.g,revoked=True)
  with self.assertRaises(Denied):w.resume(self.g.tenant,self.g.member,'r1',s['__interrupt__'][0].value['payload_digest'],True)
 def test_approval_replay(self):
  w,s=self.workflow([self.x['findings']]);digest=s['__interrupt__'][0].value['payload_digest']
  final=w.resume(self.g.tenant,self.g.member,'r1',digest,True);self.assertEqual(final['external_writes'],0)
  with self.assertRaises(Denied):w.resume(self.g.tenant,self.g.member,'r1',digest,True)
 def test_tampered_approval(self):
  w,s=self.workflow([self.x['findings']])
  with self.assertRaises(Denied):w.resume(self.g.tenant,self.g.member,'r1','tampered',True)
 def test_unsafe_loop(self):
  for p in [LoopParameters(max_iterations=99),LoopParameters(max_model_calls=1),LoopParameters(max_external_writes=1)]:
   with self.assertRaises(Denied):DiligenceWorkflow(self.r,p)
 def test_time_budget(self):
  w=DiligenceWorkflow(self.r);ticks=iter([1000,1000,1000,1100,1100,1100]);self.r.clock=lambda:next(ticks,1100)
  with self.assertRaises(Denied):w.start(self.g.tenant,self.g.member,'r1',[self.x['findings']])
 def test_pinecone_contract_scope(self):
  class Index:
   def query(s,**kwargs):
    s.kwargs=kwargs;return {'matches':[{'metadata':{'document_id':'msa'}},{'metadata':{'document_id':'forbidden'}}]}
  i=Index();matches=self.r.pinecone_query(self.g.tenant,self.g.member,i,[0.1,0.2])
  self.assertEqual(len(matches),1);self.assertEqual(len(i.kwargs['namespace']),64)
  self.assertIn('document_id',i.kwargs['filter'])
 def test_pinecone_no_call_when_revoked(self):
  self.r.grant=replace(self.g,revoked=True)
  with self.assertRaises(Denied):self.r.pinecone_query(self.g.tenant,self.g.member,None,[0.1])

 def test_changed_grant_invalidates_review(self):
  w,s=self.workflow([self.x['findings']]);self.r.grant=replace(self.g,expires_at=2500)
  with self.assertRaises(Denied):w.resume(self.g.tenant,self.g.member,'r1',s['__interrupt__'][0].value['payload_digest'],True)
 def test_foreign_reference_never_expands(self):
  self.docs[0]['references']=['foreign-private-document']
  r=DiligenceRoom(self.g,self.docs,lambda:1000)
  self.assertNotIn('foreign-private-document',json.dumps(r.graph.to_serializable()))

 def test_nonfinite_room_consent_denied(self):
  for value in [float('nan'),float('inf')]:
   with self.assertRaises(Denied):DiligenceRoom(replace(self.g,expires_at=value),self.docs,lambda:1000)

 def test_expired_consent_before_document_iteration(self):
  class Documents:
   def __iter__(s):raise AssertionError('documents touched without active consent')
  with self.assertRaises(Denied):DiligenceRoom(replace(self.g,expires_at=999),Documents(),lambda:1000)
 def test_retrieved_context_budget(self):
  self.docs[0]['text']='fees ' * 300
  r=DiligenceRoom(self.g,self.docs,lambda:1000)
  with self.assertRaises(Denied):r.retrieve(self.g.tenant,self.g.member,'fees',LoopParameters(max_context_chars=100))

 def test_fractional_and_boolean_loop_counts_rejected(self):
  for p in [LoopParameters(top_k=1.5),LoopParameters(max_iterations=True)]:
   with self.assertRaises(Denied):p.validate()
