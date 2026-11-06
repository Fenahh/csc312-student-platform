"""Run the search SQL pattern with Python's built-in sqlite3.

This verifies SQL matching semantics, NOT the Flask/SQLAlchemy HTTP integration.
"""
import sqlite3
import unittest

from search_utils import escaped_like_contains, normalized_module


class SQLiteSearchContractTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute("CREATE TABLE item (title TEXT, description TEXT, module_code TEXT)")
        self.conn.executemany("INSERT INTO item VALUES (?, ?, ?)", [
            ("Data Structures Summary", "Linked lists and trees", "CSC312"),
            ("Statistics Notes", "Probability distributions", "STA222"),
            ("Exam Techniques", "Data structures revision", "CSC211"),
            ("Review 100%", "How to study", "MAT111"),
        ])

    def tearDown(self):
        self.conn.close()

    def search(self, q="", module=""):
        where = []
        params = []
        if q:
            where.append("(lower(title) LIKE lower(?) ESCAPE '\\' "
                         "OR lower(description) LIKE lower(?) ESCAPE '\\' "
                         "OR lower(module_code) LIKE lower(?) ESCAPE '\\')")
            params.extend([escaped_like_contains(q)] * 3)
        if module:
            where.append("module_code = ?")
            params.append(normalized_module(module))
        query = "SELECT title FROM item" + (" WHERE " + " AND ".join(where) if where else "")
        return {row[0] for row in self.conn.execute(query, params)}

    def test_keyword_title(self):
        self.assertEqual(self.search(q="statistics"), {"Statistics Notes"})

    def test_keyword_description(self):
        self.assertEqual(self.search(q="linked LISTS"), {"Data Structures Summary"})

    def test_module_code_keyword(self):
        self.assertEqual(self.search(q="CSC312"), {"Data Structures Summary"})

    def test_module_and_keyword_combined(self):
        self.assertEqual(self.search(q="data", module="CSC211"), {"Exam Techniques"})

    def test_literal_wildcards(self):
        self.assertEqual(self.search(q="%"), {"Review 100%"})
        self.assertEqual(self.search(q="_"), set())

    def test_no_results(self):
        self.assertEqual(self.search(q="ABC123"), set())


if __name__ == "__main__":
    unittest.main()
