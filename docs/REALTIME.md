# Real-time collaboration

Two WebSockets carry everything live: `/ws/diagrams/{id}` (canvas updates, presence, pointers, saved changes
and comment notifications for one diagram) and `/ws/workspaces/{id}/presence` (who is in each diagram, for the
sidebar). Both are listed in the [API routes](API.md#routes-placeholder).

## Live cursors

Everyone with a diagram open sees the other people's pointers as coloured arrows with their name, in the editor,
in presentation mode and on a shared link, over the same `/ws/diagrams/{id}` socket as the presence. The colour and
name are the ones of the presence avatars; nobody sees their own pointer, not even from another tab.

Pointers travel in page (canvas) coordinates, so each viewer draws them at their own zoom, pan and window size:

- Client to server, at most ~30 a second and only when the position changes (rounded to 0.1):
  `{"type": "cursor", "point": {"x": 120.5, "y": -40}, "page": "page:page"}`, or `{"type": "cursor", "point": null}`
  when the pointer leaves the canvas.
- Server to the other connections of the same diagram, stamped with the sender's presence id and name (a client
  cannot speak for someone else): `{"type": "cursor", "id": "<presence id>", "name": "Ana", "point": {...} | null,
  "page": "page:page" | null}`.

The server never stores positions. It validates each message (finite coordinates within ±10,000,000, a tldraw page
id, no extra fields) and relays at most 60 a second per connection, dropping the rest. Receivers ease each cursor
towards its latest position on every animation frame without re-rendering the app, show only the cursors on the page
they are looking at, and drop a cursor when its pointer leaves the canvas, when the person leaves the diagram, when
the connection drops or after 30s without moving. Messages a client does not understand are ignored.

## Sidebar presence

The sidebar shows, next to each diagram, the photos of the people who have it open right now and, next to each
project (even collapsed), everyone in any of its diagrams, each person once. Up to three faces are stacked with a
`+N` for the rest; tooltips and the group's `aria-label` carry the names. Photos come from the same `picture_url`
as the presence avatars (initial on the person's colour when there is none or it fails to load), agents look as they
do in the presence, and share-link guests in a diagram are shown under the name they entered. You are left out of the
sidebar (the top bar already shows you in the open diagram), whether you are in one tab or several.

Each open sidebar holds one socket, `/ws/workspaces/{id}/presence`, whatever the number of diagrams:

- On connect: `{"type": "presence_snapshot", "you": "<your presence id>" | null, "diagrams": [{"diagram_id":
  "...", "project_id": "...", "users": [<presence entries>]}]}`, with only the diagrams someone is in.
- Then: `{"type": "presence_delta", "diagrams": [...]}` with only the diagrams whose people changed, each with its
  full list (`"users": []` when everyone left). Changes are batched for 1s per workspace, so a signed-in person
  who reloads and is back within the batch causes no message, and a burst of joins sends one.
- Presence entries are the ones of the diagram socket: `id`, `name`, `kind` (`person` or `agent`), `picture_url`
  for people and `owner_id`/`owner_name`/`label` for agents with a personal key.

Permissions follow the workspace: any member (viewer and up) can open every diagram of the workspace, so a member
sees the presence of every diagram of that workspace and of no other. The socket needs a signed-in member's ID token;
no token (share-link guests) or a token of someone outside the workspace is refused with close code 1008, and the
membership is checked again every 60s, so someone removed from the workspace stops receiving it without reloading
(a check that fails for another reason closes the socket too). Each person may hold 10 of these sockets at once, and
since the channel only flows from server to client, a client that keeps sending (more than a burst of 10, then 1 a
second) is disconnected. With authentication disabled the socket is open to anyone, like the rest of the API, and
rooms of diagrams that do not exist (only reachable that way) are never shown.
The client reconnects 2s after a drop (30s after a 1008) and shows nobody while disconnected.
