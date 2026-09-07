import argparse
import json
import time
from pathlib import Path
from .core import Agent, Policy, Consent, Evidence
from .sources import github


def main():
    parser = argparse.ArgumentParser(description='Independent read-only contributor pilot')
    parser.add_argument('mode', choices=['demo', 'pilot'])
    parser.add_argument('--policy', type=Path)
    parser.add_argument('--consent', type=Path)
    args = parser.parse_args()
    now = time.time()
    if args.mode == 'demo':
        p = Policy('synthetic', 'member-demo', '1', ('github',), ('cncf/example',), (), ('documentation', 'go'))
        c = Consent(p.tenant, p.member, p.digest(), now + 3600)
        evidence = [Evidence('github', 'cncf/example', 'public', 'https://github.com/cncf/example/issues/1',
                             'SYNTHETIC: improve contributor documentation', ('documentation',), now)]
    else:
        if not args.policy or not args.consent:
            parser.error('pilot requires --policy and --consent; never generates consent automatically')
        p = Policy(**json.loads(args.policy.read_text()))
        c = Consent(**json.loads(args.consent.read_text()))
        evidence = None
    agent = Agent(p, c)
    if evidence is None:
        evidence = github(agent, p.tenant, p.member)
    results = agent.recommend(p.tenant, p.member, evidence)
    print(json.dumps({'mode': args.mode, 'recommendations': results}, indent=2))
    if args.mode == 'pilot':
        for item in results:
            answer = input('Approve for personal use only? Type approve, otherwise reject: ')
            print(json.dumps(agent.review(p.tenant, p.member, item['review_id'], answer == 'approve')))

if __name__ == '__main__':
    main()
