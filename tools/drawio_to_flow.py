"""Convert the "AS IS" draw.io process maps into the app's data structure.

Each *.drawio.xml file is one call category (Billing, Device Support,
Essentials, Upgrades). Every file has an "Overview" page (the call flow the
agent steps through) plus one page per task sub-procedure.

This script produces, for each file:
  - data/flows/<id>.json          flow graph built from the Overview page
  - data/knowledge/<id>/*.md      one markdown doc per page (Overview + subs),
                                  used by the RAG chat assistant

Run:  python tools/drawio_to_flow.py
Re-run any time the diagrams change. It only reads the .drawio.xml files and
writes into data/; nothing else is touched.
"""
from __future__ import annotations

import html
import json
import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLOWS_DIR = os.path.join(ROOT, "data", "flows")
KNOWLEDGE_DIR = os.path.join(ROOT, "data", "knowledge")

# filename (without " AS IS.drawio.xml") -> process metadata
PROCESSES = {
    "Billing Process": {
        "id": "billing",
        "name": "Billing",
        "description": "Customer is calling about a bill, charge, refund or payment "
        "— explain a bill, handle a dispute, change details, or take a payment.",
    },
    "Device Support": {
        "id": "device_support",
        "name": "Device Support",
        "description": "Customer needs help with a device — troubleshooting, "
        "simulator, unlock, track/repair returns, or cancellations.",
    },
    "Essentials": {
        "id": "essentials",
        "name": "Essentials",
        "description": "Account essentials — apply bundles, credits, vouchers, "
        "refunds, clubcard points, and balance checks.",
    },
    "Upgrades": {
        "id": "upgrades",
        "name": "Upgrades",
        "description": "Customer wants to upgrade — triage, eligibility check, and "
        "completing the upgrade.",
    },
}

# The page that holds the agent-facing call flow (used to build the flow JSON).
OVERVIEW_PAGES = {"Overview", "Page-1"}

