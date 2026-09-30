from dataclasses import dataclass


@dataclass(frozen=True)
class RevisionPolicy:
    # A person's saves within this window update their latest revision instead of adding one.
    interval_minutes: int = 10
    # Revisions older than this are deleted; 0 keeps them regardless of age.
    retention_days: int = 30
    # Only the newest ones are kept per diagram; 0 keeps any number.
    max_per_diagram: int = 100
