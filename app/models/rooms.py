import datetime

import sqlalchemy
from sqlalchemy import orm
from werkzeug.security import generate_password_hash, check_password_hash

from app.db_session import SqlAlchemyBase


class Rooms(SqlAlchemyBase):
    __tablename__ = 'rooms'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    created_at = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    creator_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    is_private = sqlalchemy.Column(sqlalchemy.Boolean, default=False)

    messages = orm.relationship("Messages", back_populates="rooms")
    user = orm.relationship("User")
    access = orm.relationship("RoomAccess", back_populates="rooms")

    def __repr__(self):
        return f'<Room> {self.id} {self.name}'

    def set_password(self, password):
        self.password = generate_password_hash(password) if not (password is None) else password

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)