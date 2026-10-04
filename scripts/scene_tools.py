#!/usr/bin/env python3
"""Validate reviewed plan facts and draw an SVG. No CAD semantic recognition."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
import xml.etree.ElementTree as ET

SCHEMA = "cad-plan-scene/1.0"
OBJECT_CATEGORIES = {
    "bed", "sofa", "chair", "armchair", "table", "dining_table", "coffee_table",
    "wardrobe", "cabinet", "counter", "basin", "sink", "toilet", "squat_toilet",
    "shower", "washer", "fridge", "stove", "plant", "unknown",
}
OPENING_CATEGORIES = {"door", "window", "opening", "sliding_door", "unknown"}


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_scene(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    def invalid_constant(value):
        raise ValueError(f"Non-finite JSON number: {value}")

    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                      parse_constant=invalid_constant)


def validate_scene(scene):
    """Structural checks only; preserve unknown semantic categories."""
    errors, warnings = [], []

    def finite_tree(value, where):
        if isinstance(value, float) and not math.isfinite(value):
            errors.append(f"{where}: number must be finite")
        elif isinstance(value, str) and any(not (c in "\t\n\r" or 0x20 <= ord(c) <= 0xD7FF
                                               or 0xE000 <= ord(c) <= 0xFFFD
                                               or 0x10000 <= ord(c) <= 0x10FFFF) for c in value):
            errors.append(f"{where}: text contains characters forbidden in XML")
        elif isinstance(value, dict):
            for key, child in value.items():
                finite_tree(child, f"{where}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                finite_tree(child, f"{where}[{index}]")

    def number(value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False
        try:
            return math.isfinite(value)
        except OverflowError:
            return False

    def point(value, where):
        ok = isinstance(value, list) and len(value) == 2 and all(number(n) for n in value)
        if not ok:
            errors.append(f"{where}: expected two finite numbers [x, y]")
        return ok

    def ring(value, where):
        if not isinstance(value, list) or len(value) < 3:
            errors.append(f"{where}: expected at least three points")
            return
        if all([point(p, f"{where}[{i}]") for i, p in enumerate(value)]):
            if len({tuple(p) for p in value}) < 3:
                errors.append(f"{where}: expected three distinct points")
            # Translate before computing area to reduce far-coordinate cancellation.
            ox, oy = value[0]
            pts = [(x - ox, y - oy) for x, y in value]
            area2 = sum(a[0] * b[1] - b[0] * a[1]
                        for a, b in zip(pts, pts[1:] + pts[:1]))
            if not number(area2) or abs(area2) <= 1e-9:
                errors.append(f"{where}: non-finite or zero signed area")

    if not isinstance(scene, dict):
        return ["Scene must be a JSON object"], []
    finite_tree(scene, "scene")
    if scene.get("schema") != SCHEMA:
        errors.append(f"schema must be {SCHEMA}")
    if scene.get("units") != "mm":
        errors.append("units must be mm; do not label pixels or unknown dimensions as millimetres")
    if scene.get("coordinates") != {"x": "right", "y": "up", "z": "up"}:
        errors.append('coordinates must be {"x":"right","y":"up","z":"up"}')
    if not isinstance(scene.get("title"), str) or not scene["title"].strip():
        errors.append("title must be a non-empty string")
    source = scene.get("source")
    if not isinstance(source, dict):
        errors.append("source must be an object")
    else:
        if not isinstance(source.get("kind"), str) or not source["kind"].strip():
            errors.append("source.kind must describe the input, e.g. dxf, pdf, image or synthetic")
        supplied_hash = source.get("sha256")
        if source.get("kind") != "synthetic" or supplied_hash is not None:
            if not isinstance(supplied_hash, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", supplied_hash):
                errors.append("source.sha256 must be a 64-digit SHA-256 hash")
            if not isinstance(source.get("filename"), str) or not source["filename"].strip():
                errors.append("source.filename must be a non-empty string")
        else:
            warnings.append("Synthetic example has no source hash; it cannot prove source identity")
    for key in ("assumptions", "unresolved"):
        if not isinstance(scene.get(key), list) or not all(isinstance(x, str) for x in scene[key]):
            errors.append(f"{key} must be a list of strings")

    ids = set()
    for group in ("walls", "openings", "objects"):
        items = scene.get(group)
        if not isinstance(items, list):
            errors.append(f"{group} must be a list")
            continue
        for index, item in enumerate(items):
            where = f"{group}[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{where}: expected an object")
                continue
            identity = item.get("id")
            if not isinstance(identity, str) or not identity.strip():
                errors.append(f"{where}.id: expected a non-empty string")
            elif identity in ids:
                errors.append(f"Duplicate ID across scene: {identity}")
            else:
                ids.add(identity)
            if not isinstance(item.get("basis"), str) or not item["basis"].strip():
                errors.append(f"{where}.basis: describe how this geometry/classification was obtained")
            if "name" in item and not isinstance(item["name"], str):
                errors.append(f"{where}.name: expected a string")
            if "height_mm" in item and (not number(item["height_mm"]) or item["height_mm"] <= 0):
                errors.append(f"{where}.height_mm: expected a positive finite number")
            if "height_mm" in item and (not isinstance(item.get("height_basis"), str) or not item["height_basis"].strip()):
                errors.append(f"{where}.height_basis: distinguish measured height from design completion")
            if group == "walls":
                ring(item.get("outer_mm"), f"{where}.outer_mm")
                holes = item.get("holes_mm", [])
                if not isinstance(holes, list):
                    errors.append(f"{where}.holes_mm: expected a list of rings")
                else:
                    for j, hole in enumerate(holes):
                        ring(hole, f"{where}.holes_mm[{j}]")
                continue
            known = OBJECT_CATEGORIES if group == "objects" else OPENING_CATEGORIES
            category = item.get("category")
            if not isinstance(category, str) or not category.strip():
                errors.append(f"{where}.category: expected a non-empty string")
            elif category not in known or category == "unknown":
                warnings.append(f"{identity}: unknown category {category!r}; geometry retained, review required")
            if group == "objects":
                ring(item.get("footprint_mm"), f"{where}.footprint_mm")
                front = item.get("front_vector")
                if front is None:
                    warnings.append(f"{identity}: functional front is unspecified")
                elif point(front, f"{where}.front_vector"):
                    magnitude = math.hypot(*front)
                    if not math.isfinite(magnitude) or magnitude <= 1e-12:
                        errors.append(f"{where}.front_vector: expected a finite non-zero direction")
            else:
                a_ok = point(item.get("a_mm"), f"{where}.a_mm")
                b_ok = point(item.get("b_mm"), f"{where}.b_mm")
                if a_ok and b_ok and item["a_mm"] == item["b_mm"]:
                    errors.append(f"{where}: opening endpoints must differ")
                if "thickness_mm" in item and (not number(item["thickness_mm"]) or item["thickness_mm"] <= 0):
                    errors.append(f"{where}.thickness_mm: expected a positive finite number")
    if not any(isinstance(scene.get(k), list) and scene[k] for k in ("walls", "openings", "objects")):
        errors.append("Scene has no drawable geometry")
    return errors, warnings


def make_report(scene, scene_hash, source_path=None):
    errors, warnings = validate_scene(scene)
    structural_valid = not errors
    source_check = {"status": "not_checked", "reason": "No source file supplied"}
    if source_path is not None:
        source = scene.get("source") if isinstance(scene, dict) else None
        expected = source.get("sha256") if isinstance(source, dict) else None
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected):
            errors.append("Cannot check source without a valid recorded source.sha256")
            source_check = {"status": "failed", "reason": "Recorded hash missing or invalid"}
        else:
            try:
                actual = file_sha256(source_path)
                matched = actual == expected.lower()
                source_check = {"status": "passed" if matched else "failed", "actual_sha256": actual}
                if not matched:
                    errors.append("Source SHA-256 mismatch; review the new source and remap, do not replace only the hash")
            except OSError as exc:
                errors.append(f"Cannot read source: {exc}")
                source_check = {"status": "failed", "reason": "Source file unreadable"}
    return {
        "report_schema": "cad-plan-checks/1.0", "scene_sha256": scene_hash,
        "valid": not errors, "errors": errors, "warnings": warnings,
        "checks": {"structure": "passed" if structural_valid else "failed",
                   "source_hash": source_check, "polygon_topology": "not_checked",
                   "wall_object_collision": "not_checked", "room_connectivity": "not_checked",
                   "semantic_classification": "not_checked", "construction_accuracy": "not_checked"},
    }


def render_svg(scene):
    errors, _ = validate_scene(scene)
    if errors:
        raise ValueError("Invalid scene: " + "; ".join(errors))
    points = []
    for wall in scene["walls"]:
        points.extend(wall["outer_mm"])
        for hole in wall.get("holes_mm", []):
            points.extend(hole)
    for opening in scene["openings"]:
        points.extend([opening["a_mm"], opening["b_mm"]])
    for obj in scene["objects"]:
        points.extend(obj["footprint_mm"])
    xs, ys = zip(*points)
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    span = max(x1 - x0, y1 - y0, 1)
    margin = span * .12
    width, height = x1 - x0 + margin * 2, y1 - y0 + margin * 2
    if not all(math.isfinite(n) and n > 0 for n in (span, margin, width, height)):
        raise ValueError("Coordinate extent is too large to render safely")
    f = lambda n: format(n, ".17g")
    root = ET.Element("svg", {"xmlns": "http://www.w3.org/2000/svg", "role": "img",
        "aria-labelledby": "diagram-title diagram-description",
        "viewBox": " ".join(map(f, (x0 - margin, -y1 - margin, width, height))),
        "width": "1600", "height": str(max(240, min(2400, round(1600 * height / width))))})
    ET.SubElement(root, "title", {"id": "diagram-title"}).text = scene["title"]
    ET.SubElement(root, "desc", {"id": "diagram-description"}).text = (
        "Reviewed input diagram. Millimetres; x right, y up. Arrows show functional front. "
        "Not an automatic CAD classification, collision, connectivity or construction check.")
    ET.SubElement(root, "rect", {"x": f(x0 - margin), "y": f(-y1 - margin),
        "width": f(width), "height": f(height), "fill": "white"})

    def path(rings):
        return " ".join("M " + " L ".join(f(x) + " " + f(-y) for x, y in ring) + " Z" for ring in rings)

    def line(a, b, color, stroke):
        return ET.SubElement(root, "line", {"x1": f(a[0]), "y1": f(-a[1]),
            "x2": f(b[0]), "y2": f(-b[1]), "stroke": color, "stroke-width": f(stroke)})

    for wall in scene["walls"]:
        node = ET.SubElement(root, "path", {"d": path([wall["outer_mm"], *wall.get("holes_mm", [])]),
            "data-id": wall["id"], "fill": "#9b9f9c", "fill-rule": "evenodd",
            "stroke": "#454f49", "stroke-width": f(span * .0015)})
        ET.SubElement(node, "title").text = wall.get("name", wall["id"])
    for opening in scene["openings"]:
        color = "#3383ac" if opening["category"] == "window" else "#a86b2d"
        node = line(opening["a_mm"], opening["b_mm"], color, span * .007)
        node.set("data-id", opening["id"])
        ET.SubElement(node, "title").text = opening.get("name", opening["id"]) + " — " + opening["category"]
    for obj in scene["objects"]:
        pts = obj["footprint_mm"]
        known = obj["category"] in OBJECT_CATEGORIES and obj["category"] != "unknown"
        node = ET.SubElement(root, "path", {"d": path([pts]), "data-id": obj["id"],
            "data-category": obj["category"], "fill": "#e9eee7" if known else "#f4f4f4",
            "stroke": "#50634f", "stroke-width": f(span * .002)})
        if not known:
            node.set("stroke-dasharray", f(span * .01) + " " + f(span * .006))
        ET.SubElement(node, "title").text = obj.get("name", obj["id"]) + " — " + obj["category"]
        cx = (min(p[0] for p in pts) + max(p[0] for p in pts)) / 2
        cy = (min(p[1] for p in pts) + max(p[1] for p in pts)) / 2
        label = ET.SubElement(root, "text", {"x": f(cx), "y": f(-cy), "text-anchor": "middle",
            "font-size": f(span * .014), "font-family": "sans-serif", "fill": "#253d2c"})
        label.text = obj["id"] + (" ?" if not known else "")
        if obj.get("front_vector") is not None:
            vx, vy = obj["front_vector"]
            norm = math.hypot(vx, vy)
            ux, uy = vx / norm, vy / norm
            length = min(max(p[0] for p in pts) - min(p[0] for p in pts),
                         max(p[1] for p in pts) - min(p[1] for p in pts)) * .3
            tip = (cx + ux * length, cy + uy * length)
            line((cx, cy), tip, "#274c3c", span * .002)
            for side in (-1, 1):
                line(tip, (tip[0] - ux * length * .3 + side * uy * length * .17,
                           tip[1] - uy * length * .3 - side * ux * length * .17), "#274c3c", span * .002)
    return ET.tostring(root, encoding="unicode", xml_declaration=False) + "\n"


def guard_output(path, protected):
    path = Path(path)
    for source in (Path(p) for p in protected if p is not None):
        if path.resolve() == source.resolve() or (path.exists() and source.exists() and path.samefile(source)):
            raise ValueError(f"Output must not overwrite an input or another output: {path}")


def write_text(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".scene-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "check-source", "render"):
        sub = subs.add_parser(command)
        sub.add_argument("scene", type=Path)
        if command == "check-source":
            sub.add_argument("source", type=Path)
        else:
            sub.add_argument("--source", type=Path)
        if command == "render":
            sub.add_argument("--out", type=Path, required=True)
        sub.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    digest = None
    try:
        protected = [args.scene, args.source]
        output = getattr(args, "out", None)
        if output is not None:
            guard_output(output, protected)
        if args.report is not None:
            guard_output(args.report, protected + [output])
        raw = args.scene.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        scene = parse_scene(raw)
        report = make_report(scene, digest, args.source)
        if args.command == "render" and report["valid"]:
            svg = render_svg(scene)
            write_text(output, svg)
            report["rendered_svg_sha256"] = hashlib.sha256(svg.encode("utf-8")).hexdigest()
        message = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if args.report is not None:
            write_text(args.report, message)
        print(message, end="")
        return 0 if report["valid"] else 2
    except (OSError, UnicodeError, ValueError, OverflowError, RecursionError) as exc:
        print(json.dumps({"valid": False, "scene_sha256": digest, "errors": [str(exc)]},
                         ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())
