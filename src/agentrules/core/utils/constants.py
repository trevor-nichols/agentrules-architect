"""Shared constants for core utilities.

Centralizes filenames and other cross-cutting settings so they can be
updated in one place without combing through multiple modules.
"""

DEFAULT_RULES_FILENAME = "AGENTS.md"
"""Default filename for the generated agent guidance document."""

DEFAULT_SNAPSHOT_FILENAME = "SNAPSHOT.md"
"""Default filename for generated snapshot artifacts."""

DEFAULT_RULES_TREE_MAX_DEPTH = 3
"""Default depth for the AGENTS project structure tree section."""

# Historically this constant was imported directly across the codebase. Preserve it for
# backward compatibility, but prefer `DEFAULT_RULES_FILENAME` and allow runtime overrides
# via configuration where supported.
FINAL_RULES_FILENAME = DEFAULT_RULES_FILENAME
"""Deprecated alias of the default rules filename; prefer DEFAULT_RULES_FILENAME."""
