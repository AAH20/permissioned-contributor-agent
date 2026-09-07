# Personal read-only GitHub pilot

Review `examples/policy.json` and set your own member ID, public repositories, skill labels and expiry. Do not infer a person's languages, interests or permission from a public profile. `good first issue` is a broad issue label, not a reliable skill match.

Compute the policy digest:

```sh
python -c 'import json; from contributor_agent.core import Policy; print(Policy(**json.load(open("examples/policy.json"))).digest())'
```

After explicitly consenting, create a local `consent.json` with matching `tenant`, `member`, `policy_digest`, a finite future Unix `expires_at`, `purpose` equal to `personal_contributor_opportunities`, and `revoked` equal to `false`. Do not commit the file or reuse consent for a different purpose.

```sh
python -m contributor_agent pilot --policy examples/policy.json --consent consent.json
```

The collector verifies public repository status, uses unauthenticated bounded reads and excludes pull requests and assigned/unknown-assignment issues. It requests at most 20 matching records per repository in up to three repositories. Empty output is a valid abstention; it is not a comprehensive census of available issues.

The human reviews source availability and contribution instructions. Typing `approve` permits personal use only. The agent does not create an issue, send a message, purchase anything or deploy.

No raw session consent receipt or identifying browser capture is included in the OSS release. The sanitized historical smoke-test summary explains the assignment-filter fix without publishing session data.
