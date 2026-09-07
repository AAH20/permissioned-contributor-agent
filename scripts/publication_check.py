"""Conservative release-tree check. A supplement to review, not a secret-scanner guarantee."""
from pathlib import Path
import re, sys
ROOT=Path(__file__).resolve().parents[1]
SKIP={'.git','.venv','__pycache__','node_modules','build','dist'}
BLOCKED={'research-and-commercial-plan.md','pricing-screenshot.png','github-live.json',
         'github-baseline.json','consent.json','github-source-screenshot.png'}
RULES=[re.compile(r'/' + 'Users' + r'/[^/\s]+/'),re.compile(r'/' + 'home' + r'/[^/\s]+/'),
       re.compile(r'gh[pousr]_[A-Za-z0-9]{20,}'),re.compile(r'xox[baprs]-[A-Za-z0-9-]{15,}'),
       re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')]

def main():
    failures=[];count=0
    for p in ROOT.rglob('*'):
        if any(x in SKIP for x in p.relative_to(ROOT).parts) or not p.is_file():continue
        count+=1
        if p.is_symlink():failures.append(str(p.relative_to(ROOT))+':symlink')
        if p.name in BLOCKED or p.name.startswith('.env'):failures.append(str(p.relative_to(ROOT))+':private-name')
        if p.suffix not in ('.png','.jpg','.woff','.woff2'):
            text=p.read_text(errors='replace')
            if any(rule.search(text) for rule in RULES):failures.append(str(p.relative_to(ROOT))+':sensitive-pattern')
    for required in ['LICENSE','NOTICE','README.md','SECURITY.md','CONTRIBUTING.md','docs/ai-agent-evaluation.md']:
        if not (ROOT/required).is_file():failures.append(required+':missing')
    if failures:
        print('\n'.join(failures));return 1
    print(f'Publication checks passed for {count} files; manual scope review is still required.')
    return 0
if __name__=='__main__':sys.exit(main())
