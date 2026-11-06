# CSC312 Person C — Testing evidence & execution log

**Selected strategy:** Black-Box Functional Testing (the single formal strategy required by the lecturer and group playbook).

## Executed in the preparation environment, 6 November 2026

| Check | Result | Evidence |
|---|---|---|
| `tests/test_search_utils.py` | PASS — 4/4 | Python unittest output |
| `tests/test_sqlite_search_contract.py` | PASS — 6/6 | Python sqlite3 in-memory matching output |
| Python syntax compile (`app.py`, migration, helper, tests) | PASS | `compileall` |
| Jinja template syntax (`browse.html`, `upload.html`) | PASS | `jinja2.Environment.parse` |
| Flask HTTP tests | **NOT RUN** | Required Flask packages unavailable in this execution environment |
| Running app screenshot evidence | **NOT CAPTURED** | GitHub write link and Flask environment unavailable |

## Final black-box test cases (run these on the integrated app)

| Case | Input and procedure | Expected behavior | Actual result | Status |
|---|---|---|---|---|
| TC-05 | Browse → enter `CSC312` → Search | Only resource cards whose title, description or module code matches `CSC312` remain; tagged CSC312 cards should be present in seeded data | **Not yet observed** | PENDING |
| TC-06 | Browse → enter `ABC123` → Search | No crash; `No resources found` and `View all resources` visible | **Not yet observed** | PENDING |
| C-03 | Browse → choose module `CSC312` → Find notes | Only CSC312-tagged resources appear | **Not yet observed** | PENDING |
| C-04 | Browse → search `Data` + select module `CSC211` | Only combined matches appear | **Not yet observed** | PENDING |
| C-05 | Narrow browser to ~375 px width | Search controls, cards and buttons remain usable without horizontal overflow | **Not yet observed** | PENDING |

### Seed data / demonstration setup

After updating the schema, register a local test account and use the Upload form to add these **metadata-only** resources:

- `Data Structures Summary`, `Linked lists, stacks, queues`, module `CSC312`.
- `Statistics Revision`, `Distributions and estimation`, module `STA222`.
- `Introduction to Algorithms`, `Searching and sorting`, module `CSC211`.

These are example resource records for search testing. They do **not** constitute PDF file uploads; that is Person B's unfinished feature in the available snapshot.

### Screenshots to capture from the real app

- **Figure C1:** Browse catalogue displaying resource cards and module tags.
- **Figure C2:** Successful search for `CSC312`, showing matching results (TC-05).
- **Figure C3:** Active `CSC312` module filter with matching resource cards (C-03).
- **Figure C4:** Zero-results message for `ABC123` (TC-06).

Capture using **Win + Shift + S** on Windows, with a readable browser zoom. Do not label tests PASS until the actual behavior is observed. Insert screenshots and observed outcomes in the group's Testing section of the final PDF.
