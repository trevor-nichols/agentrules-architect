import unittest

from agentrules.core.utils.execplan_identity import (
    matches_execplan_filename_policy,
    parse_execplan_filename,
)


class ExecPlanIdentityTests(unittest.TestCase):
    def test_parse_accepts_plain_markdown_filename(self) -> None:
        parsed = parse_execplan_filename("EP-20260207-001.md")
        self.assertEqual(parsed, ("EP-20260207-001", "20260207", 1))

    def test_parse_accepts_slug_suffix_filename(self) -> None:
        parsed = parse_execplan_filename("EP-20260207-001_auth-refresh.md")
        self.assertEqual(parsed, ("EP-20260207-001", "20260207", 1))

    def test_parse_rejects_non_boundary_suffix(self) -> None:
        self.assertIsNone(parse_execplan_filename("EP-20260207-001x.md"))

    def test_filename_policy_accepts_documented_variants(self) -> None:
        valid_names = (
            "EP-20260207-001.md",
            "EP-20260207-001_auth-refresh.md",
            "EP-20260207-001-auth-refresh.md",
        )
        for filename in valid_names:
            self.assertTrue(matches_execplan_filename_policy(filename), msg=filename)

    def test_filename_policy_rejects_non_documented_variants(self) -> None:
        invalid_names = (
            "EP-20260207-001",
            "EP-20260207-001.other.md",
            "EP-20260207-001__bad!.md",
        )
        for filename in invalid_names:
            self.assertFalse(matches_execplan_filename_policy(filename), msg=filename)


if __name__ == "__main__":
    unittest.main()