NOTE_FILL = "#dae8fc"  # blue annotation boxes ("Steps to Triage...", "OTAC is...")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def clean(value: str | None) -> str:
    """Strip HTML tags and unescape entities from a draw.io label."""
    if not value:
        return ""
    text = value.replace("<br>", " ").replace("<br/>", " ")
    text = re.sub(r"<[^>]+>", " ", text)        # drop <font>, <span>, ...
    text = html.unescape(html.unescape(text))    # &amp;amp; -> &amp; -> &
    text = text.replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def slugify(text: str, fallback: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return s[:50] or fallback


def style_of(cell: ET.Element) -> str:
    return cell.get("style", "") or ""


def is_swimlane(style: str) -> bool:
    return "swimlane" in style


def is_stack_container(style: str) -> bool:
    # Legend / option boxes (Query Types, Tools, Actions, Options List).
    return "childLayout=stackLayout" in style


def is_step(cell: ET.Element) -> bool:
    """A real process node: a rectangle or decision rhombus, not a lane/label/note."""
    if cell.get("vertex") != "1":
        return False
    style = style_of(cell)
    if any(
        tok in style
        for tok in ("swimlane", "edgeLabel", "text;", "rotation=-90", "direction=east")
    ):
        return False
    if NOTE_FILL in style:           # blue annotation boxes -> captured as notes
        return False
    if not clean(cell.get("value")):
        return False
    is_box = style.startswith("rounded=") or "rhombus" in style
    return is_box


# --------------------------------------------------------------------------- #
# Page model
# --------------------------------------------------------------------------- #
@dataclass
class Node:
    id: str
    title: str
    system: str
    decision: bool
    x: float
    y: float
    out: list[tuple[str, str]] = field(default_factory=list)  # (target_id, label)
    indeg: int = 0


@dataclass
class Page:
    name: str
    nodes: dict[str, Node]
    notes: list[str]
    legend: list[str]


def parse_page(model: ET.Element, page_name: str) -> Page:
    cells = model.findall(".//mxCell")
    by_id = {c.get("id"): c for c in cells if c.get("id")}

    # Geometry lookup (relative to parent) for absolute positioning.
    def geom(cell: ET.Element) -> tuple[float, float]:
        g = cell.find("mxGeometry")
        if g is None:
            return 0.0, 0.0
        return float(g.get("x", 0) or 0), float(g.get("y", 0) or 0)

    def abs_pos(cell: ET.Element) -> tuple[float, float]:
        x, y = geom(cell)
        parent = by_id.get(cell.get("parent"))
        seen = set()
        while parent is not None and parent.get("id") not in ("0", "1") and parent.get("id") not in seen:
            seen.add(parent.get("id"))
            px, py = geom(parent)
            x += px
            y += py
            parent = by_id.get(parent.get("parent"))
        return x, y

    # Swimlane (lane) names, excluding stack-layout legend containers.
    lanes = {
        c.get("id"): clean(c.get("value"))
        for c in cells
        if is_swimlane(style_of(c)) and not is_stack_container(style_of(c))
    }
    stack_ids = {c.get("id") for c in cells if is_stack_container(style_of(c))}

    def system_for(cell: ET.Element) -> str:
        parent = by_id.get(cell.get("parent"))
        seen = set()
        while parent is not None and parent.get("id") not in seen:
            seen.add(parent.get("id"))
            if parent.get("id") in lanes:
                return lanes[parent.get("id")]
            parent = by_id.get(parent.get("parent"))
        return ""

    # Nodes.
    nodes: dict[str, Node] = {}
    for c in cells:
        if is_step(c):
            ax, ay = abs_pos(c)
            nodes[c.get("id")] = Node(
                id=c.get("id"),
                title=clean(c.get("value")),
                system=system_for(c),
                decision="rhombus" in style_of(c),
                x=ax,
                y=ay,
            )

    # Edge labels: a child vertex (style=edgeLabel) whose parent is the edge id.
    edge_labels: dict[str, str] = {}
    for c in cells:
        if "edgeLabel" in style_of(c):
            lbl = clean(c.get("value"))
            if lbl:
                edge_labels.setdefault(c.get("parent"), lbl)

    # Edges between two step nodes.
    for c in cells:
        if c.get("edge") == "1":
            src, tgt = c.get("source"), c.get("target")
            if src in nodes and tgt in nodes:
                label = clean(c.get("value")) or edge_labels.get(c.get("id"), "")
                nodes[src].out.append((tgt, label))
                nodes[tgt].indeg += 1

    # Notes (blue boxes) and legend items (children of stack containers).
    notes, legend = [], []
    for c in cells:
        style = style_of(c)
        val = clean(c.get("value"))
        if not val:
            continue
        if NOTE_FILL in style and not is_swimlane(style):
            notes.append(val)
        elif c.get("parent") in stack_ids:
            legend.append(val)

    return Page(name=page_name, nodes=nodes, notes=notes, legend=legend)


def parse_file(path: str) -> list[Page]:
    tree = ET.parse(path)
    pages = []
    for diagram in tree.getroot().findall("diagram"):
        model = diagram.find("mxGraphModel")
        if model is None:
            continue
        pages.append(parse_page(model, diagram.get("name", "Page")))
    return pages


# --------------------------------------------------------------------------- #
# Output builders
# --------------------------------------------------------------------------- #
def assign_step_ids(nodes: dict[str, Node]) -> dict[str, str]:
    out, used = {}, set()
    for n in sorted(nodes.values(), key=lambda n: (n.x, n.y)):
        base = slugify(n.title, n.id)
        sid, i = base, 2
        while sid in used:
            sid = f"{base}_{i}"
            i += 1
        used.add(sid)
        out[n.id] = sid
    return out


def build_flow(page: Page, meta: dict) -> dict:
    # Drop fully-isolated stray boxes (e.g. a duplicate "Close Account" with no
    # edges) — they aren't part of any flow.
    nodes = {
        nid: n for nid, n in page.nodes.items() if n.indeg or n.out
    }

    # Start = an entry node (no incoming edges), top-left-most.
    entries = [n for n in nodes.values() if n.indeg == 0]
    start = min(entries or list(nodes.values()), key=lambda n: (n.x, n.y))

    def reachable() -> set[str]:
        seen, stack = set(), [start.id]
        while stack:
            cur = stack.pop()
            if cur in seen or cur not in nodes:
                continue
            seen.add(cur)
            stack += [t for t, _ in nodes[cur].out]
        return seen

    # Wrap-up bridge: the AS-IS Overview pages let the success path dead-end once
    # the account is open, because the actual task is handled on a separate
    # sub-procedure page. The standard call close (Close Account -> disposition
    # -> notes -> ACW) is drawn but left unconnected. Reconnect the reachable
    # success leaf to that close chain so the agent-facing guide completes,
    # mirroring how the fully-wired Upgrades page works.
    reach = reachable()

    def is_failure_end(n: Node) -> bool:
        t = n.title.lower()
        return "acw" in t or "dpa has failed" in t or "end call" in t

    close_heads = [
        n for n in nodes.values()
        if n.title.strip().lower() == "close account" and n.out and n.id not in reach
    ]
    bridged = set()
    if close_heads:
        head = close_heads[0]
        success_leaves = [
            n for n in nodes.values()
            if n.id in reach and not n.out and not is_failure_end(n)
        ]
        for leaf in success_leaves:
            leaf.out.append((head.id, ""))
            head.indeg += 1
            bridged.add(leaf.id)

    ids = assign_step_ids(nodes)

    steps = []
    for n in sorted(nodes.values(), key=lambda n: (n.x, n.y)):
        instructions = (f"System: {n.system}. " if n.system else "") + n.title
        if n.id in bridged:
            instructions += (
                " — then complete the customer's request using the relevant "
                "procedure (ask the assistant if unsure), and return here to close."
            )
        step = {
            "id": ids[n.id],
            "title": n.title,
            "instructions": instructions,
        }
        if not n.out:
            step["is_end"] = True
        elif len(n.out) == 1:
            step["next_step_id"] = ids[n.out[0][0]]
        else:
            step["options"] = [
                {
                    "label": (lbl.title() if lbl else nodes[tgt].title),
                    "next_step_id": ids[tgt],
                }
                for tgt, lbl in n.out
            ]
        steps.append(step)

    return {
        "process_id": meta["id"],
        "name": meta["name"],
        "description": meta["description"],
        "start_step_id": ids[start.id],
        "steps": steps,
    }


def build_markdown(page: Page, process_name: str) -> str:
    nodes = page.nodes
    title = page.name if page.name not in OVERVIEW_PAGES else "Overview (call flow)"
    lines = [f"# {process_name} — {title}", ""]

    systems = sorted({n.system for n in nodes.values() if n.system})
    if systems:
        lines.append(f"**Systems used:** {', '.join(systems)}")
        lines.append("")

    ordered = sorted(nodes.values(), key=lambda n: (n.x, n.y))
    for i, n in enumerate(ordered, 1):
        prefix = f"[{n.system}] " if n.system else ""
        if n.decision:
            q = n.title.rstrip("?").strip()
            lines.append(f"{i}. **Decision — {prefix}{q}?**")
            for tgt, lbl in n.out:
                branch = lbl or "→"
                lines.append(f"   - If **{branch}**: {nodes[tgt].title}")
        else:
            lines.append(f"{i}. {prefix}{n.title}")
            if not n.out:
                lines.append("   - (end of this flow)")
    lines.append("")

    if page.legend:
        lines.append("## Options / query types")
        lines += [f"- {x}" for x in page.legend]
        lines.append("")
    if page.notes:
        lines.append("## Notes")
        lines += [f"- {x}" for x in page.notes]
        lines.append("")

    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    os.makedirs(FLOWS_DIR, exist_ok=True)
    for fname in os.listdir(ROOT):
        if not fname.endswith(".drawio.xml"):
            continue
        key = fname.replace(" AS IS.drawio.xml", "").replace(".drawio.xml", "")
        meta = PROCESSES.get(key)
        if not meta:
            print(f"!! no process mapping for {fname!r}, skipping")
            continue

        pages = parse_file(os.path.join(ROOT, fname))
        kdir = os.path.join(KNOWLEDGE_DIR, meta["id"])
        os.makedirs(kdir, exist_ok=True)

        overview = next((p for p in pages if p.name in OVERVIEW_PAGES), pages[0])
        flow = build_flow(overview, meta)
        with open(os.path.join(FLOWS_DIR, f"{meta['id']}.json"), "w", encoding="utf-8") as f:
            json.dump(flow, f, indent=2, ensure_ascii=False)
            f.write("\n")

        for page in pages:
            if not page.nodes:
                continue
            slug = "overview" if page.name in OVERVIEW_PAGES else slugify(page.name, "page")
            with open(os.path.join(kdir, f"{slug}.md"), "w", encoding="utf-8") as f:
                f.write(build_markdown(page, meta["name"]))

        n_steps = len(flow["steps"])
        n_pages = sum(1 for p in pages if p.nodes)
        print(f"{meta['id']:14s} flow: {n_steps:2d} steps  |  knowledge: {n_pages} page(s)")
        for p in pages:
            if p.nodes:
                print(f"    - {p.name:28s} {len(p.nodes):2d} nodes")


if __name__ == "__main__":
    main()
