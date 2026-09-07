from pathlib import Path
import sys,json,time
from dataclasses import asdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from contributor_agent.diligence import RoomGrant,DiligenceRoom,DiligenceWorkflow,LoopParameters
ROOT=Path(__file__).resolve().parents[1]
def setup():
 x=json.loads((ROOT/'examples/diligence-room.json').read_text())
 grant=RoomGrant(x['tenant'],x['member'],x['room'],time.time()+3600,tuple(d['id'] for d in x['documents']))
 docs=[dict(d,tenant=x['tenant'],room=x['room']) for d in x['documents']]
 return x,DiligenceRoom(grant,docs)
def main():
 x,room=setup();wf=DiligenceWorkflow(room)
 # One bad number demonstrates rejection and a bounded second-pass repair.
 bad=[dict(f) for f in x['findings']];bad[0]['quote']='Termination requires 30 days notice.'
 state=wf.start(x['tenant'],x['member'],'synthetic-demo',[bad,x['findings']])
 review=state['__interrupt__'][0].value
 result={'mode':'SYNTHETIC_SPECIALIST_REPLAY_REAL_LANGGRAPH', 'upstream':'AAH20/A2Z_due-diligence-agents',
         'upstream_commit':'6aeabb4046e04f2979571fbb536fa43614d8c2db','parameters':asdict(LoopParameters()),
         'iterations':state['iteration'],'domains':len(state['accepted']),'findings':state['accepted'],
         'review':review,'status':'pending_human_review','graph':room.graph.to_serializable(),
         'graph_context':room.graph.get_document_context('msa'),
         'retrieval_demo':room.retrieve(x['tenant'],x['member'],'Annual service fees',LoopParameters()),
         'llm_calls':0,'pinecone_calls':0,'external_writes':0,
         'limitation':'Nine supplied findings replay specialist roles; no model-generated diligence or compliance verdict.'}
 (ROOT/'evidence/diligence-demo.json').write_text(json.dumps(result,indent=2,default=str))
 print(json.dumps({k:result[k] for k in ['mode','iterations','domains','status','llm_calls','pinecone_calls','external_writes']},indent=2))
if __name__=='__main__':main()
