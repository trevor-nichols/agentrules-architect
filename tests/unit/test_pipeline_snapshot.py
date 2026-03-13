import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from agentrules.core.pipeline import (
    EffectiveExclusions,
    PipelineSettings,
    build_project_snapshot,
)


class BuildProjectSnapshotTests(unittest.TestCase):
    @patch("agentrules.core.pipeline.snapshot.build_project_profile")
    @patch("agentrules.core.pipeline.snapshot.collect_dependency_info")
    @patch("agentrules.core.pipeline.snapshot.get_project_tree")
    @patch("agentrules.core.pipeline.snapshot.load_gitignore_spec")
    def test_build_project_snapshot_respects_gitignore(
        self,
        mock_load_gitignore,
        mock_get_project_tree,
        mock_collect_dependency,
        mock_build_project_profile,
    ) -> None:
        with TemporaryDirectory() as tmpdir:
            target_directory = Path(tmpdir)

            settings = PipelineSettings(
                target_directory=target_directory,
                tree_max_depth=3,
                respect_gitignore=True,
                effective_exclusions=EffectiveExclusions(
                    directories=frozenset({"build"}),
                    files=frozenset({"notes.txt"}),
                    extensions=frozenset({".log"}),
                ),
                exclude_relative_paths=frozenset({"AGENTS.custom.md", "SNAPSHOT.custom.md"}),
                exclusion_overrides=None,
            )

            spec = object()
            gitignore_path = target_directory / ".gitignore"
            mock_load_gitignore.return_value = SimpleNamespace(spec=spec, path=gitignore_path)
            mock_get_project_tree.return_value = [
                "<project_structure>",
                "src/",
                "</project_structure>",
            ]
            dependency_payload = {"manifests": ["package.json"], "summary": {}}
            mock_collect_dependency.return_value = dependency_payload
            profile_payload = {"schema_version": "1.0", "detected_types": ["generic"]}
            mock_build_project_profile.return_value = profile_payload

            snapshot = build_project_snapshot(settings)

        mock_load_gitignore.assert_called_once_with(target_directory)
        mock_get_project_tree.assert_called_once()
        kwargs = mock_get_project_tree.call_args.kwargs
        self.assertEqual(kwargs["max_depth"], 3)
        self.assertEqual(kwargs["exclude_dirs"], {"build"})
        self.assertEqual(kwargs["exclude_files"], {"notes.txt"})
        self.assertEqual(kwargs["exclude_extensions"], {".log"})
        self.assertEqual(kwargs["exclude_relative_paths"], {"AGENTS.custom.md", "SNAPSHOT.custom.md"})
        self.assertIs(kwargs["gitignore_spec"], spec)

        mock_collect_dependency.assert_called_once_with(
            target_directory,
            gitignore_spec=spec,
            max_depth=3,
            exclude_relative_paths={"AGENTS.custom.md", "SNAPSHOT.custom.md"},
        )
        mock_build_project_profile.assert_called_once_with(
            target_directory=target_directory,
            dependency_info=dependency_payload,
            tree_max_depth=3,
            gitignore_spec=spec,
            exclude_dirs={"build"},
            exclude_files={"notes.txt"},
            exclude_extensions={".log"},
            exclude_relative_paths={"AGENTS.custom.md", "SNAPSHOT.custom.md"},
            explicit_exclude_files=set(),
            explicit_exclude_extensions=set(),
        )

        self.assertEqual(snapshot.tree_with_delimiters, ("<project_structure>", "src/", "</project_structure>"))
        self.assertEqual(snapshot.tree, ("src/",))
        self.assertIs(snapshot.gitignore.spec, spec)
        self.assertEqual(snapshot.gitignore.path, gitignore_path)
        self.assertEqual(snapshot.dependency_info, dependency_payload)
        self.assertEqual(snapshot.project_profile, profile_payload)

    @patch("agentrules.core.pipeline.snapshot.build_project_profile")
    @patch("agentrules.core.pipeline.snapshot.collect_dependency_info")
    @patch("agentrules.core.pipeline.snapshot.get_project_tree")
    @patch("agentrules.core.pipeline.snapshot.load_gitignore_spec")
    def test_build_project_snapshot_without_gitignore(
        self,
        mock_load_gitignore,
        mock_get_project_tree,
        mock_collect_dependency,
        mock_build_project_profile,
    ) -> None:
        with TemporaryDirectory() as tmpdir:
            target_directory = Path(tmpdir)

            settings = PipelineSettings(
                target_directory=target_directory,
                tree_max_depth=2,
                respect_gitignore=False,
                effective_exclusions=EffectiveExclusions(
                    directories=frozenset(),
                    files=frozenset(),
                    extensions=frozenset(),
                ),
                exclude_relative_paths=frozenset(),
                exclusion_overrides=None,
            )

            mock_get_project_tree.return_value = ["src/", "tests/"]
            dependency_payload = {"manifests": [], "summary": {"total": 0}}
            mock_collect_dependency.return_value = dependency_payload
            profile_payload = {"schema_version": "1.0", "detected_types": ["generic"]}
            mock_build_project_profile.return_value = profile_payload

            snapshot = build_project_snapshot(settings)

        mock_load_gitignore.assert_not_called()
        mock_get_project_tree.assert_called_once()
        kwargs = mock_get_project_tree.call_args.kwargs
        self.assertIsNone(kwargs["gitignore_spec"])
        self.assertEqual(kwargs["exclude_dirs"], set())
        self.assertEqual(kwargs["exclude_files"], set())
        self.assertEqual(kwargs["exclude_extensions"], set())
        self.assertEqual(kwargs["exclude_relative_paths"], set())

        mock_collect_dependency.assert_called_once_with(
            target_directory,
            gitignore_spec=None,
            max_depth=2,
            exclude_relative_paths=set(),
        )
        mock_build_project_profile.assert_called_once_with(
            target_directory=target_directory,
            dependency_info=dependency_payload,
            tree_max_depth=2,
            gitignore_spec=None,
            exclude_dirs=set(),
            exclude_files=set(),
            exclude_extensions=set(),
            exclude_relative_paths=set(),
            explicit_exclude_files=set(),
            explicit_exclude_extensions=set(),
        )

        self.assertEqual(snapshot.tree_with_delimiters, ("src/", "tests/"))
        self.assertEqual(snapshot.tree, ("src/", "tests/"))
        self.assertIsNone(snapshot.gitignore.spec)
        self.assertIsNone(snapshot.gitignore.path)
        self.assertEqual(snapshot.dependency_info, dependency_payload)
        self.assertEqual(snapshot.project_profile, profile_payload)


if __name__ == "__main__":
    unittest.main()
