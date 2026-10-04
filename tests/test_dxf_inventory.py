"""Synthetic DXF integration checks; skip clearly when optional ezdxf is absent."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HAS_EZDXF = importlib.util.find_spec("ezdxf") is not None
ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/inspect_dxf.py"


@unittest.skipUnless(HAS_EZDXF, "Optional ezdxf is absent; synthetic DXF integration was not run")
class DxfInventoryIntegration(unittest.TestCase):
    def test_transformed_block_inventory_and_source_protection(self):
        import ezdxf

        with tempfile.TemporaryDirectory(prefix="cad-skill-dxf-test-") as temp:
            root = Path(temp)
            source, output = root / "synthetic.dxf", root / "inventory.json"
            doc = ezdxf.new("R2010")
            doc.header["$INSUNITS"] = 4
            doc.layers.new("Reference")
            doc.layers.new("Fixtures")
            model = doc.modelspace()
            line = model.add_line((0, 0), (500, 1000), dxfattribs={"layer": "Reference"})
            block = doc.blocks.new("SIMPLE_FIXTURE")
            block.add_line((0, 0), (1000, 0))
            block.add_line((1000, 0), (1000, 400))
            inserted = model.add_blockref("SIMPLE_FIXTURE", (2000, 3000),
                                          dxfattribs={"rotation": 90, "layer": "Fixtures"})
            doc.saveas(source)
            before = source.read_bytes()
            digest = hashlib.sha256(before).hexdigest()
            result = subprocess.run([sys.executable, str(SCRIPT), str(source), "--out", str(output)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            inventory = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(inventory["source"]["sha256"], digest)
            self.assertTrue(inventory["source_unchanged"])
            self.assertEqual(source.read_bytes(), before)
            self.assertEqual(inventory["units"], {"insunits_code": 4, "label": "mm"})
            self.assertEqual(inventory["entity_counts"], {"LINE": 1, "INSERT": 1})
            self.assertTrue({"Reference", "Fixtures"}.issubset(inventory["layers"]))
            fixture = next(b for b in inventory["blocks"] if b["name"] == "SIMPLE_FIXTURE")
            self.assertEqual(fixture["entity_counts"], {"LINE": 2})
            entries = {entry["handle"]: entry for entry in inventory["modelspace_entities"]}
            self.assertEqual(entries[line.dxf.handle]["layer"], "Reference")
            self.assertEqual(entries[line.dxf.handle]["bbox_wcs"],
                             {"min": [0.0, 0.0, 0.0], "max": [500.0, 1000.0, 0.0]})
            instance = entries[inserted.dxf.handle]
            self.assertEqual(instance["block_name"], "SIMPLE_FIXTURE")
            self.assertEqual(instance["layer"], "Fixtures")
            # Local L-shape: rotate 90 degrees, then translate by (2000, 3000).
            for actual, expected in zip(instance["bbox_wcs"]["min"], (1600.0, 3000.0, 0.0)):
                self.assertAlmostEqual(actual, expected, places=7)
            for actual, expected in zip(instance["bbox_wcs"]["max"], (2000.0, 4000.0, 0.0)):
                self.assertAlmostEqual(actual, expected, places=7)
            self.assertEqual(inventory["warnings"], [])
            self.assertIn("No semantic classification", inventory["limits"][0])
            blocked = subprocess.run([sys.executable, str(SCRIPT), str(source), "--out", str(source)],
                                     capture_output=True, text=True)
            self.assertEqual(blocked.returncode, 2)
            self.assertIn("must not overwrite", blocked.stderr)
            self.assertEqual(source.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
