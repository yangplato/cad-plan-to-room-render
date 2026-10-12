"""Exercise the distributed form library from an isolated installation."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "references/form-library"
LIBRARY_FILES = (
    "data/library.json",
    "data/taxonomy.json",
    "data/library.schema.json",
    "index.html",
    "使用说明.md",
    "辅助资料/formlib.py",
    "辅助资料/viewer.template.html",
)


class PortableFormLibraryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library = json.loads((BUNDLE / "data/library.json").read_text(encoding="utf-8"))
        cls.taxonomy = json.loads((BUNDLE / "data/taxonomy.json").read_text(encoding="utf-8"))
        cls.form = next(f for f in cls.library["forms"] if f["status"] == "verified_visual")
        cls.sources = {s["id"]: s for s in cls.library["sources"]}

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="form-library-")
        self.addCleanup(temporary.cleanup)
        self.temporary = Path(temporary.name)
        self.installation = self.temporary / "中文路径 有空格" / "插件安装" / "cad-plan-to-room-render"
        self.adapter = self.installation / "scripts/form_library.py"
        self.adapter.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / "scripts/form_library.py", self.adapter)
        self.bundled = self.installation / "references/form-library"
        self.copy_library(self.bundled)
        self.cwd = self.temporary / "另一个 工作目录"
        self.cwd.mkdir()
        self.environment = os.environ.copy()
        self.environment.pop("INTERIOR_FORM_LIBRARY_ROOT", None)
        self.environment["PYTHONIOENCODING"] = "utf-8"
        self.environment["PYTHONDONTWRITEBYTECODE"] = "1"

    def copy_library(self, destination, version=None):
        for relative in LIBRARY_FILES:
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(BUNDLE / relative, target)
        if version:
            path = destination / "data/library.json"
            library = json.loads(path.read_text(encoding="utf-8"))
            library["version"] = version
            path.write_text(json.dumps(library, ensure_ascii=False), encoding="utf-8")

    def run_adapter(self, *arguments, configured=None):
        environment = dict(self.environment)
        if configured is not None:
            environment["INTERIOR_FORM_LIBRARY_ROOT"] = str(configured)
        return subprocess.run(
            [sys.executable, str(self.adapter), *map(str, arguments)],
            cwd=self.cwd, env=environment, capture_output=True,
            text=True, encoding="utf-8", timeout=30,
        )

    def successful(self, *arguments, configured=None):
        result = self.run_adapter(*arguments, configured=configured)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_relocated_bundle_validates_without_configuration(self):
        result = self.successful("validate")
        self.assertTrue(result["valid"])
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["stats"]["form_count"], len(self.library["forms"]))
        self.assertEqual(result["stats"]["source_count"], len(self.library["sources"]))

    def test_search_preserves_actual_form_and_sources(self):
        result = self.successful(
            "search", self.form["id"], "--category", self.form["category"],
            "--room", self.form["spatial_applications"][0],
            "--style", self.form["style_tags"][0],
        )
        self.assertEqual(result["library_version"], self.library["version"])
        self.assertEqual(result["total_matches"], 1)
        found = result["results"][0]
        self.assertEqual(found["id"], self.form["id"])
        self.assertEqual(found["visual_features"], self.form["visual_features"])
        self.assertEqual(found["evidence"], self.form["evidence"])
        self.assertEqual(found["references"], [self.sources[s] for s in self.form["source_ids"]])

    def test_show_and_select_export_candidate_from_real_data(self):
        shown = self.successful("show", self.form["id"])
        self.assertEqual(shown["evidence"], self.form["evidence"])
        output = self.cwd / "本次选型.json"
        selected = self.successful(
            "select", self.form["id"], "--room", self.form["spatial_applications"][0],
            "--style", self.form["style_tags"][0], "--out", output,
        )
        self.assertEqual(selected["selection_state"], "candidate")
        self.assertEqual([f["id"] for f in selected["selected_forms"]], [self.form["id"]])
        self.assertEqual(selected["selected_forms"][0]["references"], shown["references"])
        self.assertEqual(json.loads(output.read_text(encoding="utf-8")), selected)

    def test_legacy_project_library_is_preserved(self):
        legacy = self.adapter.resolve().parents[3] / "05-室内设计造型知识库"
        self.copy_library(legacy, version="test-legacy-library")
        result = self.successful("search", self.form["id"])
        self.assertEqual(result["library_version"], "test-legacy-library")

    def test_explicit_library_overrides_legacy_and_bundle(self):
        legacy = self.adapter.resolve().parents[3] / "05-室内设计造型知识库"
        self.copy_library(legacy, version="test-legacy-library")
        external = self.temporary / "独立 外部库"
        self.copy_library(external, version="test-explicit-library")
        result = self.successful("search", self.form["id"], configured=external)
        self.assertEqual(result["library_version"], "test-explicit-library")
        self.assertEqual(result["results"][0]["id"], self.form["id"])

    def test_bad_explicit_configuration_does_not_fall_back(self):
        legacy = self.adapter.resolve().parents[3] / "05-室内设计造型知识库"
        self.copy_library(legacy, version="test-legacy-library")
        incomplete = self.temporary / "不完整 外部库"
        incomplete.mkdir()
        malformed = self.temporary / "损坏 外部库"
        self.copy_library(malformed)
        (malformed / "data/library.json").write_text("not JSON", encoding="utf-8")
        for configured in (self.temporary / "不存在的库", incomplete, malformed):
            with self.subTest(configured=configured):
                result = self.run_adapter("search", self.form["id"], configured=configured)
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertNotIn('"results":', result.stdout)
                self.assertTrue(result.stdout or result.stderr)

    def test_export_does_not_overwrite_records_or_library(self):
        existing = self.cwd / "已有选型.json"
        existing.write_text("keep this record", encoding="utf-8")
        protected = (
            existing, self.bundled / "data/library.json",
            self.bundled / "data/新报告.json", self.bundled / "index.html",
        )
        before = {path: path.read_bytes() for path in protected if path.exists()}
        for output in protected:
            with self.subTest(output=output):
                result = self.run_adapter("select", self.form["id"], "--out", output)
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                if output in before:
                    self.assertEqual(output.read_bytes(), before[output])
                else:
                    self.assertFalse(output.exists())

    def test_build_uses_bundled_template_and_embeds_current_data(self):
        data_path = self.bundled / "data/library.json"
        library = json.loads(data_path.read_text(encoding="utf-8"))
        attack = '</script><script>alert("test")</script>'
        library["forms"][0]["name_zh"] += attack
        data_path.write_text(json.dumps(library, ensure_ascii=False), encoding="utf-8")
        viewer = self.bundled / "index.html"
        viewer.write_text("outdated viewer", encoding="utf-8")
        result = self.successful("build")
        self.assertEqual(Path(result["built"]), viewer.resolve())
        html = viewer.read_text(encoding="utf-8")
        payload_match = re.search(
            r'<script id="library-data" type="application/json">(.*?)</script>', html, re.S,
        )
        self.assertIsNotNone(payload_match)
        payload = json.loads(payload_match.group(1))
        self.assertEqual(payload["library"], library)
        self.assertEqual(payload["taxonomy"], self.taxonomy)
        self.assertEqual(payload["stats"]["form_count"], len(library["forms"]))
        template = (self.bundled / "辅助资料/viewer.template.html").read_text(encoding="utf-8")
        self.assertTrue(html.startswith(template.split("__LIBRARY_PAYLOAD__")[0]))
        self.assertNotIn("__LIBRARY_PAYLOAD__", html)
        self.assertNotIn(attack, html)


if __name__ == "__main__":
    unittest.main()
