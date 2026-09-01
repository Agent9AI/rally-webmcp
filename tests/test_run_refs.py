import unittest

from src.run_refs import (
    AmbiguousRunReferenceError,
    RunReferenceNotFoundError,
    RunReferenceResolutionError,
    candidate_prefix,
    public_ref,
    resolve,
)


class PublicReferenceTests(unittest.TestCase):
    def test_uuid_run_uses_date_and_first_uuid_component(self):
        self.assertEqual(
            public_ref("r-20260901-d3042d73-9378-4516-8e63-5960d47db896"),
            "260901-D3042D73",
        )

    def test_short_legacy_run_is_preserved(self):
        self.assertEqual(public_ref("r-20260831-abc123"), "260831-ABC123")

    def test_input_is_case_insensitive_and_output_is_canonical(self):
        self.assertEqual(public_ref("R-20260901-DeAdBeEf-AB12"), "260901-DEADBEEF")

    def test_rejects_non_string_and_malformed_run_ids(self):
        with self.assertRaises(TypeError):
            public_ref(None)
        for invalid in (
            "260901-D3042D73",
            "r-20260901",
            "r-20260901-dead_beef",
            "r-20260901-deadbeef/other",
            " r-20260901-deadbeef",
            "r-20260901-deadbeef ",
            "r-20261301-deadbeef",
            "r-19990901-deadbeef",
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                public_ref(invalid)


class CandidatePrefixTests(unittest.TestCase):
    def test_expands_compact_reference(self):
        self.assertEqual(
            candidate_prefix("260901-D3042D73"),
            "r-20260901-d3042d73",
        )

    def test_accepts_lowercase_and_canonicalizes(self):
        self.assertEqual(candidate_prefix("260831-abc123"), "r-20260831-abc123")

    def test_rejects_non_string_and_non_compact_forms(self):
        with self.assertRaises(TypeError):
            candidate_prefix(260901)
        for invalid in (
            "r-20260901-d3042d73",
            "260901",
            "260901-D3042D73-9378",
            "260901-D3042D73/other",
            " 260901-D3042D73",
            "260901-D3042D73 ",
            "260229-D3042D73",
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                candidate_prefix(invalid)


class ResolveTests(unittest.TestCase):
    UUID_RUN = "r-20260901-d3042d73-9378-4516-8e63-5960d47db896"

    def test_resolves_compact_reference_to_full_exact_id(self):
        self.assertEqual(
            resolve("260901-D3042D73", ["r-20260901-other", self.UUID_RUN]),
            self.UUID_RUN,
        )

    def test_compact_lookup_is_case_insensitive(self):
        available = "R-20260901-D3042D73-9378-4516-8E63-5960D47DB896"
        self.assertEqual(resolve("260901-d3042d73", [available]), available)

    def test_component_boundary_prevents_overmatching(self):
        with self.assertRaises(RunReferenceNotFoundError):
            resolve("260901-ABC123", ["r-20260901-abc1234-rest"])

    def test_accepts_legacy_full_id_and_matches_it_exactly(self):
        exact = "r-20260831-abc123"
        sibling = "r-20260831-abc123-more"
        self.assertEqual(resolve("R-20260831-ABC123", [exact, sibling]), exact)

    def test_missing_reference_raises_custom_error(self):
        with self.assertRaises(RunReferenceResolutionError) as raised:
            resolve("260901-DEADBEEF", [self.UUID_RUN])
        self.assertIsInstance(raised.exception, RunReferenceNotFoundError)

    def test_shared_public_prefix_is_explicitly_ambiguous(self):
        first = "r-20260901-deadbeef-1111-2222"
        second = "r-20260901-deadbeef-aaaa-bbbb"
        self.assertEqual(public_ref(first), public_ref(second))
        with self.assertRaises(RunReferenceResolutionError) as raised:
            resolve("260901-DEADBEEF", [first, second])
        self.assertIsInstance(raised.exception, AmbiguousRunReferenceError)

    def test_exact_and_extended_prefix_are_ambiguous_for_compact_form(self):
        with self.assertRaises(AmbiguousRunReferenceError):
            resolve(
                "260831-ABC123",
                ["r-20260831-abc123", "r-20260831-abc123-more"],
            )

    def test_duplicate_identical_entries_count_as_one_run(self):
        self.assertEqual(resolve("260901-D3042D73", [self.UUID_RUN] * 2), self.UUID_RUN)

    def test_ignores_entries_that_are_not_valid_run_ids(self):
        available = (item for item in [None, "README", "../escape", self.UUID_RUN])
        self.assertEqual(resolve("260901-D3042D73", available), self.UUID_RUN)

    def test_invalid_reference_syntax_is_not_treated_as_missing(self):
        with self.assertRaises(ValueError):
            resolve("260901-D3042D73-extra", [self.UUID_RUN])


if __name__ == "__main__":
    unittest.main()
