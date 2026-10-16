# Authentication and permissions

Sign-in uses an Amazon Cognito user pool with Google federation (authorization code + PKCE, no client
secret). The API validates the Cognito **ID token** (`iss`, `aud`, `token_use`, `exp`) on every route
except `/health` and `/ready`, creates the user in `users` on first sign-in, and the WebSocket reads it from `?token=`.
Leave `AUTH_ENABLED=false` and the `VITE_COGNITO_*` variables empty to develop without logging in. The variables
are described in [Configuration](CONFIGURATION.md).

## Workspace roles

Access is scoped by workspace membership (`workspace_members`): the creator of a workspace becomes its
**owner**, and only members see it. **Viewers** read, **editors** also change content, and **owners** also
manage members and rename or delete the workspace. Resources outside the user's workspaces answer 404.
A workspace always keeps at least one owner. Workspaces that have no members (created before sign-in was
enabled) are adopted by the first signed-in user who lists workspaces.

Agents authenticate with an API key instead of a sign-in: the shared `SERVICE_API_KEY` or a personal key, see
[Diagram history and personal API keys](FEATURES.md#diagram-history-and-personal-api-keys).

## Cognito app client

The app client in the pool needs: no client secret, the *Authorization code grant*, scopes
`openid email profile`, the Google identity provider enabled, callback URL `<app origin>/auth/callback`
and sign-out URL `<app origin>` with no trailing slash (add the `http://localhost:3000` ones for local testing).

## Profile photos

Profile photos come from the ID token's `picture` claim: map the Google attribute `picture` to the user pool
attribute `picture` in the Google identity provider and allow the app client to read it. The photo (https
URLs only) is stored on the user, returned by `/me` as `picture_url` and shared in the diagram presence;
without it avatars fall back to the name's initial.
