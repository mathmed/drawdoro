# How long an agent (the MCP server) stays listed in a diagram after its last call.
AGENT_PRESENCE_SECONDS = 60

# Clients send at most ~30 pointer moves a second; the server relays up to this many per
# connection and drops the rest, so a misbehaving client cannot flood a diagram.
CURSOR_MESSAGES_PER_SECOND = 60
CURSOR_MESSAGE_BURST = 60
