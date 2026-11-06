"""One-time additive schema migration for existing Commons installations.

Run from the project root: python migrate_add_module_code.py
Existing Item records receive module_code='UNASSIGNED'. Review and retag them
using a future edit workflow or administrative migration if necessary.
"""
from sqlalchemy import inspect, text
from app import app, db, Item


def migrate() -> None:
    with app.app_context():
        inspector = inspect(db.engine)
        if not inspector.has_table("item"):
            raise RuntimeError("The item table does not exist; start the app once first.")

        columns = {col["name"] for col in inspector.get_columns("item")}
        if "module_code" not in columns:
            with db.engine.begin() as conn:
                conn.execute(text(
                    "ALTER TABLE item ADD COLUMN module_code "
                    "VARCHAR(16) NOT NULL DEFAULT 'UNASSIGNED'"
                ))
            print("Added item.module_code; previous records marked UNASSIGNED.")
        else:
            print("Column item.module_code already exists.")

        module_index = next(index for index in Item.__table__.indexes
                            if index.name == "ix_item_module_code")
        module_index.create(bind=db.engine, checkfirst=True)
        print("Module index verified; migration complete.")


if __name__ == "__main__":
    migrate()
