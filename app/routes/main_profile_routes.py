from flask import render_template, Blueprint
from flask_login import login_required, current_user
from app import db_session
from app.models.rooms import Rooms
from app_key import TEMP_DIR

main_bp = Blueprint('other', __name__, template_folder=TEMP_DIR)


@main_bp.route("/")
def main_page():
    db_sess = db_session.create_session()
    rooms = db_sess.query(Rooms).all()
    return render_template("main_page.html", rooms=rooms)


@main_bp.route("/profile")
@login_required
def profile_page():
    db_sess = db_session.create_session()
    rooms = db_sess.query(Rooms).filter(Rooms.creator_id == current_user.id).all()
    return render_template("profile.html", user=current_user, rooms=rooms)
