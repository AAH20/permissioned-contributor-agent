"""Purpose-isolated synthetic diligence workflow with actual LangGraph and DD graph/guard."""
from dataclasses import dataclass, asdict
from hashlib import sha256
import json
import math
import time
import re
from .core import Denied
from ._vendor.dd.graph import DealKnowledgeGraph, GraphEdge, EdgeType
from ._vendor.dd.quote_guard import quote_salience_mismatches

DOMAINS=('legal','finance','commercial','producttech','cybersecurity','hr','tax','regulatory','esg')
PURPOSE='synthetic_due_diligence'

@dataclass(frozen=True)
class RoomGrant:
    tenant: str
    member: str
    room: str
    expires_at: float
    documents: tuple[str,...]
    purpose: str = PURPOSE
    revoked: bool = False
    def check(self,tenant,member,room,now):
        if (tenant,member,room)!=(self.tenant,self.member,self.room): raise Denied('room_identity_mismatch')
        if type(self.expires_at) not in (int,float) or not math.isfinite(self.expires_at) or self.purpose!=PURPOSE or self.revoked or now>=self.expires_at: raise Denied('room_consent_inactive')
    def digest(self):
        return sha256(json.dumps(asdict(self),sort_keys=True).encode()).hexdigest()

@dataclass(frozen=True)
class LoopParameters:
    max_iterations: int=2
    max_seconds: float=30
    top_k: int=3
    max_context_chars: int=12000
    graph_hops: int=1
    max_model_calls: int=0
    max_external_writes: int=0
    def validate(self):
        counts=(self.max_iterations,self.top_k,self.max_context_chars,self.graph_hops,
                self.max_model_calls,self.max_external_writes)
        if any(type(v) is not int for v in counts):raise Denied('invalid_loop_parameter_type')
        if type(self.max_seconds) not in (int,float) or not math.isfinite(self.max_seconds):
            raise Denied('invalid_time_budget')
        if not (1<=self.max_iterations<=3 and 0<self.max_seconds<=60 and 1<=self.top_k<=5 and
                100<=self.max_context_chars<=20000 and self.graph_hops in (0,1) and
                self.max_model_calls==0 and self.max_external_writes==0):
            raise Denied('unsafe_loop_parameters')

class DiligenceRoom:
    def __init__(self,grant,documents,clock=time.time):
        self.grant,self.clock=grant,clock
        self.documents={}
        self.graph=DealKnowledgeGraph()
        self.nodes={}
        self.check(grant.tenant,grant.member)
        # Reject mismatched records before indexing; never create a mixed-tenant graph.
        for d in documents:
            if (d['tenant'],d['room'])!=(grant.tenant,grant.room) or d['id'] not in grant.documents:
                raise Denied('document_scope_mismatch')
            if d['id'] in self.documents: raise Denied('duplicate_document')
            self.documents[d['id']]=dict(d)
            self.nodes[d['id']]=self.graph.add_document(d['id'],'synthetic',tenant=grant.tenant,room=grant.room)
        for d in self.documents.values():
            for target in d.get('references',[]):
                if target in self.nodes:
                    self.graph.add_edge(GraphEdge(source_id=self.nodes[d['id']],target_id=self.nodes[target],edge_type=EdgeType.REFERENCES))
        self.check(grant.tenant,grant.member)
    def check(self,tenant,member):
        self.grant.check(tenant,member,self.grant.room,self.clock())
    def retrieve(self,tenant,member,query,params):
        self.check(tenant,member);params.validate()
        words=set(re.findall(r'\w+',query.lower()))
        scored=[]
        for d in self.documents.values():
            score=len(words & set(re.findall(r'\w+',d['text'].lower())))
            if score: scored.append((score,d['id']))
        ids=[i for _,i in sorted(scored,key=lambda x:(-x[0],x[1]))[:params.top_k]]
        if params.graph_hops:
            # References are curated synthetic graph edges, never inferred by an LLM.
            for i in tuple(ids):
                reverse={v:k for k,v in self.nodes.items()}
                for edge in self.graph.get_edges(self.nodes[i],EdgeType.REFERENCES):
                    target=reverse.get(edge.target_id)
                    if target in self.documents and target not in ids and len(ids)<params.top_k:
                        ids.append(target)
        context=[dict(self.documents[i]) for i in ids]
        if sum(len(d['text']) for d in context)>params.max_context_chars:
            raise Denied('retrieved_context_budget')
        return context
    def verify(self,tenant,member,finding):
        self.check(tenant,member)
        d=self.documents.get(finding['document'])
        if not d: return False,'missing_or_unauthorized_evidence'
        quote=finding['quote']
        if not quote or quote not in d['text']: return False,'not_exact_quote'
        mismatch=quote_salience_mismatches(quote,d['text'])
        if mismatch: return False,'salience_mismatch'
        return True,'exact_source_quote'
    def pinecone_query(self,tenant,member,index,vector,top_k=3):
        # Adapter contract only. Never sends text; no default index or credentials.
        self.check(tenant,member)
        if not 1<=top_k<=5: raise Denied('query_budget')
        namespace=sha256(f'{tenant}:{self.grant.room}:{self.grant.purpose}:{self.grant.digest()}'.encode()).hexdigest()
        result=index.query(namespace=namespace,vector=vector,top_k=top_k,include_metadata=True,
                           filter={'document_id':{'$in':list(self.grant.documents)}})
        self.check(tenant,member)
        return [m for m in result.get('matches',[]) if m.get('metadata',{}).get('document_id') in self.grant.documents]

