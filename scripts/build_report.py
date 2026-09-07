"""Generate a public synthetic report; includes no session or commercial data."""
from pathlib import Path
from html import escape
import json
ROOT=Path(__file__).resolve().parents[1]
def main():
    evaluation=json.loads((ROOT/'evidence/evaluation.json').read_text())
    demo=json.loads((ROOT/'evidence/diligence-demo.json').read_text())
    k=evaluation['synthetic_kpis']
    rows=''.join('<tr><td>'+escape(f['domain'])+'</td><td>'+escape(f['quote'])+'</td><td>Source verified</td></tr>' for f in demo['findings'])
    doc=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AI Agent Governance &amp; Evaluation — Synthetic Evidence</title><style>
body{{margin:0;background:#0d1625;color:#e3eefc;font:16px system-ui,sans-serif}}main{{max-width:1320px;margin:auto;padding:40px}}.eyebrow{{color:#70dbc4;letter-spacing:2px;font-size:12px}}h1{{font-size:34px;margin:12px 0}}p{{color:#b1c3da;line-height:1.7}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin:28px 0}}.card{{background:#16263c;border:1px solid #304867;padding:22px;border-radius:10px}}strong{{display:block;font-size:32px;margin-top:10px}}small{{color:#b5c6da}}.note{{background:#342d20;border:1px solid #806d3b;color:#efd197;border-radius:8px;padding:18px;line-height:1.6}}table{{width:100%;border-collapse:collapse;margin-top:22px;font-size:14px}}td,th{{padding:15px;border-bottom:1px solid #30415a;text-align:left}}th{{background:#1b2c43;color:#a7c0db}}td{{background:#122034}}.flow{{padding:20px;margin:22px 0;border:1px solid #345d69;border-radius:8px;color:#8de0d0}}a{{color:#78dfcb}}footer{{font-size:12px;color:#8ca6c1;margin-top:28px}}@media(max-width:700px){{main{{padding:20px}}.cards{{grid-template-columns:repeat(2,1fr)}}}}</style><main>
<div class="eyebrow">OPEN-SOURCE REFERENCE · SYNTHETIC EVIDENCE</div><h1>AI Agent Governance &amp; Evaluation</h1><p>Permissioned Contributor Agent · LangGraph · Human-in-the-loop review · Graph-assisted retrieval</p>
<div class="cards"><div class="card"><small>Regression tests</small><strong>{evaluation['tests_run']} passed</strong></div><div class="card"><small>Synthetic domains</small><strong>9</strong></div><div class="card"><small>Independent holdout units</small><strong>0</strong></div><div class="card"><small>Production release</small><strong style="color:#f2cf88">BLOCKED</strong></div></div>
<div class="note">These are supplied synthetic findings, not model-generated diligence. Exact quotes test provenance, not professional judgment. No Slack, model or Pinecone service was called.</div>
<div class="flow">Purpose-specific consent → Scoped graph retrieval → Citation checks → Bounded repair → Human interrupt</div>
<h2>Reproducible demonstration</h2><p>A fabricated 30-day notice quote is rejected. A supplied 90-day source quote reaches review on pass two. Review remains pending; no external action follows.</p>
<table><thead><tr><th>Specialist</th><th>Synthetic source quote</th><th>Validation</th></tr></thead><tbody>{rows}</tbody></table>
<h2>KPI interpretation</h2><p>Synthetic citation precision: {k['citation_precision']:.2f} · Synthetic retrieval recall: {k['retrieval_recall']:.2f} · Opportunity precision@5: not measured.<br>Retrieval+verification component timings are recorded separately from the end-to-end production latency target.</p><p><a href="evaluation.json">Machine-readable report</a> · <a href="../docs/ai-agent-evaluation.md">KPI definitions</a> · <a href="https://a2zsoc.com">A2Z SOC — implementation and support</a></p><footer>Independent experimental project. Not endorsed by CNCF. No DMs/private-channel ingestion, automated outreach or autonomous contracting.</footer></main></html>'''
    (ROOT/'evidence/report.html').write_text(doc)
    print('Built public synthetic report.')
if __name__=='__main__':main()
