import json
import os
import re
import time
from datetime import datetime, UTC
from hashlib import md5
from pathlib import Path
from typing import Iterable

import boto3
from boto3.s3.transfer import TransferConfig
from bson.json_util import dumps

from db import client

__all__ = ['create_backup']

os.makedirs('backups', exist_ok=True)

current_quotes_collection = client['quotes-dataset']['current-quotes']
processed_quotes_collection = client['quotes-dataset']['processed-quotes']
reported_quotes_collection = client['quotes-dataset']['reported-quotes']

COLLECTIONS = {'current': current_quotes_collection, 'processed': processed_quotes_collection, 'reported': reported_quotes_collection}
BUCKET_NAME = 'quotes-dataset-backup'

session = boto3.session.Session()
s3 = session.client(
    service_name='s3',
    endpoint_url='https://storage.yandexcloud.net'
)

MB = 1024 ** 2
transfer_config = TransferConfig(multipart_threshold=100 * MB)


def _create_local_backup(collection: str, filename: str):
    with open(filename, 'w', encoding='utf-8') as backup_file:
        json.dump(json.loads(dumps(COLLECTIONS[collection].find(), ensure_ascii=False)), backup_file, ensure_ascii=False)


def _get_last_collection_file(collection_name: str) -> str | None:
    bucket_objects = s3.list_objects_v2(Bucket=BUCKET_NAME)['Contents']
    bucket_objects.sort(key=lambda content: content['LastModified'], reverse=True)

    for key in bucket_objects:
        if key['Key'].startswith(f'backups/{collection_name}'):
            return key['Key']


def _get_local_md5(filename: str) -> str:
    file_md5 = md5()

    with open(filename, 'rb') as file:
        file_md5.update(file.read())

    return file_md5.hexdigest()


def _get_remote_md5(filename: str) -> str:
    key = s3.get_object(Bucket=BUCKET_NAME, Key=filename)

    return key['ETag'][1:-1]


def _write_duplicate_message(filename: str):
    duplicate_message = {'message': 'Current backup is the exact copy of the previous one', 'md5': _get_local_md5(filename)}

    with open(filename, 'w', encoding='utf-8') as duplicate_backup_file:
        json.dump(duplicate_message, duplicate_backup_file)


def _upload_files(filenames: Iterable[str]):
    for filename in filenames:
        s3.upload_file(filename, BUCKET_NAME, filename, Config=transfer_config)


def _clear_local_backups():
    for file in Path('./backups').glob('*'):
        file.unlink()


def _clear_outdated_remote_backups():
    filename_pattern = re.compile(r'backups/\w+-(\d{2}-\w{3})-\d{2}-\d{2}\.json')
    today = datetime.now(UTC).strftime('%d-%b')

    bucket_objects = s3.list_objects_v2(Bucket=BUCKET_NAME)['Contents']
    for key in bucket_objects:
        date = re.match(filename_pattern, key['Key']).group(1)
        if date != today:
            s3.delete_object(Bucket=BUCKET_NAME, Key=key['Key'])


def create_backup():
    initial_time = time.perf_counter()

    formatted_date = datetime.now(UTC).strftime('%d-%b-%H-%M')
    collection_filename = {collection_name: f'backups/{collection_name}_collection_backup-{formatted_date}.json'
                           for collection_name in COLLECTIONS.keys()}

    for collection_name in COLLECTIONS.keys():
        _create_local_backup(collection_name, collection_filename[collection_name])

    for collection_name in COLLECTIONS.keys():
        representative_filename = _get_last_collection_file(collection_name)
        assert representative_filename is not None
        local_filename = collection_filename[collection_name]

        if _get_local_md5(local_filename) == _get_remote_md5(representative_filename):
            _write_duplicate_message(local_filename)

    _upload_files(collection_filename.values())
    _clear_local_backups()
    _clear_outdated_remote_backups()

    final_time = time.perf_counter()
    print(f'Procedure of backup took {final_time - initial_time:.2f} seconds')


if __name__ == '__main__':
    create_backup()
