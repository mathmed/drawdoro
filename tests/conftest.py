import os

# Tests must not depend on the developer's local .env: environment variables take precedence
# over it, so authentication is pinned off here and enabled explicitly by the tests that need it.
os.environ["AUTH_ENABLED"] = "false"
os.environ["ENV"] = "test"
