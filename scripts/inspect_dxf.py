#!/usr/bin/env python3
"""Read-only DXF entity inventory. No wall, room or furniture classification."""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import sys

from scene_tools import file_sha256, guard_output, write_text


def inspect(path):
    # The scene validator/SVG renderer does not need this optional dependency.
    try:
        import ezdxf
        from ezdxf import bbox
    except ImportError as exc:
        raise ValueError("Optional DXF inventory requires ezdxf in this Python environment. "
                         "Install it only if DXF inspection is needed; image/PDF and scene tools do not require it.") from exc
    before = file_sha256(path)
    doc = ezdxf.readfile(path)
    entries, warnings = [], []
    for entity in doc.modelspace():
        entry = {"handle": entity.dxf.handle, "type": entity.dxftype(), "layer": entity.dxf.layer}
        if entity.dxftype() == "INSERT":
            entry["block_name"] = entity.dxf.name
        try:
            bounds = bbox.extents([entity])
            if bounds.has_data:
                values = [float(x) for p in (bounds.extmin, bounds.extmax) for x in p]
                if all(math.isfinite(x) for x in values):
                    entry["bbox_wcs"] = {"min": values[:3], "max": values[3:]}
                else:
                    warnings.append(f"{entry['handle']}: non-finite extents omitted")
            else:
                warnings.append(f"{entry['handle']}: no supported finite extents")
        except Exception as exc:
            # Unsupported CAD entities stay in the inventory with an explicit gap.
            warnings.append(f"{entry['handle']}: extents unavailable ({type(exc).__name__})")
        entries.append(entry)
    after = file_sha256(path)
    if before != after:
        raise ValueError("Source changed during inspection; retry against a stable original")
    code = doc.header.get("$INSUNITS", 0)
    return {
        "inventory_schema": "cad-plan-dxf-inventory/1.0",
        "source": {"kind": "dxf", "filename": Path(path).name, "sha256": before},
        "units": {"insunits_code": code, "label": {0: "unspecified", 1: "inches", 2: "feet",
            3: "miles", 4: "mm", 5: "cm", 6: "m", 7: "km"}.get(code, "unmapped; inspect DXF unit code")},
        "ezdxf_version": ezdxf.__version__, "source_unchanged": True,
        "entity_counts": dict(Counter(e["type"] for e in entries)),
        "layers": [layer.dxf.name for layer in doc.layers],
        "blocks": [{"name": block.name, "entity_counts": dict(Counter(e.dxftype() for e in block))}
                   for block in doc.blocks],
        "modelspace_entities": entries, "warnings": warnings,
        "limits": ["No semantic classification; a block name is only a source label.",
                   "Bounding boxes may be approximations or unavailable for unsupported entities.",
                   "No unit conversion, DWG conversion, collision, connectivity or construction validation.",
                   "Modelspace is inventoried; layouts, external references and hidden content require separate review."],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dxf", type=Path)
    parser.add_argument("--out", type=Path, help="JSON output; omit to print to stdout")
    args = parser.parse_args(argv)
    try:
        if args.out is not None:
            guard_output(args.out, [args.dxf])
        result = inspect(args.dxf)
        message = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if args.out is not None:
            write_text(args.out, message)
            print(json.dumps({"written": str(args.out), "source_sha256": result["source"]["sha256"]}, ensure_ascii=False))
        else:
            print(message, end="")
        return 0
    except Exception as exc:
        print(f"DXF inventory failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
