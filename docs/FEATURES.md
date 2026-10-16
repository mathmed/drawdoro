# Features in depth

How the diagram previews, the history, personal API keys, comments and the personal gallery behave. The routes
are in [API](API.md); what agents can do with them is in [MCP server](MCP.md).

## Diagram previews

The diagram cards of a project's overview show a preview of each diagram instead of a generic icon. Previews are
rendered by the editor in the browser, never by the server, and stored apart from the diagram:

- **Rendering.** While someone who can edit has a diagram open, the editor renders its current page with tldraw's
  `toImage` after each saved version (theirs, another editor's or an agent's) and once on open when the stored
  preview is missing or older than the diagram. It waits until 2s have passed without a new version or a local edit,
  so a burst of changes renders once and never mid-gesture. Each render makes a light and a dark
  image with a transparent background, so the card's own background shows in either theme. Images are WebP (PNG in
  browsers that can't encode it), scaled down to fit twice the card size (big diagrams shrink, small ones are never
  enlarged); a render over 64 KiB is retried at half the scale once and otherwise left out. An empty page clears the
  preview. Rendering and uploading run in the background: a failure shows no toast and the card keeps what it had.
- **Storage.** `PUT /diagrams/{id}/thumbnail` writes both themes to `diagram_thumbnails` (one row per diagram and
  theme) in one atomic upsert that only replaces an older `version`, so late, retried or concurrent uploads never
  bring back an older image. The table is separate from `diagrams`, so storing a preview never changes the diagram's
  `updated_at` ("Edited ..." on the card) and opening or listing diagrams never reads the images.
- **Listing.** The overview fetches `GET /projects/{id}/diagrams/thumbnails?theme=` once per visit and theme, next
  to the project tree (which stays lean for the sidebar and the MCP server). Cards show an empty preview area while it
  loads and the placeholder icon for diagrams without a preview (empty, or never opened by an editor since previews
  exist: the first editor who opens one renders it).
- **Permissions.** Reading previews needs workspace membership, like the listing; storing one needs the editor role,
  and the editor only renders for owners and editors (nobody while the role is still loading). Viewers, share-link
  guests and the public `/share/{token}` payload are unchanged: they never write previews nor receive them.

## Diagram history and personal API keys

Every saved change to a diagram is kept in `diagram_revisions` as a full snapshot (name, canvas, shape metadata)
with its author, origin (`human` or `agent`), an optional summary and timestamps. The editor's *History* tab lists
them with a preview, and editors and owners can restore any of them; viewers only look.

To keep the table small:

- A person's saves (the editor autosaves every few seconds) update their own revision for
  `REVISION_INTERVAL_MINUTES`, so each person gets at most one revision per interval, even when several people
  edit together.
- Every agent change (`update_diagram`, `edit_shapes`) and every restore gets a revision of its own, and the state
  right before it is captured first (as a `baseline`) when the history doesn't already end with it.
- Saves that change nothing (e.g. `{}` versus no metadata) don't add revisions.
- After each write, revisions beyond `REVISION_MAX_PER_DIAGRAM` or older than `REVISION_RETENTION_DAYS` are deleted.

A restore brings back the canvas and shape metadata (name and folder stay), is recorded as a new `restore` revision
and is pushed to every open editor, so it can itself be undone.

People create **personal API keys** from the user menu (*API keys* or *Connect Claude*). Each has a label and a
last-used time; the secret (`mcpk_...`) is shown once and only its SHA-256 hash is stored. A key acts as its owner,
with their role, but can't manage keys. Agents using one show up as *Ana's Claude* in the presence avatars and the
history, so two people's agents are two different avatars. The shared `SERVICE_API_KEY` still works as an agent
without owner.

## Comments

Comments are plain text (never rendered as HTML or Markdown), anchored to a shape through `element_id` or to the
whole diagram. Control characters and bidirectional overrides are dropped, and the text is limited to 5000
characters. Each comment records who wrote it with the same identity rules as the history: a person, an agent with
a personal key (shown as *Ana's Claude*, with an agent mark and the key's label), or an ownerless agent on the
shared `SERVICE_API_KEY`.

A comment is open until someone resolves it; it can be reopened, and the editor shows who resolved it and when.
The *Comments* tab hides resolved comments behind *Show resolved* and dims them, and the pins on the canvas and the
tab count only open comments.

| Action | People | Agents (MCP server) |
|---|---|---|
| Read | Any member | Any member (the key owner's role) |
| Create | Editor or owner | Editor or owner |
| Resolve / reopen | Editor or owner, any comment | Editor or owner, any comment (it's reversible and recorded) |
| Delete | Editor or owner, any comment | Editor or owner, and only comments written with **the same key** |

The backend enforces these rules; the MCP tools only describe them. The shared service key keeps skipping workspace
roles, as for every other route, but it can only delete the comments written with it. Creating, resolving,
reopening and deleting are logged at `INFO` with who did it (never the text).

## Personal gallery

The gallery holds what each person saved for reuse: selections of shapes and images (PNG, JPEG, GIF or WebP).
Items have a name, up to 10 tags (stored in lower case) and an optional description, edited and searched in the
editor's *Gallery* panel. It is personal: every route works on the caller's own items, someone else's item answers
`404`, and the shared service key (no owner) gets `403` with a message asking for a personal key. With
`AUTH_ENABLED=false` the items without owner form one shared gallery.

Agents reach it with a personal key: `list_gallery_items` (search by name, tag or description, filter by kind, up to
100 items per call; never image data), `get_gallery_item` (what a "shapes" item contains, or an image's size),
`update_gallery_item` (name, tags, description) and `insert_gallery_item`. The tool descriptions and the server
instructions tell the agent to look in the gallery before drawing a logo, an icon or a component from scratch.
Names, tags, descriptions and texts come in `untrusted_user_content` / `untrusted_text` next to a `notice` saying
they are data, not instructions.

Insertion runs in the API (`POST /diagrams/{id}/gallery-insertions`), so people and agents share the same rules: it
needs the editor role in the diagram's workspace, copies every shape, binding and asset with new ids (arrows stay
connected, nothing is overwritten), keeps the layout, places the copy where asked without covering shapes, refuses
items whose record versions differ from the diagram's tldraw schema (the server doesn't migrate records), and is
recorded in the history (as the agent, with the person it works for) and pushed to open editors. Positions must be
finite and within a billion units of the origin, the scale between 0.1 and 10, and the diagram must stay within 4000
shapes and `GALLERY_MAX_CANVAS_BYTES`; items whose shapes repeat an id or don't all hang from a top-level shape are
refused rather than copied as a broken tree. Images are embedded in the canvas as a `data:` URL built from the
stored bytes, whose type was detected from their content on upload, so no external URL is ever fetched or stored.
