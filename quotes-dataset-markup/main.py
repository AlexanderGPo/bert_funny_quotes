import os
import secrets
import time
from functools import wraps
from threading import Thread

import msgpack
import redis
import schedule
from flask import abort, Flask, jsonify, render_template, request, session
from flask_session import Session
from flask_talisman import Talisman

from db import add_reported_quote, apply_nsfw, apply_vote, get_first_quote_id, get_quote_from_collection
from db_backup import create_backup

REDIS_ADDRESS = os.getenv('REDIS_ADDRESS')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')

app = Flask(__name__)
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url(f'redis://default:{REDIS_PASSWORD}@{REDIS_ADDRESS}')
Session(app)
Talisman(app, content_security_policy=None)

NSFW_THRESHOLD = 1


def current_quote_id(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        quotes_iterator_start = session.get('quotes_iterator', get_first_quote_id())
        quotes_iterator = get_quote_from_collection(quotes_iterator_start)
        *_, _id = next(quotes_iterator)

        return func(_id, *args, **kwargs)

    return wrapper


@app.route('/')
def index():
    nsfw_filter = request.args.get('nsfw_filter', 'false').lower() == 'true'
    if nsfw_filter:
        session['nsfw_always_on'] = True

    return render_template('index.html')


@app.route('/report', methods=['POST'])
@current_quote_id
def report(quote_id: str):
    mongo_id = request.form.get('internal_id')

    if mongo_id is None:
        abort(400)

    if session.get('name') is None or quote_id != mongo_id:
        return abort(403)

    add_reported_quote(mongo_id)

    session['vote_streak'] += 1

    return 'Successfully reported the quote!'


@app.route('/mark_nsfw', methods=['POST'])
@current_quote_id
def mark_nsfw(quote_id: str):
    mongo_id = request.form.get('internal_id')

    if mongo_id is None:
        abort(400)

    if session.get('name') is None or quote_id != mongo_id:
        return abort(403)

    apply_nsfw(mongo_id)

    return 'Successfully marked the quote as NSFW!'


@app.route('/vote', methods=['POST'])
@current_quote_id
def vote(quote_id: str):
    vote_value = request.form.get('vote')
    mongo_id = request.form.get('internal_id')

    if vote_value is None or mongo_id is None:
        abort(400)

    if session.get('name') is None or quote_id != mongo_id:
        return abort(403)

    try:
        skip = apply_vote(vote_value, mongo_id)
    except ValueError:
        abort(400)

    session['vote_streak'] += 1

    return jsonify({'skip': skip})


@app.route('/sync_data', methods=['POST'])
def sync_data():
    if session.get('name') is None:
        return abort(403)

    data_token = request.form.get('token')

    if data_token is None:
        return jsonify({'token': session.get('name')})

    redis_conn = app.config['SESSION_REDIS']
    keys = redis_conn.keys('*')
    values = redis_conn.mget(keys)

    for raw_value in values:
        value = msgpack.unpackb(raw_value)
        if value['name'] == data_token:
            session['quotes_iterator'] = value['quotes_iterator']
            session['vote_streak'] = value['vote_streak']
            break
    else:
        return abort(400)

    return 'Successfully synchronized accounts!'


@app.route('/get_quote', methods=['GET'])
def get_quote():
    nsfw_filter = request.args.get('nsfw_filter', 'false').lower() == 'true'
    new_user = session.get('name') is None

    if new_user:
        session['name'] = secrets.token_hex(4)
        session['vote_streak'] = 0

    if session.get('nsfw_always_on') is not None:
        nsfw_filter = True

    quotes_iterator_start = session.get('quotes_iterator', get_first_quote_id())
    quotes_iterator = get_quote_from_collection(quotes_iterator_start)

    text, channel_name, channel_link, nsfw, mongo_id = next(quotes_iterator)
    if nsfw_filter:
        while nsfw >= NSFW_THRESHOLD:
            text, channel_name, channel_link, nsfw, mongo_id = next(quotes_iterator)

    session['quotes_iterator'] = mongo_id

    # TODO: should Mongo Cursor be tailed?
    return jsonify(
        {'text': text, 'internal_id': mongo_id, 'new_user': new_user, 'channel_name': channel_name, 'channel_link': channel_link,
         'nsfw': nsfw, 'vote_streak': session['vote_streak']})


@app.route('/proceed', methods=['GET'])
def proceed():
    if session.get('name') is None:
        return abort(403)

    quotes_iterator_start = session.get('quotes_iterator', get_first_quote_id())
    session['quotes_iterator'] = hex(int(quotes_iterator_start, 16) + 1)[2:].rjust(24, '0')

    return 'Successfully moved iterator forwards!'


if __name__ == '__main__':
    Thread(target=app.run, args=('0.0.0.0', int(os.getenv('PORT', 80)))).start()

    schedule.every().hour.do(create_backup)

    while True:
        schedule.run_pending()
        time.sleep(1)