class DiligenceWorkflow:
    """No external effects. Specialist outputs are fixtures, not live LLM analysis."""
    def __init__(self,room,params=LoopParameters()):
        from langgraph.graph import StateGraph, START, END
        from langgraph.checkpoint.memory import InMemorySaver
        from langgraph.types import interrupt
        self.room,self.params=room,params
        params.validate()
        self.started={}
        self.used=set()
        self.replays={}
        self.grants={}
        def analyze(state):
            room.check(state['tenant'],state['member'])
            start=self.started[state['run_id']]
            if room.clock()-start>params.max_seconds: raise Denied('time_budget_exhausted')
            iteration=state.get('iteration',0)+1
            outputs=self.replays[state['run_id']]
            findings=outputs[min(iteration-1,len(outputs)-1)]
            accepted,rejected=[],[]
            for f in findings:
                room.check(state['tenant'],state['member'])
                if room.clock()-start>params.max_seconds:raise Denied('time_budget_exhausted')
                if f['domain'] not in DOMAINS: raise Denied('unknown_specialist')
                context=room.retrieve(state['tenant'],state['member'],f['quote'],params)
                valid,reason=room.verify(state['tenant'],state['member'],f)
                if f['document'] not in {d['id'] for d in context}: valid,reason=False,'not_retrieved'
                (accepted if valid else rejected).append(dict(f,validation=reason))
            covered={f['domain'] for f in accepted}
            return dict(state,iteration=iteration,accepted=accepted,rejected=rejected,
                        missing_domains=sorted(set(DOMAINS)-covered))
        def route(state):
            if (state['rejected'] or state['missing_domains']) and state['iteration']<params.max_iterations:return 'analyze'
            if state['rejected'] or state['missing_domains']:return 'abstain'
            return 'review'
        def abstain(state):return dict(state,status='abstained',external_writes=0)
        def review(state):
            room.check(state['tenant'],state['member'])
            payload=sha256(json.dumps(state['accepted'],sort_keys=True).encode()).hexdigest()
            decision=interrupt({'run_id':state['run_id'],'payload_digest':payload,'findings':state['accepted'],
                                'notice':'SYNTHETIC replay. Human assessment required. No external effects.'})
            room.check(state['tenant'],state['member'])
            if decision.get('payload_digest')!=payload or decision.get('grant_digest')!=room.grant.digest():
                raise Denied('approval_binding_mismatch')
            return dict(state,status='reviewed_synthetic' if decision.get('approve') is True else 'rejected',external_writes=0)
        g=StateGraph(dict)
        for name,fn in [('analyze',analyze),('abstain',abstain),('review',review)]:g.add_node(name,fn)
        g.add_edge(START,'analyze');g.add_conditional_edges('analyze',route)
        g.add_edge('abstain',END);g.add_edge('review',END)
        self.graph=g.compile(checkpointer=InMemorySaver())
    def start(self,tenant,member,run_id,replay):
        self.room.check(tenant,member)
        if run_id in self.started or not replay: raise Denied('duplicate_or_empty_run')
        if len(replay)>self.params.max_iterations or any(len(batch)>18 for batch in replay):raise Denied('replay_budget')
        if any(len(json.dumps(batch))>self.params.max_context_chars for batch in replay):raise Denied('context_budget')
        self.started[run_id]=self.room.clock();self.replays[run_id]=json.loads(json.dumps(replay,allow_nan=False))
        self.grants[run_id]=self.room.grant.digest()
        return self.graph.invoke({'tenant':tenant,'member':member,'run_id':run_id},self.config(tenant,member,run_id))
    def config(self,tenant,member,run_id):
        return {'configurable':{'thread_id':sha256(f'{tenant}:{member}:{self.room.grant.room}:{run_id}'.encode()).hexdigest()},'recursion_limit':16}
    def resume(self,tenant,member,run_id,payload_digest,approve):
        from langgraph.types import Command
        self.room.check(tenant,member)
        if run_id in self.used or run_id not in self.started:raise Denied('approval_replay_or_unknown')
        if self.room.clock()-self.started[run_id]>3600:raise Denied('approval_expired')
        if self.grants[run_id]!=self.room.grant.digest():raise Denied('grant_changed')
        self.used.add(run_id)
        return self.graph.invoke(Command(resume={'approve':approve,'payload_digest':payload_digest,
            'grant_digest':self.room.grant.digest()}),self.config(tenant,member,run_id))
