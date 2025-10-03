#!/usr/bin/env python3
"""Compatibility wrapper for the packaged LeadVille bridge module."""

import asyncio
import logging

try:
    from impact_bridge.leadville_bridge import main as module_main
except ImportError as exc:  # pragma: no cover - ensure the wrapper fails loudly
    logging.basicConfig(level=logging.ERROR)
    logging.getLogger(__name__).error(
        "LeadVille bridge package unavailable; ensure PYTHONPATH includes src/."
    )
    raise


def main() -> None:
    """Launch the canonical bridge entry point."""
    asyncio.run(module_main())


if __name__ == "__main__":
    main()
