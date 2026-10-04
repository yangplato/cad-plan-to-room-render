from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/scene_tools.py"
spec = importlib.util.spec_from_file_location("scene_tools", SCRIPT)
tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tools)
EXAMPLE = json.loads((ROOT / "examples/synthetic-scene.json").read_text(encoding="utf-8"))
NS = {"s": "http://www.w3.org/2000/svg"}


class SceneChecks(unittest.TestCase):
    def setUp(self):
        self.scene = deepcopy(EXAMPLE)

    def test_example_unknown_category_is_preserved(self):
        errors, warnings = tools.validate_scene(self.scene)
        self.assertEqual(errors, [])
        self.assertTrue(any("unidentified_fixture" in w for w in warnings))
        svg = ET.fromstring(tools.render_svg(self.scene))
        unknown = next(x for x in svg.findall("s:path", NS) if x.get("data-id") == "U1")
        self.assertEqual(unknown.get("data-category"), "unidentified_fixture")
        self.assertIn("stroke-dasharray", unknown.attrib)
        self.assertIn("4000", unknown.get("d"))  # Concave contour is not replaced by a box.

    def test_far_coordinates_dynamic_viewbox_and_holes(self):
        shift = (1500000, -900000)
        for wall in self.scene["walls"]:
            for ring in [wall["outer_mm"], *wall["holes_mm"]]:
                for p in ring:
                    p[0] += shift[0]
                    p[1] += shift[1]
        for opening in self.scene["openings"]:
            for key in ("a_mm", "b_mm"):
                opening[key] = [opening[key][i] + shift[i] for i in range(2)]
        for obj in self.scene["objects"]:
            obj["footprint_mm"] = [[p[i] + shift[i] for i in range(2)] for p in obj["footprint_mm"]]
        svg = ET.fromstring(tools.render_svg(self.scene))
        x, y, w, h = map(float, svg.get("viewBox").split())
        for wall in self.scene["walls"]:
            for px, py in wall["outer_mm"]:
                self.assertTrue(x < px < x + w and y < -py < y + h)
        wall = next(n for n in svg.findall("s:path", NS) if n.get("data-id") == "W1")
        self.assertEqual(wall.get("fill-rule"), "evenodd")
        self.assertEqual(wall.get("d").count("M "), 2)
        self.assertEqual(wall.get("d").count(" Z"), 2)

    def test_units_duplicate_id_bad_direction_and_nan_rejected(self):
        edits = [lambda s: s.update(units="px"),
                 lambda s: s["objects"][0].update(id="W1"),
                 lambda s: s["objects"][0].update(front_vector=[0, 0]),
                 lambda s: s["walls"][0]["outer_mm"][0].__setitem__(0, float("nan")),
                 lambda s: s["objects"][0]["footprint_mm"][0].__setitem__(1, True),
                 lambda s: s.update(title="invalid\u0000text"),
                 lambda s: s.update(source=None)]
        for edit in edits:
            with self.subTest(edit=edit):
                scene = deepcopy(EXAMPLE)
                edit(scene)
                self.assertTrue(tools.validate_scene(scene)[0])
                with self.assertRaises(ValueError):
                    tools.render_svg(scene)

    def test_json_nonfinite_duplicate_keys_and_exponent_overflow(self):
        for raw in (b'{"x":NaN}', b'{"x":Infinity}', b'{"x":-Infinity}', b'{"x":1,"x":2}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                tools.parse_scene(raw)
        raw = json.dumps(self.scene).replace('"height_mm": 2700', '"height_mm": 1e999').encode()
        self.assertTrue(tools.validate_scene(tools.parse_scene(raw))[0])

    def test_source_hash_change_and_report_scene_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "original.dxf"
            source.write_bytes(b"synthetic fixture, not a DXF")
            self.scene["source"] = {"kind": "dxf", "filename": source.name,
                                      "sha256": tools.file_sha256(source)}
            digest = hashlib.sha256(json.dumps(self.scene).encode()).hexdigest()
            report = tools.make_report(self.scene, digest, source)
            self.assertTrue(report["valid"])
            self.assertEqual(report["scene_sha256"], digest)
            self.assertEqual(report["checks"]["source_hash"]["status"], "passed")
            source.write_bytes(b"changed source")
            report = tools.make_report(self.scene, digest, source)
            self.assertFalse(report["valid"])
            self.assertEqual(report["checks"]["source_hash"]["status"], "failed")

    def test_report_unperformed_checks_are_not_checked(self):
        report = tools.make_report(self.scene, "a" * 64)
        for key in ("polygon_topology", "wall_object_collision", "room_connectivity", "semantic_classification", "construction_accuracy"):
            self.assertEqual(report["checks"][key], "not_checked")
        self.assertEqual(report["checks"]["source_hash"]["status"], "not_checked")
        self.scene["source"] = None
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(tools.make_report(self.scene, "b" * 64, Path(tmp) / "missing")["valid"])

    def test_xml_text_and_attributes_are_escaped(self):
        attack = '<script>alert("x")</script> & "quoted"'
        self.scene["title"] = attack
        self.scene["objects"][0].update(id=attack, name=attack, category=attack)
        rendered = tools.render_svg(self.scene)
        svg = ET.fromstring(rendered)
        self.assertEqual(svg.find("s:title", NS).text, attack)
        self.assertEqual(svg.findall(".//s:script", NS), [])
        self.assertNotIn("<script>", rendered)
        node = next(x for x in svg.findall("s:path", NS) if x.get("data-id") == attack)
        self.assertEqual(node.get("data-category"), attack)

    def test_cli_roundtrip_output_protection_and_source_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scene = root / "scene.json"
            raw = json.dumps(self.scene).encode()
            scene.write_bytes(raw)
            output, report = root / "plan.svg", root / "report.json"

            def run(*args):
                return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True)

            result = run("render", scene, "--out", output, "--report", report)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result_report = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(result_report["scene_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(result_report["rendered_svg_sha256"], tools.file_sha256(output))
            self.assertEqual(run("render", scene, "--out", scene).returncode, 2)
            self.assertEqual(scene.read_bytes(), raw)
            self.assertEqual(run("render", scene, "--out", output, "--report", output).returncode, 2)
            self.scene["source"] = {"kind": "dxf", "filename": "original.dxf", "sha256": "0" * 64}
            scene.write_text(json.dumps(self.scene), encoding="utf-8")
            original = root / "original.dxf"
            original.write_bytes(b"different bytes")
            blocked = root / "blocked.svg"
            self.assertEqual(run("render", scene, "--source", original, "--out", blocked).returncode, 2)
            self.assertFalse(blocked.exists())
            self.assertEqual(run("validate", scene, "--report", original, "--source", original).returncode, 2)
            self.assertEqual(original.read_bytes(), b"different bytes")

    def test_hardlink_and_symlink_cannot_overwrite_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.json"
            source.write_text("original", encoding="utf-8")
            for name, method in (("hard", os.link), ("sym", os.symlink)):
                target = Path(tmp) / name
                method(source, target)
                with self.assertRaises(ValueError):
                    tools.guard_output(target, [source])


if __name__ == "__main__":
    unittest.main()
