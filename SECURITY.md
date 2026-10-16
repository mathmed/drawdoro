# Security policy

Drawdoro stores diagrams, documentation and API keys for whole teams, and its MCP server lets AI agents act on
them: we take reports seriously and thank everyone who makes one.

## Supported versions

Drawdoro has no versioned releases yet: security fixes go into the `main` branch. Update to it before you report.

## Reporting a vulnerability

**Do not open a public issue.** If this repository's *Security* tab offers *Report a vulnerability*, report it
privately there. Otherwise, open an issue that only asks for a private contact, with no detail of the problem.

Please include what you found, the steps to reproduce it (the commit, the relevant settings without their secrets,
and the requests involved) and what an attacker could do with it. Never send real tokens, API keys or data.
Please give us a reasonable time to ship a fix before you disclose the problem.

## What counts

- Reaching a workspace, project, folder, diagram, comment or gallery item you are not a member or owner of, or
  changing content with a role that only reads (see [`docs/AUTHENTICATION.md`](docs/AUTHENTICATION.md)).
- A way around authentication when `AUTH_ENABLED=true`: forged or unchecked ID tokens, or WebSockets that accept
  someone they should refuse.
- A secret (an API key, a token, `SERVICE_API_KEY`) that ends up in logs, error responses or anywhere it is not
  meant to be; personal API keys are only stored as hashes.
- A share link that gives more than read-only access to its own diagram.
- Code execution or data exfiltration through a crafted canvas, comment, documentation page, gallery item or
  image, or through the MCP server's rendering.
- An MCP tool that does more than the API allows the key it uses.

## What does not count

- Instructions planted in comments or other user content that an agent chooses to follow: the MCP server marks
  that content as untrusted data, which lowers the risk of prompt injection but cannot rule it out. A way to make
  the API accept what the key's permissions refuse is in scope, though.
- Anything reachable only with `AUTH_ENABLED=false`, which is meant for local development and refused in
  production.
- Problems of the dependencies, Amazon Cognito or the browsers themselves: report those upstream.

## Recommended setup

Run production with `ENV=production` and `AUTH_ENABLED=true`, keep `SERVICE_API_KEY` secret, keep the MCP server's
HTTP port private unless it sits behind a proxy listed in `MCP_ALLOWED_HOSTS`, and prefer personal API keys for
agents so their actions carry their owner's role.
