from flask import flash, redirect, url_for, render_template, request, Blueprint
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash


from app import db_session
from app.models.messages import Messages
from app.models.room_access import RoomAccess
from app.models.rooms import Rooms
from app_key import TEMP_DIR
from forms.room import RoomForm, RoomAccessForm

rooms_bp = Blueprint('rooms', __name__, template_folder=TEMP_DIR)


@rooms_bp.route("/create_room", methods=['GET', 'POST'])
@login_required
def create_room():
    form = RoomForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()

        room = Rooms(
            name=form.name.data,
            creator_id=current_user.id,
            is_private=form.is_private.data
        )

        room.set_password(form.password.data)

        db_sess.add(room)
        db_sess.commit()

        access = RoomAccess(user_id=current_user.id, room_id=room.id)
        db_sess.add(access)
        db_sess.commit()

        flash(f'Комната "{form.name.data}" создана', 'success')

        return redirect(url_for('other.main_page'))

    return render_template('create_room.html', form=form)


@rooms_bp.route("/delete_room/<int:room_id>", methods=['POST'])
@login_required
def delete_room(room_id):
    db_sess = db_session.create_session()
    room = db_sess.query(Rooms).filter(Rooms.id == room_id, Rooms.creator_id == current_user.id).first()
    accesses = db_sess.query(RoomAccess).filter(RoomAccess.room_id == room.id).all()
    if room:
        for access in accesses:
            db_sess.delete(access)
        db_sess.delete(room)
        db_sess.commit()
        print(accesses)
        flash('Комната успешно удалена', 'success')
    else:
        flash('Комната не найдена или у вас нет прав', 'error')

    return redirect(url_for('other.profile_page'))


@rooms_bp.route('/search')
@login_required
def search_rooms():
    query = request.args.get('query', '').strip()
    db_sess = db_session.create_session()

    if query:
        rooms = db_sess.query(Rooms).filter(
            Rooms.name.ilike(f'%{query}%')
        ).order_by(Rooms.created_at.desc()).all()
    else:
        rooms = db_sess.query(Rooms).order_by(Rooms.created_at.desc()).all()

    return render_template('main_page.html',
                           rooms=rooms,
                           tittle_word=f"Результаты поиска: '{query}'" if query else "Все комнаты")


@rooms_bp.route('/enter_private_room/<int:room_id>', methods=['POST', 'GET'])
def enter_private_room(room_id):
    db_sess = db_session.create_session()
    room = db_sess.get(Rooms, room_id)
    form = RoomAccessForm()

    if not room:
        flash('Комната не найдена', 'error')
        return redirect(url_for('other.main_page'))

    if not room.is_private:
        return redirect(url_for('join_room', room_id=room.id))

    access = db_sess.query(RoomAccess).filter(RoomAccess.user_id == current_user.id,
                                              RoomAccess.room_id == room_id).first()
    if access:
        return redirect(url_for('join_room', room_id=room.id))

    if form.validate_on_submit():
        if check_password_hash(room.password, form.password.data):

            access = RoomAccess(user_id=current_user.id, room_id=room.id)

            db_sess.add(access)
            db_sess.commit()

            return redirect(url_for('join_room', room_id=room.id))
        else:
            flash('Неверный пароль', 'error')

    return render_template('room_password.html', room=room, form=form)


@rooms_bp.route('/join_room/<int:room_id>')
@login_required
def join_room(room_id):
    db_sess = db_session.create_session()
    room = db_sess.get(Rooms, room_id)

    if not room:
        flash('Комната не найдена', 'error')
        return redirect(url_for('other.main_page'))

    messages = db_sess.query(Messages).filter(Messages.room_id == room.id).order_by(Messages.date.asc()).all()

    return render_template('room.html', room=room, messages=messages, current_user=current_user)