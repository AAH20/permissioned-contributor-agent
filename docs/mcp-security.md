# MCP security: consent and Slack's official server

The agent's permission is the intersection of member policy, active purpose-specific consent and the source's own access scope. OAuth access is necessary for Slack, but it is not permission to collect everything the token can see.

The only planned Slack endpoint is [Slack's official MCP server](https://docs.slack.dev/ai/slack-mcp-server/): `https://mcp.slack.com/mcp`. The shipped `SlackBoundary` is a tested preflight boundary, not a completed OAuth client. A trusted host must provide an approved app, authenticated session, verified grant and reviewed tool-schema binding.

Before any channel-content read, the boundary checks identity, expiration, administrator authorization reference, public-only scopes and explicitly allowed channel IDs. The trusted binding must provide explicit public/local channel metadata; private, DM, group-DM, externally shared and unknown channels are rejected. No generic tool-name input or message-sending API is exposed.

The local grant reference is an operator assertion, not verified written approval. Production needs a protected authorization registry and actual verification of administrator authority. For a CNCF workspace, written administrator authorization is required before connection or deployment, independently of member consent. No CNCF app has been installed by this project.

## Threat model and limits

- Source text is data, never instructions. The current matcher and synthetic validator do not give tools to an LLM.
- Policy changes invalidate consent digests; revocation and nonfinite/expired timestamps are rejected.
- Review binds to the payload and grant and cannot authorize outreach, spending or contracts.
- A malicious local caller can change Python objects. This is not a hardened multi-tenant server.
- In-memory review state is not durable or transactionally safe across workers. Token vaults, signed grants, production RBAC, deletion and event auditing remain required work.
- Human reviewers must verify current evidence and resolve contradictions; a citation check alone cannot prove a conclusion.

For private or regulated communities, the permitted future input is an explicitly authorized document room under a separate purpose. The project-wide ban on DMs/private Slack channels remains in place.
