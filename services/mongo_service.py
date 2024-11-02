import json
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st
from pymongo import MongoClient, ASCENDING

from config.configuration import configs


def add_log_to_db_coll(document):
    add_to_collection('logs', document, 'messageId')


def add_to_collection(collection, document, unique_field):
    db = get_mongo_db()
    coll = db[collection]
    unique_key = document[unique_field]
    timestamp = datetime.now(ZoneInfo("Asia/Kolkata"))
    document['timestamps.lastModified'] = timestamp
    update_document = {
        '$set': document,
        '$setOnInsert': {
            "timestamps.added": timestamp,
        }
    }
    coll.update_one(
        {unique_field: unique_key},
        update_document,
        upsert=True
    )
    #Use result.upserted_id is None to know if document was updated


@st.cache_data(show_spinner=configs['streamlit.spinner.messages.find_logs_for_file'])
def find_logs_for_file(file_id, projection = None):
    if configs['mongo.mockData']:
        time.sleep(4)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(current_dir, '..', 'db', 'mock_logs.json')
        with open(json_path, 'r') as file:
            mock_logs = json.load(file)
        for log in mock_logs:
            log['stackTrace'] = log['stackTrace'].replace('\\n', '\n')
        return mock_logs
    else:
        db = get_mongo_db()
        collection = db['logs']
        query = {'fileId': file_id}
        cursor = collection.find(query, projection).sort('messageId', ASCENDING)
        return list(cursor)


def get_mongo_db():
    client = MongoClient(configs['mongo.connectionString'])
    db = client[configs['mongo.database']]
    return db


# add_log_to_db_coll(
#     {
#         "fileId": "abc",
#         "fileName": "test2.log",
#         "message": "RuntimeException",
#         "messageId": "msg2",
#         "stackTrace": "some trace",
#     }
# )
