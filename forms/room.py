from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length


class RoomForm(FlaskForm):
    name = StringField('Название комнаты', validators=[
        DataRequired(message="Обязательное поле"),
        Length(min=3, max=50, message="От 3 до 50 символов")
    ])
    is_private = BooleanField('Приватная комната')
    password = PasswordField('Пароль')
    submit = SubmitField('Создать комнату')


class RoomAccessForm(FlaskForm):
    password = PasswordField('Пароль комнаты', validators=[
        DataRequired(message="Введите пароль")
    ])
    submit = SubmitField('Войти')
