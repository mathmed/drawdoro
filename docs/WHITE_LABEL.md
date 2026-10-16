# White-label

The product name is configuration, not code, so a fork can rebrand the app and still take upstream changes with
`git merge` without conflicts. Code identifiers (classes, shape utils, tldraw ids, the `window.renderDiagram` hook
used by `render_diagram`, package names) are brand-neutral; everything people or agents read comes from:

| Where | Setting | Used for |
|---|---|---|
| API | `APP_NAME` (`app/common/settings.py`) | OpenAPI title, error messages such as "hasn't signed in to <name> yet" |
| MCP server | `APP_NAME` (`mcp/settings.py`) | Server name (slug of the name), description, instructions sent to agents, API error messages |
| Frontend | `VITE_APP_NAME` (`frontend/src/config/branding.ts`) | Page title, logo wordmark, loading screens, landing, home, 404 and members texts |
| Frontend | `VITE_APP_SLUG` (`frontend/src/config/branding.ts`) | Prefix of the localStorage/sessionStorage keys |
| Docker compose | `APP_NAME`, `APP_SLUG` (root `.env`) | Passes the name to the three services; names the containers and local database |

`VITE_*` variables are read at build time, so set them where the frontend is built (`frontend/.env`, the shell or the
Docker build). For example, a fork called CondoDraw sets `APP_NAME=CondoDraw` for the API and the MCP server and
`VITE_APP_NAME=CondoDraw` for the frontend build; the storage slug then becomes `condodraw`. Changing
`VITE_APP_SLUG` signs everyone out. Deployment files (manifests, workflows, web server config) and the logo artwork
(`frontend/public/favicon.svg`, `components/ui/Logo.tsx`) stay per fork.

The loading screens are branded the same way: `BrandLoader` (boot, sign-in, opening a diagram or a shared link) draws
the `Logo` component and, where it shows a name, `branding.name`, so a build with `VITE_APP_NAME=CondoDraw` shows the
CondoDraw name with no code change. To change the logo a fork replaces the artwork in `components/ui/Logo.tsx` (and
`public/favicon.svg`); the loaders, the landing page and the headers all pick it up, since none of them draws the mark
themselves. The loader colours (halo, orbiting arc, progress bar) come from the `--accent` token in
`frontend/src/styles/tokens.css`.

The repository's own documentation artwork (`media/icon.svg`, `media/icon.png`, used by the README) is separate
from the app's logo and is never shown by the app.
