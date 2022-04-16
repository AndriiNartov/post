from flask import render_template, flash, redirect, url_for, request
from post_site import app
from post_site.forms import AddLetterForm, CurrencyExchangeRateForm, TextAreaForm, UpdateLetterForm
from post_site.models import Truck, Letter
from post_site import db
from post_site.services import set_status_for_letter, make_text_for_paste, parse_text_to_get_date, get_closest_prev_workday
from loguru import logger
from datetime import datetime


@app.route('/post')
def show_letters_list():
    set_status_for_letter()
    page = request.args.get('page', 1, type=int)
    letters = Letter.query.order_by(Letter.sending_date.desc()).paginate(per_page=10, page=page)
    return render_template('letters_list.html', title='Letters', letters=letters)

@logger.catch
@app.route('/post/add-letter/', methods=['GET', 'POST'])
def add_new_letter():
    form = AddLetterForm()
    if form.validate_on_submit():
        logger.info('Validated')
        truck = Truck.query.filter_by(plate_number=form.truck.data).first()
        new_letter = Letter(
            sending_date=form.sending_date.data,
            truck_id=truck.id,
            track_number=form.track_number.data,
            status='В пути',
            status_date=form.sending_date.data,
            comment=form.comment.data
        )
        db.session.add(new_letter)
        db.session.commit()
        flash(f'Новое письмо добавлено', 'success')
        return redirect(url_for('show_letters_list'))
    form.sending_date.data = datetime.utcnow().date()
    return render_template('add_letter.html', title='Add letter', form=form)

@logger.catch
@app.route('/post/update-letter/<track_number>', methods=['GET', 'POST'])
def update_letter(track_number):
    form = UpdateLetterForm()
    letter = Letter.query.filter_by(track_number=track_number).first()
    if form.validate_on_submit():
        truck = Truck.query.filter_by(plate_number=form.truck.data).first()
        letter.sending_date = form.sending_date.data
        letter.truck_id = truck.id
        letter.track_number = form.track_number.data
        letter.status = form.status.data
        letter.status_date = form.status_date.data
        letter.comment = form.comment.data
        db.session.commit()
        flash(f'Изменения сохранены', 'success')
        return redirect(url_for('show_letters_list'))
    if request.method == 'GET':
        truck = Truck.query.get(letter.truck_id)
        form.sending_date.data = letter.sending_date
        form.truck.data = truck.plate_number
        form.track_number.data = letter.track_number
        form.status.data = letter.status
        form.status_date.data = letter.status_date
        form.comment.data = letter.comment
    return render_template('update_letter.html', form=form)


@app.route('/post/delete-letter/<int:letter_id>', methods=['GET', 'POST'])
def delete_letter(letter_id):
    letter = Letter.query.filter_by(id=letter_id).first()
    if request.method == 'POST':
        db.session.delete(letter)
        db.session.commit()
        return redirect(url_for('show_letters_list'))
    return render_template('delete_confirmation.html', letter=letter)


@app.route('/currency')
def get_currency_exchange_rate():
    form = CurrencyExchangeRateForm()
    text_area_form = TextAreaForm()
    form.date.data, text_area_form.text.data = get_closest_prev_workday(datetime.utcnow().date())
    format = '%Y-%m-%d'
    if request.args.get('text'):
        text = request.args.get('text')
        date = parse_text_to_get_date(text)
        try:
            form.date.data = datetime.strptime(date, format)
            text_area_form.text.data = make_text_for_paste(datetime.strftime(form.date.data, format))
        except:
            flash(f'Выбери корректную дату и нажми "Получить"', 'danger')
            return render_template('currency.html', form=form, text_area_form=text_area_form)
        return render_template('currency.html', form=form, text_area_form=text_area_form)
    if request.args.get('date'):
        form = CurrencyExchangeRateForm()
        form.date.data = datetime.strptime(request.args.get('date'), format)
        text_area_form = TextAreaForm()
        text_area_form.text.data = make_text_for_paste(str(request.args.get('date')))
        return render_template('currency.html', form=form, text_area_form=text_area_form)
    return render_template('currency.html', form=form, text_area_form=text_area_form)
