"""Loads and serves call-flow definitions from JSON files in data/flows/.

Each process (campaign/call type) is a JSON file describing a graph of steps.
Steps either have a single `next_step_id` (linear) or a list of `options`,
each pointing to a different `next_step_id` (branching).
"""
import json
import os
from functools import lru_cache

from app.core.config import get_settings
from app.models.schemas import FlowDefinition, ProcessSummary

settings = get_settings()


def _flows_dir() -> str:
    # Resolve relative to the backend/ directory regardless of cwd.
    here = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # backend/
    return os.path.normpath(os.path.join(here, settings.flows_dir))


@lru_cache
def _load_all_flows() -> dict[str, FlowDefinition]:
    flows: dict[str, FlowDefinition] = {}
    flows_dir = _flows_dir()
    if not os.path.isdir(flows_dir):
        return flows
    for filename in os.listdir(flows_dir):
        if not filename.endswith(".json"):
            continue
        with open(os.path.join(flows_dir, filename), "r", encoding="utf-8") as f:
            data = json.load(f)
        flow = FlowDefinition(**data)
        flows[flow.process_id] = flow
    return flows


def list_processes() -> list[ProcessSummary]:
    return [
        ProcessSummary(process_id=f.process_id, name=f.name, description=f.description)
        for f in _load_all_flows().values()
    ]


def get_flow(process_id: str) -> FlowDefinition | None:
    return _load_all_flows().get(process_id)


def get_step(process_id: str, step_id: str):
    flow = get_flow(process_id)
    if not flow:
        return None
    for step in flow.steps:
        if step.id == step_id:
            return step
    return None


def reload_flows():
    """Clear the cache, e.g. after editing flow JSON files."""
    _load_all_flows.cache_clear()
