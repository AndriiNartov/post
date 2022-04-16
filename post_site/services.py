from zeep import Client
from zeep.wsse import UsernameToken
from post_site.models import *
from datetime import datetime, timedelta
from loguru import logger
import requests

logger.add('debug.log', level='DEBUG', rotation='10:00', compression='zip')

TRUCKS = [
    'KR1J156',
    'KWI6250C',
    'KWI1303E',
    'KWI3768E',
    'KR1AN72',
    'KR5FX41',
    'KR3KL07',
    'KR3KL10',
    'KR2KL76',
    'KR3KM14',
    'KR3TP62'
]


STATUSES = [
    'В пути',
    'Передан на доставку',
    'Авизо',
    'Доставлено',
    'Не бьётся'
]


API_POST_CLIENT = Client(wsdl='https://tt.poczta-polska.pl/Sledzenie/services/Sledzenie?wsdl',
                    wsse=UsernameToken('sledzeniepp', 'PPSA'))

CURRENCY_API_REQUEST_URL = 'http://api.nbp.pl/api/exchangerates/rates/A/EUR/'


def fill_in_table_with_trucks():
    for truck in TRUCKS:
        new_truck = Truck(plate_number=truck)
        db.session.add(new_truck)
        db.session.commit()


def reformat_date(date_time_str_obj):
    date_without_time = date_time_str_obj.split(' ')[0]
    new_date = datetime.strptime(date_without_time, '%Y-%m-%d')
    return new_date


def get_undelivered_letters():
    query = Letter.query.filter(
        Letter.status.startswith('В пути') |
        Letter.status.startswith('Передан') |
        Letter.status.startswith('Авизо') |
        Letter.status.startswith('Не бьётся')).all()
    return query


def set_status_for_letter():
    undelivered_letters = get_undelivered_letters()
    for letter in undelivered_letters:
        if letter.track_number == 'Без номера':
            letter.status = 'В пути'
            letter.status_date = letter.sending_date
            continue
        requested_letter = API_POST_CLIENT.service.sprawdzPrzesylke(letter.track_number)
        status_list = []
        if not requested_letter.danePrzesylki.zdarzenia:
            letter.status = 'Не бьётся'
            letter.status_date = letter.sending_date
            continue
        for zdarzenie in requested_letter.danePrzesylki.zdarzenia.zdarzenie:
            status_list.append(zdarzenie.nazwa)
        if 'Wysłanie przesyłki z kraju nadania' in status_list:
            letter.status = 'В пути'
            letter.status_date = reformat_date(zdarzenie.czas)
        if 'Doręczenie' in status_list or 'Odebranie w urzędzie' in status_list:
            letter.status = 'Доставлено'
            letter.status_date = reformat_date(zdarzenie.czas)
            continue
        if 'Awizo' in status_list:
            letter.status = 'Авизо'
            letter.status_date = reformat_date(zdarzenie.czas)
            continue
        if 'Wprowadzenie do księgi oddawczej' in status_list:
            letter.status = 'Передан на доставку'
            letter.status_date = reformat_date(zdarzenie.czas)
            continue
    db.session.commit()


def get_exc_rate_info_for_date(date):
    response = requests.get(f'{CURRENCY_API_REQUEST_URL}{date}/')
    if response.status_code == 200:
        response_dict = response.json()
        eur_exc_rate = str(response_dict['rates'][0]['mid'])
        table_number = response_dict['rates'][0]['no']
        if len(eur_exc_rate.split('.')[1]) == 2:
            eur_exc_rate += '00'
        return eur_exc_rate, table_number


def make_text_for_paste(date):
    try:
        eur_exc_rate, table_number = get_exc_rate_info_for_date(date)
        return f'Tabela nr {table_number} z dnia {date}\n\nKURS: 1 EUR = {eur_exc_rate} PLN'
    except:
        return 'Нет курса на заданную дату!'


def get_closest_prev_workday(datetime_date_today):
    for prev_date_delta in range(1, 8):
        prev_date = datetime_date_today - timedelta(prev_date_delta)-timedelta(1)
        prev_date_str = datetime.strftime(prev_date, '%Y-%m-%d')
        response = requests.get(f'{CURRENCY_API_REQUEST_URL}{prev_date_str}/')
        if response.status_code == 200:
            return prev_date, make_text_for_paste(prev_date_str)


def parse_text_to_get_date(text):
    splitted_text = text.split(' ')
    date = ''
    for list_el in splitted_text:
        if 'KURS' in list_el:
            date = list_el[:10]
    return date
