"""Person 5: ratings, reviews and moderation for the Commons app.

Plug-in (only 4 lines to add in app.py, inside create_app()):

    import reviews                                   # top of app.py
    ...
    reviews.init(app, db, User, Item)                # BEFORE db.create_all()
    app.register_blueprint(reviews.bp)

Admins: set the environment variable ADMIN_USERNAMES, e.g.
    ADMIN_USERNAMES=alice,bob
Any user whose username is in that list can open /admin/flags.
(No change to the User model, so no database migration is needed.)
"""
import os
from datetime import datetime, timezone
from functools import wraps

from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, url_for)
from flask_login import current_user, login_required
from sqlalchemy import (ForeignKey, String, UniqueConstraint, delete, func,
                        select)
from sqlalchemy.orm import Mapped, mapped_column, relationship

bp = Blueprint("reviews", __name__)

FLAG_REASONS = {
    "COPYRIGHT_VIOLATION": "Copyright violation",
    "OUTDATED_SYLLABUS": "Outdated syllabus",
    "INACCURATE_CONTENT": "Inaccurate content",
    "POOR_QUALITY": "Poor quality",
}
MAX_COMMENT = 500

# Filled in by init()
db = User = Item = Review = Flag = None


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def init(app, database, user_model, item_model):
    """Create the Review and Flag tables using the app's db, User and Item."""
    global db, User, Item, Review, Flag
    db, User, Item = database, user_model, item_model

    class Review(db.Model):
        __table_args__ = (UniqueConstraint("user_id", "item_id"),)
        id: Mapped[int] = mapped_column(primary_key=True)
        user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
        item_id: Mapped[int] = mapped_column(ForeignKey("item.id"), index=True)
        score: Mapped[int]
        comment: Mapped[str] = mapped_column(String(MAX_COMMENT), default="")
        created_at: Mapped[datetime] = mapped_column(default=utcnow, index=True)
        author = relationship(user_model)

    class Flag(db.Model):
        id: Mapped[int] = mapped_column(primary_key=True)
        user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
        item_id: Mapped[int] = mapped_column(ForeignKey("item.id"), index=True)
        reason: Mapped[str] = mapped_column(String(30))
        details: Mapped[str] = mapped_column(String(500), default="")
        created_at: Mapped[datetime] = mapped_column(default=utcnow, index=True)
        is_resolved: Mapped[bool] = mapped_column(default=False)
        reporter = relationship(user_model)
        item = relationship(item_model)

    globals()["Review"], globals()["Flag"] = Review, Flag

    app.config.setdefault(
        "ADMIN_USERNAMES",
        [n.strip() for n in os.environ.get("ADMIN_USERNAMES", "").split(",") if n.strip()],
    )
    # Make these available inside every template
    app.jinja_env.globals.update(
        rating_summary=rating_summary,
        reviews_for=reviews_for,
        is_admin=is_admin,
        flag_reasons=FLAG_REASONS,
    )


# ------------------------------------------------------------------ helpers
def is_admin() -> bool:
    return (current_user.is_authenticated
            and current_user.username in current_app.config["ADMIN_USERNAMES"])


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapper(*args, **kwargs):
        if not is_admin():
            abort(403)  # logged in but not allowed
        return view(*args, **kwargs)
    return wrapper


def rating_summary(item):
    """Return (average, count). Average = sum of scores / number of reviews."""
    avg, count = db.session.execute(
        select(func.avg(Review.score), func.count(Review.id))
        .where(Review.item_id == item.id)
    ).one()
    return (round(avg, 1) if avg is not None else None, count)


def reviews_for(item):
    return db.session.scalars(
        select(Review).where(Review.item_id == item.id)
        .order_by(Review.created_at.desc())
    ).all()


def back():
    return redirect(url_for("browse"))


# -------------------------------------------------------- ratings & reviews
@bp.route("/items/<int:item_id>/review", methods=["POST"])
@login_required
def submit_review(item_id):
    item = db.session.get(Item, item_id) or abort(404)

    if item.user_id == current_user.id:
        flash("You can't review your own upload.", "danger")
        return back()

    try:
        score = int(request.form.get("score", ""))
    except ValueError:
        score = 0
    if not 1 <= score <= 5:
        flash("Score must be a whole number from 1 to 5.", "danger")
        return back()

    comment = request.form.get("comment", "").strip()
    if len(comment) > MAX_COMMENT:
        flash(f"Keep your review under {MAX_COMMENT} characters.", "danger")
        return back()

    if db.session.scalar(select(Review).where(
            Review.user_id == current_user.id, Review.item_id == item_id)):
        flash("You've already reviewed this one.", "danger")
        return back()

    db.session.add(Review(user_id=current_user.id, item_id=item_id,
                          score=score, comment=comment))
    db.session.commit()
    flash("Thanks, your review was saved.", "success")
    return back()


@bp.route("/reviews/<int:review_id>/delete", methods=["POST"])
@login_required
def delete_review(review_id):
    review = db.session.get(Review, review_id) or abort(404)
    if review.user_id != current_user.id and not is_admin():
        abort(403)  # only the author or an admin
    db.session.delete(review)
    db.session.commit()
    flash("Review deleted.", "info")
    return back()


# ---------------------------------------------------------------- reporting
@bp.route("/items/<int:item_id>/flag", methods=["POST"])
@login_required
def flag_item(item_id):
    db.session.get(Item, item_id) or abort(404)

    reason = request.form.get("reason", "")
    if reason not in FLAG_REASONS:
        flash("Choose a valid reason for the report.", "danger")
        return back()

    if db.session.scalar(select(Flag).where(
            Flag.user_id == current_user.id, Flag.item_id == item_id,
            Flag.is_resolved.is_(False))):
        flash("You've already reported this item.", "danger")
        return back()

    db.session.add(Flag(user_id=current_user.id, item_id=item_id, reason=reason,
                        details=request.form.get("details", "").strip()[:500]))
    db.session.commit()
    flash("Report sent. A moderator will take a look.", "success")
    return back()


# ------------------------------------------------------------ admin / moderation
@bp.route("/admin/flags")
@admin_required
def admin_flags():
    flags = db.session.scalars(
        select(Flag).where(Flag.is_resolved.is_(False)).order_by(Flag.created_at)
    ).all()
    return render_template("admin_flags.html", flags=flags)


@bp.route("/admin/flags/<int:flag_id>/resolve", methods=["POST"])
@admin_required
def resolve_flag(flag_id):
    flag = db.session.get(Flag, flag_id) or abort(404)
    action = request.form.get("action")

    if action == "dismiss":
        flag.is_resolved = True
        flash("Report dismissed.", "info")
    elif action == "remove_item":
        item = flag.item
        db.session.execute(delete(Review).where(Review.item_id == item.id))
        db.session.execute(delete(Flag).where(Flag.item_id == item.id))
        db.session.delete(item)
        flash("Item removed.", "success")
    else:
        abort(400)

    db.session.commit()
    return redirect(url_for("reviews.admin_flags"))
