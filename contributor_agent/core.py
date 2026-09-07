from dataclasses import dataclass, asdict
from hashlib import sha256
import json
import math
import re
import time
from urllib.parse import urlsplit

PURPOSE = 'personal_contributor_opportunities'
DISCLAIMER = 'Independent experimental project. Not endorsed by CNCF.'

class Denied(ValueError):
    pass

@dataclass(frozen=True)
class Policy:
    tenant: str
    member: str
    version: str
    sources: tuple[str, ...]
    repositories: tuple[str, ...]
    channels: tuple[str, ...]
    skills: tuple[str, ...]
    max_age_days: int = 30
    limit: int = 5

    def digest(self):
        return sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()

@dataclass
class Consent:
    tenant: str
    member: str
    policy_digest: str
    expires_at: float
    purpose: str = PURPOSE
    revoked: bool = False

@dataclass(frozen=True)
class Evidence:
    source: str
    scope: str
    visibility: str
    url: str
    title: str
    tags: tuple[str, ...]
    updated_at: float
    state: str = 'open'

class Agent:
    """Single-user trusted local process. Source text never becomes instructions."""
    def __init__(self, policy, consent, clock=time.time):
        self.policy, self.consent, self.clock = policy, consent, clock
        self.audit = []
        self.pending = {}

    def authorize(self, tenant, member):
        p, c = self.policy, self.consent
        if (tenant, member) != (p.tenant, p.member):
            raise Denied('identity_mismatch')
        if (c.tenant, c.member, c.policy_digest, c.purpose) != (tenant, member, p.digest(), PURPOSE):
            raise Denied('consent_scope_mismatch')
        if type(c.expires_at) not in (int,float) or not math.isfinite(c.expires_at) or c.revoked or c.expires_at <= self.clock():
            self.pending.clear()
            raise Denied('consent_inactive')
        if not 1 <= p.limit <= 20 or not 1 <= p.max_age_days <= 90 or len(p.repositories) > 3:
            raise Denied('invalid_policy_bounds')

    def allowed(self, e):
        p = self.policy
        try:
            u = urlsplit(e.url)
            port = u.port
        except ValueError:
            return False
        if e.source not in p.sources or e.visibility != 'public':
            return False
        if u.scheme != 'https' or u.username or u.password or port not in (None, 443):
            return False
        if e.source == 'github':
            if e.scope not in p.repositories or u.hostname != 'github.com':
                return False
            if not re.fullmatch('/' + re.escape(e.scope) + r'/issues/[0-9]+', u.path):
                return False
        elif e.source == 'cncf':
            if u.hostname != 'contribute.cncf.io' or e.scope != 'contributors':
                return False
        elif e.source == 'slack':
            if e.scope not in p.channels or u.hostname != 'app.slack.com':
                return False
            if not u.path.startswith('/archives/' + e.scope + '/'):
                return False
        else:
            return False
        age = self.clock() - e.updated_at
        return e.state == 'open' and 0 <= age <= p.max_age_days * 86400

    def recommend(self, tenant, member, evidence):
        self.authorize(tenant, member)
        ranked, seen = [], set()
        for e in evidence:
            if not self.allowed(e) or e.url in seen:
                continue
            seen.add(e.url)
            overlap = sorted(set(map(str.lower, e.tags)) & set(map(str.lower, self.policy.skills)))
            if not overlap:
                continue
            ranked.append((len(overlap), e.url, e, overlap))
        results = []
        for score, url, e, overlap in sorted(ranked, key=lambda x: (-x[0], x[1]))[:self.policy.limit]:
            item = dict(url=url, title=re.sub(r'[\x00-\x1f\x7f-\x9f]', '', e.title)[:200], matched_skills=overlap, score=score,
                        source=e.source, updated_at=e.updated_at, disclaimer=DISCLAIMER,
                        next_step='Review contribution guidelines and current availability manually.')
            digest = sha256(json.dumps(item, sort_keys=True).encode()).hexdigest()
            self.pending[digest] = (item, self.clock() + 3600)
            results.append(dict(item, review_id=digest, status='pending_human_review'))
        self.audit.append(dict(event='recommend', count=len(results), at=self.clock()))
        return results

    def review(self, tenant, member, review_id, approve):
        self.authorize(tenant, member)
        record = self.pending.pop(review_id, None)
        if record is None or record[1] <= self.clock():
            raise Denied('review_missing_or_expired')
        self.audit.append(dict(event='review', decision=bool(approve), at=self.clock()))
        return dict(record[0], status='approved_for_personal_use' if approve else 'rejected')

    def revoke(self):
        self.consent.revoked = True
        self.pending.clear()
        self.audit.clear()

    def execute(self, *args, **kwargs):
        raise Denied('external_actions_disabled')
