"""Fast dependency-free unit tests of search input handling."""
import unittest
from search_utils import (
    escaped_like_contains, normalized_module, normalized_search, valid_new_module,
)


class SearchInputTests(unittest.TestCase):
    def test_normalized_search(self):
        self.assertEqual(normalized_search("   Data Structures   "), "Data Structures")
        self.assertEqual(normalized_search(None), "")
        self.assertEqual(len(normalized_search("a" * 200)), 100)

    def test_like_wildcards_are_escaped(self):
        self.assertEqual(escaped_like_contains("100%_ready\\"), r"%100\%\_ready\\%")
        self.assertEqual(escaped_like_contains("Data Structures"), "%Data Structures%")

    def test_module_normalization(self):
        self.assertEqual(normalized_module(" csc312 "), "CSC312")
        self.assertEqual(normalized_module(None), "")

    def test_valid_new_module(self):
        self.assertTrue(valid_new_module("CSC312"))
        self.assertTrue(valid_new_module("MAT111"))
        self.assertFalse(valid_new_module(""))
        self.assertFalse(valid_new_module("CSC-312"))
        self.assertFalse(valid_new_module("UNASSIGNED"))
        self.assertFalse(valid_new_module("CSC312; DROP TABLE item"))


if __name__ == "__main__":
    unittest.main()
