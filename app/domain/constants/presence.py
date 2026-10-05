# How long an agent (the MCP server) stays listed in a diagram after its last call.
AGENT_PRESENCE_SECONDS = 60

# Clients send at most ~30 pointer moves a second; the server relays up to this many per
# connection and drops the rest, so a misbehaving client cannot flood a diagram.
CURSOR_MESSAGES_PER_SECOND = 60
CURSOR_MESSAGE_BURST = 60

# The sidebar's view of who is in each diagram of a workspace. Changes are batched for this long,
# so a reload (leave and come back) or a burst of joins reaches the subscribers as one message.
WORKSPACE_PRESENCE_BATCH_SECONDS = 1.0
# Open sidebars (tabs) one person may subscribe at once; more are refused.
WORKSPACE_PRESENCE_SUBSCRIPTIONS_PER_USER = 10
# How often a subscriber's membership is checked again, so someone removed from the workspace
# stops seeing its presence without having to reload.
WORKSPACE_PRESENCE_RECHECK_SECONDS = 60.0
# The channel only flows from server to client: a client that keeps sending is cut off.
WORKSPACE_PRESENCE_MESSAGE_BURST = 10
WORKSPACE_PRESENCE_MESSAGES_PER_SECOND = 1
