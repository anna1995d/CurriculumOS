"""
Human-in-the-loop event registry.

Events are keyed by (pipeline_id, node_id) so that fixed node IDs like
'node-audience' don't bleed across pipeline runs.

The orchestrator awaits a node's event when it needs human approval.
The API layer (main.py) sets the event when the human approves/edits/decides.
"""

import asyncio
from typing import Dict, Tuple

_events: Dict[Tuple[str, str], asyncio.Event] = {}


def get_node_event(pipeline_id: str, node_id: str) -> asyncio.Event:
    key = (pipeline_id, node_id)
    if key not in _events:
        _events[key] = asyncio.Event()
    return _events[key]


def signal_node_ready(pipeline_id: str, node_id: str) -> None:
    """Call this when a human approves, edits, or decides on a node."""
    get_node_event(pipeline_id, node_id).set()
