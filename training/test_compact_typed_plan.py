import unittest

from compact_typed_plan import CompactPlanError, parse_compact_output, serialize_compact
from prompt_contract_v2_migrate import build_v2_target


class CompactTypedPlanTests(unittest.TestCase):
    def setUp(self):
        self.rendered = build_v2_target("A fact. Do the task.", ["A fact.", "Do the task."], ["Do the task."])
        self.lines = ["1F|B1|N,B1", "2T|B2|N,B2,A1"]

    def test_round_trip(self):
        parsed = parse_compact_output(serialize_compact(self.lines, self.rendered))
        self.assertEqual(parsed.rendered_text, self.rendered)
        self.assertEqual(len(parsed.propositions), 2)

    def assert_bad(self, lines):
        with self.assertRaises(CompactPlanError):
            serialize_compact(lines, self.rendered)

    def test_rejects_missing_action_coverage(self): self.assert_bad(["1F|B1|N,B1", "2T|B2|N,B2"])
    def test_rejects_duplicate_action_coverage(self): self.assert_bad(["1T|B1|N,B1,A1", "2T|B2|N,B2,A1"])
    def test_rejects_action_on_fact(self): self.assert_bad(["1F|B1|N,B1,A1", "2T|B2|N,B2"])
    def test_rejects_out_of_range_ref(self): self.assert_bad(["1F|B9|N,B9", "2T|B2|N,B2,A1"])
    def test_rejects_unknown_state(self): self.assert_bad(["1X|B1|N,B1", "2T|B2|N,B2,A1"])
    def test_rejects_forward_duplicate(self): self.assert_bad(["1F|B1|N,B1|D:2", "2T|B2|N,B2,A1"])
    def test_rejects_unknown_role(self): self.assert_bad(["1F|B1|N,B1|R:x=value", "2T|B2|N,B2,A1"])
    def test_rejects_unknown_qualifier(self): self.assert_bad(["1F|B1|N,B1|Q:x=value", "2T|B2|N,B2,A1"])
    def test_rejects_invalid_coreference(self): self.assert_bad(["1F|B1|N,B1|C:maybe", "2T|B2|N,B2,A1"])


if __name__ == "__main__": unittest.main()
