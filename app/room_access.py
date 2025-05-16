import datetime
import sqlalchemy

from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class RoomAccess(SqlAlchemyBase):
    __tablename__ = 'room_access'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    room_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('rooms.id'))
    access_granted = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now())

    user = orm.relationship('User', back_populates="access")
    rooms = orm.relationship('Rooms', back_populates="access")
