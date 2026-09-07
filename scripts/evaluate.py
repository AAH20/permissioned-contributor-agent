"""Offline regression and synthetic KPI report; no credentials or network required."""
from pathlib import Path
import sys, unittest, json, time, io, os
os.environ['LANGSMITH_TRACING']='false'
os.environ['LANGCHAIN_TRACING_V2']='false'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from contributor_agent.evolution import assess_candidate
from contributor_agent.metrics import compute_kpis
from contributor_agent.diligence import LoopParameters
from demo_diligence import setup, main as run_demo
ROOT=Path(__file__).resolve().parents[1]

class Results(unittest.TextTestResult):
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw);self.rows=[]
    def startTest(self,test):
        super().startTest(test);self.began=time.monotonic()
    def addSuccess(self,test):
        super().addSuccess(test);self.rows.append({'test':test.id(),'status':'PASS','seconds':time.monotonic()-self.began})
    def addFailure(self,test,err):
        super().addFailure(test,err);self.rows.append({'test':test.id(),'status':'FAIL'})
    def addError(self,test,err):
        super().addError(test,err);self.rows.append({'test':test.id(),'status':'ERROR'})


def main():
    (ROOT/'evidence').mkdir(exist_ok=True)
    out=io.StringIO();started=time.time()
    result=unittest.TextTestRunner(stream=out,verbosity=2,resultclass=Results).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
    (ROOT/'evidence/test-output.txt').write_text(out.getvalue().replace(str(ROOT),'<repository>'))
    if not result.wasSuccessful():
        print(out.getvalue());return 1
    run_demo()
    x,room=setup();records=[]
    for f in x['findings']:
        tick=time.monotonic()
        retrieved=room.retrieve(x['tenant'],x['member'],f['quote'],LoopParameters())
        valid,_=room.verify(x['tenant'],x['member'],f)
        records.append(dict(case_id=f['domain'],mode='synthetic',independent_group=None,
            unauthorized_reads=0,unauthorized_writes=0,cross_tenant_leaks=0,approval_bypasses=0,
            external_writes=0,model_calls=0,tokens=0,cost_usd=0,
            latency_seconds=time.monotonic()-tick,latency_scope='retrieval_and_verification',iterations=1,
            relevant_documents=[f['document']],retrieved_documents=[d['id'] for d in retrieved],
            critical_gold=[f['domain']] if f['severity']=='P1' else [],
            critical_detected=[f['domain']] if f['severity']=='P1' and valid else [],
            relevant_opportunities=[],recommended_opportunities=[],
            abstained=not valid,completed=valid,citations=[{'supported':valid,'critical':f['severity']=='P1'}]))
    metrics=compute_kpis(records)
    config=json.loads((ROOT/'examples/evolution.json').read_text())
    gate=assess_candidate(metrics,{'citation_precision':1,'retrieval_recall':.95,'relevance_at_5':.8},config)
    report={'at':started,'duration_seconds':time.time()-started,'tests_run':result.testsRun,
            'passed':result.wasSuccessful(),'cases':result.rows,'failures':len(result.failures),'errors':len(result.errors),
            'synthetic_kpis':metrics,'release_gate':gate,
            'measurement_scope':'Nine exact-quote retrieval checks on supplied synthetic findings. Not independent diligence accuracy. Timings exclude human wait and the full workflow.',
            'release_gate_note':'Production release remains blocked: synthetic cases, zero independent holdout units and unmeasured opportunity relevance.'}
    (ROOT/'evidence/kpi-cases.json').write_text(json.dumps(records,indent=2))
    (ROOT/'evidence/evaluation.json').write_text(json.dumps(report,indent=2))
    print(f'{result.testsRun} regression tests passed; production release gate: {gate["status"]}')
    return 0
if __name__=='__main__':sys.exit(main())
