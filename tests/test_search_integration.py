"""Flask black-box + integration tests for Person C; requires requirements.txt.

Run from repository root: python -m unittest discover -s tests -p 'test_*.py' -v
This test file uses a separate in-memory database, never the group's database.
"""
import unittest

from app import Item, User, create_app, db


class SearchDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "unit-test-secret-only",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        })
        self.context = self.app.app_context()
        self.context.push()
        self.client = self.app.test_client()
        db.create_all()
        self.user = User(username="testcontributor", email="test@example.com")
        self.user.set_password("TestingPassword123!")
        db.session.add(self.user)
        db.session.flush()
        db.session.add_all([
            Item(title="Data Structures Summary", description="Linked lists and trees", module_code="CSC312", owner=self.user),
            Item(title="Statistics Notes", description="Probability distributions", module_code="STA222", owner=self.user),
            Item(title="Exam Techniques", description="Data structures revision and practice", module_code="CSC211", owner=self.user),
        ])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def response_text(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        return response.get_data(as_text=True)

    def test_catalog_cards_and_tags(self):
        body = self.response_text("/browse")
        self.assertIn("Data Structures Summary", body)
        self.assertIn("Statistics Notes", body)
        self.assertIn("CSC312", body)

    def test_keyword_search_title(self):
        body = self.response_text("/browse?q=Statistics")
        self.assertIn("Statistics Notes", body)
        self.assertNotIn("Data Structures Summary", body)

    def test_keyword_search_description_case_insensitive(self):
        body = self.response_text("/browse?q=linked%20LISTS")
        self.assertIn("Data Structures Summary", body)
        self.assertNotIn("Statistics Notes", body)

    def test_keyword_search_module_code_tc05(self):
        body = self.response_text("/browse?q=CSC312")
        self.assertIn("Data Structures Summary", body)
        self.assertNotIn("Statistics Notes", body)

    def test_module_filter(self):
        body = self.response_text("/browse?module=STA222")
        self.assertIn("Statistics Notes", body)
        self.assertNotIn("Data Structures Summary", body)

    def test_keyword_and_module_combination(self):
        body = self.response_text("/browse?q=Data&module=CSC211")
        self.assertIn("Exam Techniques", body)
        self.assertNotIn("Data Structures Summary", body)

    def test_zero_results_tc06(self):
        body = self.response_text("/browse?q=ABC123")
        self.assertIn("No resources found", body)
        self.assertIn("View all resources", body)

    def test_like_percent_is_literal(self):
        body = self.response_text("/browse?q=%25")
        self.assertIn("No resources found", body)

    def test_create_item_with_module(self):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(self.user.id)
            session["_fresh"] = True
        response = self.client.post("/upload", data={
            "title": "Concurrency Practice", "description": "Threads and scheduling",
            "module_code": " csc312 ",
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Concurrency Practice", response.get_data(as_text=True))
        saved = db.session.scalar(db.select(Item).where(Item.title == "Concurrency Practice"))
        self.assertEqual(saved.module_code, "CSC312")

    def test_upload_rejects_invalid_module_code(self):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(self.user.id)
            session["_fresh"] = True
        response = self.client.post("/upload", data={
            "title": "Unsorted note", "description": "Test", "module_code": "bad-code"
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("Enter a module code", response.get_data(as_text=True))
        self.assertIsNone(db.session.scalar(db.select(Item).where(Item.title == "Unsorted note")))


if __name__ == "__main__":
    unittest.main()
