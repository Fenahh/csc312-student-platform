"""Commons: Flask app with Person C Search & Discovery enhancements.

Person C additions: title/description search, module filtering, pagination, and
module tagging on upload. Existing registration and authentication are preserved.
The existing repository stores HTML in its root, so template_folder='.' is set
explicitly. A later team refactor can relocate all HTML to templates/.
"""
import os
from datetime import datetime, timezone
from urllib.parse import urlsplit

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import ForeignKey, String, Text, func, or_, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash
import reviews 

from search_utils import (
    escaped_like_contains,
    normalized_module,
    normalized_search,
    valid_new_module,
)


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
csrf = CSRFProtect()
PAGE_SIZE = 12


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    items: Mapped[list["Item"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Item(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")
    module_code: Mapped[str] = mapped_column(
        String(16), nullable=False, default="UNASSIGNED",
        server_default="UNASSIGNED", index=True,
    )
    created_at: Mapped[datetime] = mapped_column(default=utcnow, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)

    owner: Mapped[User] = relationship(back_populates="items")


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    try:
        return db.session.get(User, int(user_id))
    except (ValueError, TypeError):
        return None


def is_safe_redirect(target: str | None) -> bool:
    """Only allow same-site relative redirects (prevents open redirects)."""
    if not target:
        return False
    parts = urlsplit(target)
    return not parts.netloc and not parts.scheme and target.startswith("/")


def create_app(test_config: dict | None = None) -> Flask:
    # Current group layout keeps base.html, browse.html etc beside app.py.
    # Explicit template_folder keeps that layout working without moving files.
    app = Flask(__name__, template_folder=".")
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///app.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SITE_NAME="Commons",
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "login"
    login_manager.login_message_category = "info"

    @app.context_processor
    def inject_globals():
        return {"site_name": app.config["SITE_NAME"]}

    @app.route("/")
    def index():
        recent = db.session.scalars(
            select(Item).order_by(Item.created_at.desc(), Item.id.desc()).limit(4)
        ).all()
        return render_template("index.html", recent=recent)

    @app.route("/browse")
    def browse():
        """Server-side searchable catalogue using safely parameterized SQLAlchemy.

        Search is case-insensitive and searches title, description and code. Module code
        filtering can be combined with search; both remain in pagination links.
        """
        q = normalized_search(request.args.get("q"))
        module = normalized_module(request.args.get("module"))
        page = max(1, request.args.get("page", default=1, type=int) or 1)

        clauses = []
        if q:
            pattern = escaped_like_contains(q)
            clauses.append(or_(
                Item.title.ilike(pattern, escape="\\"),
                Item.description.ilike(pattern, escape="\\"),
                Item.module_code.ilike(pattern, escape="\\"),
            ))
        if module:
            clauses.append(Item.module_code == module)

        total = db.session.scalar(
            select(func.count(Item.id)).where(*clauses)
        ) or 0
        items = db.session.scalars(
            select(Item).where(*clauses)
            .order_by(Item.created_at.desc(), Item.id.desc())
            .limit(PAGE_SIZE).offset((page - 1) * PAGE_SIZE)
        ).all()
        modules = db.session.scalars(
            select(Item.module_code).distinct().order_by(Item.module_code)
        ).all()

        return render_template(
            "browse.html", items=items, q=q, module=module,
            modules=modules, page=page, total=total,
            page_size=PAGE_SIZE,
            has_prev=page > 1,
            has_next=page * PAGE_SIZE < total,
        )

    @app.route("/upload", methods=["GET", "POST"])
    @login_required
    def upload():
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            module_code = normalized_module(request.form.get("module_code"))
            if not title:
                flash("Add a title before uploading.", "danger")
            elif len(title) > 120:
                flash("Title must be 120 characters or fewer.", "danger")
            elif not valid_new_module(module_code):
                flash("Enter a module code such as CSC312 or MAT111.", "danger")
            else:
                db.session.add(Item(
                    title=title, description=description, module_code=module_code,
                    owner=current_user,
                ))
                db.session.commit()
                flash("Uploaded.", "success")
                return redirect(url_for("browse", module=module_code))
        return render_template("upload.html")

    @app.route("/profile")
    @login_required
    def profile():
        return render_template("profile.html", items=current_user.items)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("index"))
        if request.method == "POST":
            identifier = request.form.get("identifier", "").strip()
            password = request.form.get("password", "")
            user = db.session.scalar(
                select(User).where(
                    (User.username == identifier) | (User.email == identifier.lower())
                )
            )
            if user and user.check_password(password):
                login_user(user, remember=bool(request.form.get("remember")))
                nxt = request.args.get("next")
                return redirect(nxt if is_safe_redirect(nxt) else url_for("index"))
            flash("Username or password is incorrect.", "danger")
        return render_template("login.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("index"))
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            error = None
            if not (username and email and password):
                error = "Fill in every field."
            elif len(password) < 8:
                error = "Use a password with at least 8 characters."
            elif db.session.scalar(
                select(User).where((User.username == username) | (User.email == email))
            ):
                error = "That username or email is already registered."
            if error:
                flash(error, "danger")
            else:
                user = User(username=username, email=email)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                login_user(user)
                flash(f"Welcome, {user.username}.", "success")
                return redirect(url_for("index"))
        return render_template("register.html")

    @app.route("/logout", methods=["POST"])
    @login_required
    def logout():
        logout_user()
        flash("You're logged out.", "info")
        return redirect(url_for("index"))

    reviews.init(app, db, User, Item)
    app.register_blueprint(reviews.bp)

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
