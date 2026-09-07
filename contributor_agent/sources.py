"""Bounded public HTTP reads and a fail-closed official Slack MCP boundary."""
import json
import re
import time
from datetime import datetime
from urllib.request import Request, build_opener, HTTPRedirectHandler
from .core import Evidence, Denied

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise Denied('redirect_disabled')

def public_json(url):
    # Only called with a generated GitHub API URL; no credentials or ambient cookies.
    request = Request(url, headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'independent-contributor-pilot'})
    with build_opener(NoRedirect).open(request, timeout=15) as response:
        data = response.read(1_000_001)
        if len(data) > 1_000_000:
            raise Denied('response_too_large')
        return json.loads(data)

def github(agent, tenant, member, fetch=public_json):
    agent.authorize(tenant, member)
    if 'github' not in agent.policy.sources:
        raise Denied('source_disabled')
    out = []
    for repo in agent.policy.repositories:
        agent.authorize(tenant, member)
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo):
            raise Denied('invalid_repository')
        base = 'https://api.github.com/repos/' + repo
        metadata = fetch(base)
        if metadata.get('private') is not False or metadata.get('full_name', '').lower() != repo.lower():
            raise Denied('repository_not_verified_public')
        for issue in fetch(base + '/issues?state=open&labels=good%20first%20issue&per_page=20'):
            # An open issue may already have an owner. Unknown assignment also abstains.
            if 'pull_request' in issue or issue.get('assignees') != []:
                continue
            out.append(Evidence('github', repo, 'public', issue['html_url'], issue['title'],
                tuple(label['name'] for label in issue['labels']),
                datetime.fromisoformat(issue['updated_at'].replace('Z', '+00:00')).timestamp(), issue['state']))
    return out

SLACK_ENDPOINT = 'https://mcp.slack.com/mcp'
PUBLIC_SCOPES = frozenset({'search:read.public', 'channels:read', 'channels:history'})

class SlackBoundary:
    """Host injects authenticated MCP session and reviewed schema binding.

    No generic tool-call API. Channel metadata must be fetched by the trusted host,
    never inferred from a message. All checks precede any content request.
    """
    def __init__(self, agent, session, binding, grant):
        self.agent, self.session, self.binding, self.grant = agent, session, binding, grant

    async def read(self, tenant, member, channel):
        self.agent.authorize(tenant, member)
        g, b = self.grant, self.binding
        if 'slack' not in self.agent.policy.sources or channel not in self.agent.policy.channels:
            raise Denied('channel_not_allowed')
        if (g.get('tenant'), g.get('member')) != (tenant, member):
            raise Denied('slack_identity_mismatch')
        if (g.get('endpoint') != SLACK_ENDPOINT or not g.get('app_id') or
            g.get('expires_at', 0) <= self.agent.clock() or not g.get('admin_authorization_ref')):
            raise Denied('slack_grant_unverified')
        scopes = set(g.get('scopes', []))
        if not scopes or not scopes <= PUBLIC_SCOPES or 'channels:history' not in scopes:
            raise Denied('excessive_or_missing_scopes')
        # Production host must bind these attestations to OAuth identity and signed admin evidence.
        metadata = await b.channel_metadata(self.session, channel)
        if (metadata.get('id') != channel or metadata.get('workspace') != g.get('workspace') or
            metadata.get('is_private') is not False or metadata.get('is_im') is not False or
            metadata.get('is_mpim') is not False or metadata.get('is_ext_shared') is not False):
            raise Denied('channel_not_verified_public_local')
        self.agent.authorize(tenant, member)
        return await b.read_public_channel(self.session, channel, limit=20)
