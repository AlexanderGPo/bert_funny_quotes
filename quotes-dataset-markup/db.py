import os
import random
from contextlib import suppress
from pathlib import Path
from typing import Iterator

from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from quotes import *

__all__ = ['get_first_quote_id', 'get_quote_from_collection', 'add_reported_quote', 'apply_vote', 'apply_nsfw', 'client']

MONGO_CLUSTER_ADDRESS = os.getenv('MONGO_CLUSTER_ADDRESS')
MONGO_ADMIN_PASSWORD = os.getenv('MONGO_ADMIN_PASSWORD')

SOURCE_MAPPING = {
    'letovo': LetovoQuote,
    'myxa': MyxaQuote,
    'hse': HSEQuote,
    'fefu': FEFUQuote,
    'ksu': KSUQuote,
    'isu': ISUQuote,
    'mgtu': MGTUQuote,
    'mipt': MIPTQuote,
    'sgu': SGUQuote,
    'vkletovo': VKLetovoQuote,
    'nstu': NSTUQuote,
    'sfedu': SFEDUQuote,
    'urfu': URFUQuote,
    'msu': MSUQuote
}

VOTES_THRESHOLD = 3

random.seed(42)

client = MongoClient(f'mongodb+srv://admin:{MONGO_ADMIN_PASSWORD}@{MONGO_CLUSTER_ADDRESS}/')

current_quotes_collection = client['quotes-dataset']['current-quotes']
processed_quotes_collection = client['quotes-dataset']['processed-quotes']
reported_quotes_collection = client['quotes-dataset']['reported-quotes']


def load_homogeneous_dataset(source: str, quotes: list[GenericQuote]):
    source_class = SOURCE_MAPPING[source]
    inserted_quotes = []

    for quote in quotes:
        if not isinstance(quote, source_class):
            raise ValueError(f'Found quote of {type(quote)} instead of the expected {source_class}')

        inserted_quotes.append({'text': quote.text, 'positive_votes': 0, 'negative_votes': 0, 'channel_link': quote.channel_link,
                                'channel_name': quote.channel_name})

    current_quotes_collection.insert_many(inserted_quotes, ordered=False)


def load_dataset(quotes: list[GenericQuote]):
    inserted_quotes = []

    for quote in quotes:
        inserted_quotes.append({'text': quote.text, 'positive_votes': 0, 'negative_votes': 0, 'channel_link': quote.channel_link,
                                'channel_name': quote.channel_name})

    current_quotes_collection.insert_many(inserted_quotes, ordered=False)


def prepare_vk_dataset(dataset_filename: str, source: str) -> list[GenericQuote]:
    vk_dataset = []
    source_class = SOURCE_MAPPING[source]

    with open(Path('./data') / dataset_filename, encoding='utf-8') as dataset_file:
        quotes = eval(dataset_file.read())

    for quote_text in quotes:
        try:
            vk_dataset.append(source_class(quote_text))
        except AssertionError:
            # TODO: implement some logging
            continue

    return vk_dataset


def get_first_quote_id() -> str:
    return str(current_quotes_collection.find_one()['_id'])


def get_quote_from_collection(starting_point: str) -> Iterator[tuple[str, str, str, int, str]]:
    for quote in current_quotes_collection.find({'_id': {'$gte': ObjectId(starting_point)}}):
        yield quote['text'], quote['channel_name'], quote['channel_link'], quote['nsfw'], str(quote['_id'])


def add_reported_quote(internal_id: str):
    reported_quote = current_quotes_collection.find_one({'_id': ObjectId(internal_id)})

    with suppress(DuplicateKeyError):
        reported_quotes_collection.insert_one(reported_quote)


def apply_nsfw(internal_id: str):
    current_quotes_collection.update_one({'_id': ObjectId(internal_id)}, {'$inc': {'nsfw': 1}})


def apply_vote(vote: str, internal_id: str) -> bool:
    # TODO: handle cases when entry is not found
    internal_id = ObjectId(internal_id)

    match vote:
        case 'positive':
            current_quotes_collection.update_one({'_id': internal_id}, {'$inc': {'positive_votes': 1}})
        case 'negative':
            current_quotes_collection.update_one({'_id': internal_id}, {'$inc': {'negative_votes': 1}})
        case _:
            raise ValueError(f'Unknown vote type: {vote}')

    current_quote = current_quotes_collection.find_one({'_id': internal_id})

    if current_quote['positive_votes'] > VOTES_THRESHOLD // 2:  # assuming that VOTES_THRESHOLD is an odd number
        current_quote['positive_votes'] = VOTES_THRESHOLD - current_quote['negative_votes']

    if current_quote['negative_votes'] > VOTES_THRESHOLD // 2:
        current_quote['negative_votes'] = VOTES_THRESHOLD - current_quote['positive_votes']

    votes = current_quote['positive_votes'] + current_quote['negative_votes']
    if votes >= VOTES_THRESHOLD:
        current_quotes_collection.delete_one({'_id': internal_id})
        processed_quotes_collection.insert_one(current_quote)
        return False

    return True


if __name__ == '__main__':
    # TODO: implement tests

    dataset = []

    with open('data/letovo_quotes.json', encoding='utf-8') as data_file:
        letovo_quotes = json.load(data_file)

    for quote_object in letovo_quotes:
        try:
            dataset.append(LetovoQuote(quote_object['text']))
        except AssertionError:
            continue

    dataset += prepare_vk_dataset('citatnik_myxa.txt', 'myxa')
    dataset += prepare_vk_dataset('hseteachers.txt', 'hse')
    dataset += prepare_vk_dataset('fefu_quotes.txt', 'fefu')
    dataset += prepare_vk_dataset('glagolit_ksu.txt', 'ksu')
    dataset += prepare_vk_dataset('isu_quotes.txt', 'isu')
    dataset += prepare_vk_dataset('mgtupage.txt', 'mgtu')
    dataset += prepare_vk_dataset('prepod_mipt.txt', 'mipt')
    dataset += prepare_vk_dataset('public80867350.txt', 'sgu')
    dataset += prepare_vk_dataset('public170539958.txt', 'vkletovo')
    dataset += prepare_vk_dataset('quotes_nstu.txt', 'nstu')
    dataset += prepare_vk_dataset('sfeduquotes.txt', 'sfedu')
    dataset += prepare_vk_dataset('urfusay.txt', 'urfu')
    dataset += prepare_vk_dataset('ustami_msu.txt', 'msu')

    expletive_quotes = search_profanity(dataset, exclude=False)
    expletive_documents = [{'text': quote.text, 'positive_votes': 0, 'negative_votes': 5, 'nsfw': 5} for quote in expletive_quotes]
    # processed_quotes_collection.insert_many(expletive_documents)

    # dataset = search_profanity(dataset, exclude=True)

    # random.shuffle(dataset)
    # load_dataset(dataset)

    ...
