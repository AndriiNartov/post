from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, TextAreaField, ValidationError
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired
from post_site.models import Truck, Letter
from post_site.services import STATUSES
from post_site import db
from datetime import datetime, timedelta


class AddLetterForm(FlaskForm):
    sending_date = DateField('Дата отправки', validators=[DataRequired()])
    truck = SelectField('Номер машины', validators=[DataRequired()], choices=Truck.query.all())
    track_number = StringField('Номер письма', validators=[DataRequired()])
    comment = TextAreaField('Комментарий')
    submit = SubmitField('Добавить')

    def validate_track_number(self, track_number):
        letter = Letter.query.filter_by(track_number=track_number.data).first()
        if letter:
            raise ValidationError('Такое письмо уже добавлено!')


class UpdateLetterForm(FlaskForm):
    sending_date = DateField('Дата отправки', validators=[DataRequired()])
    truck = SelectField('Номер машины', validators=[DataRequired()], choices=Truck.query.all())
    track_number = StringField('Номер письма', validators=[DataRequired()])
    status = SelectField('Статус', validators=[DataRequired()], choices=STATUSES)
    status_date = DateField('Дата изменения статуса', validators=[DataRequired()])
    comment = TextAreaField('Комментарий')
    submit = SubmitField('Сохранить')


class CurrencyExchangeRateForm(FlaskForm):
    date = DateField('Дата курса валют', validators=[DataRequired()])
    submit = SubmitField('Получить')

    def validate_date(self, date):
        if date.data > datetime.utcnow().date() - timedelta(1):
            raise ValidationError('Уверен, что дата правильная?')


class TextAreaForm(FlaskForm):
    text = TextAreaField('Текст')
