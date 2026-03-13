import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentrules.core.pipeline.project_profile import build_project_profile


class ProjectProfileTests(unittest.TestCase):
    def test_detects_nextjs_frontend_styling_signals(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "package.json").write_text(
                '{"dependencies":{"next":"14.2.0","react":"18.3.0","tailwindcss":"3.4.0"}}',
                encoding="utf-8",
            )
            (root / "next.config.ts").write_text("export default {};\n", encoding="utf-8")
            (root / "tailwind.config.js").write_text("module.exports = {};\n", encoding="utf-8")
            (root / "src").mkdir(parents=True, exist_ok=True)
            (root / "src" / "styles").mkdir(parents=True, exist_ok=True)
            (root / "src" / "styles" / "globals.css").write_text(":root {}\n", encoding="utf-8")

            dependency_info = {
                "summary": {"npm": [str(root / "package.json")]},
                "manifests": [
                    {
                        "path": str(root / "package.json"),
                        "type": "package_json",
                        "manager": "npm",
                        "data": {
                            "dependencies": {
                                "next": "14.2.0",
                                "react": "18.3.0",
                                "tailwindcss": "3.4.0",
                            }
                        },
                    }
                ],
            }

            profile = build_project_profile(
                target_directory=root,
                dependency_info=dependency_info,
                tree_max_depth=5,
                gitignore_spec=None,
                exclude_dirs=set(),
                exclude_files=set(),
                exclude_extensions=set(),
                exclude_relative_paths=set(),
            )

        self.assertEqual(profile["schema_version"], "1.0")
        self.assertIn("frontend-web", profile["detected_types"])
        self.assertIn("frontend-nextjs", profile["detected_types"])
        self.assertNotIn("generic", profile["detected_types"])

        frontend = profile["frontend"]
        self.assertTrue(frontend["detected"])
        self.assertIn("nextjs", frontend["frameworks"])
        self.assertIn("react", frontend["frameworks"])
        self.assertIn("tailwindcss", frontend["styling_systems"])
        self.assertIn("css", frontend["styling_systems"])
        self.assertGreaterEqual(frontend["style_file_count"], 1)
        self.assertIn("next.config.ts", frontend["signal_files"])
        self.assertIn("tailwind.config.js", frontend["signal_files"])

        ecosystem = profile["ecosystem"]
        self.assertIn("npm", ecosystem["dependency_managers"])
        self.assertIn("package_json", ecosystem["manifest_types"])
        self.assertIn("package.json", ecosystem["manifest_paths"])

    def test_detects_python_packaging_and_tooling_signals(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
            (root / "requirements-dev.txt").write_text("pytest==8.3.0\n", encoding="utf-8")
            (root / "Makefile").write_text("test:\n\tpytest\n", encoding="utf-8")
            (root / "justfile").write_text("test:\n pytest\n", encoding="utf-8")
            (root / "tox.ini").write_text("[tox]\nenvlist = py311\n", encoding="utf-8")

            dependency_info = {
                "summary": {
                    "python": [str(root / "pyproject.toml")],
                    "pip": [str(root / "requirements-dev.txt")],
                },
                "manifests": [
                    {
                        "path": str(root / "pyproject.toml"),
                        "type": "pyproject.toml",
                        "manager": "python",
                        "data": {"project": ["pytest"]},
                    }
                ],
            }

            profile = build_project_profile(
                target_directory=root,
                dependency_info=dependency_info,
                tree_max_depth=5,
                gitignore_spec=None,
                exclude_dirs=set(),
                exclude_files=set(),
                exclude_extensions=set(),
                exclude_relative_paths=set(),
            )

        self.assertIn("python", profile["detected_types"])
        python_profile = profile["python"]
        self.assertTrue(python_profile["detected"])
        self.assertIn("pyproject.toml", python_profile["packaging_files"])
        self.assertIn("requirements-dev.txt", python_profile["packaging_files"])
        self.assertIn("Makefile", python_profile["task_runner_files"])
        self.assertIn("justfile", python_profile["task_runner_files"])
        self.assertIn("tox.ini", python_profile["tooling_files"])
        self.assertEqual(set(python_profile["managers"]), {"pip", "python"})

    def test_returns_generic_profile_when_no_signals_exist(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "main.txt").write_text("hello\n", encoding="utf-8")

            profile = build_project_profile(
                target_directory=root,
                dependency_info={"summary": {}, "manifests": []},
                tree_max_depth=5,
                gitignore_spec=None,
                exclude_dirs=set(),
                exclude_files=set(),
                exclude_extensions=set(),
                exclude_relative_paths=set(),
            )

        self.assertEqual(profile["detected_types"], ["generic"])
        self.assertFalse(profile["frontend"]["detected"])
        self.assertFalse(profile["python"]["detected"])

    def test_respects_exclude_relative_paths_when_collecting_signals(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "next.config.ts").write_text("export default {};\n", encoding="utf-8")

            profile = build_project_profile(
                target_directory=root,
                dependency_info={"summary": {}, "manifests": []},
                tree_max_depth=5,
                gitignore_spec=None,
                exclude_dirs=set(),
                exclude_files=set(),
                exclude_extensions=set(),
                exclude_relative_paths={"next.config.ts"},
            )

        self.assertEqual(profile["detected_types"], ["generic"])
        self.assertEqual(profile["frontend"]["signal_files"], [])


if __name__ == "__main__":
    unittest.main()
