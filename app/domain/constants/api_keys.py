# Personal API keys start with this, so they are easy to recognise (e.g. by secret scanners).
API_KEY_PREFIX = "mcpk_"
API_KEY_SECRET_BYTES = 32
# Characters of the secret kept in clear to identify a key in the list.
API_KEY_VISIBLE_CHARS = 12
API_KEY_LABEL_MAX_LENGTH = 60
# last_used_at is refreshed at most this often, so agent bursts don't write on every call.
API_KEY_LAST_USED_RESOLUTION_SECONDS = 60
