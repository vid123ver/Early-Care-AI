import os
from pymongo import MongoClient
# export MONGO_URI="mongodb+srv://vidhanverma2311_db_user:<YOUR_PASSWORD>@<cluster-host>/earlycare?retryWrites=true&w=majority"
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    socketTimeoutMS=5000,
)
db = client['earlycare']

users_collection = db['users']
reports_collection = db['reports']
predictions_collection = db['predictions']
alerts_collection = db['alerts']


def insert_user(user_data):
    return users_collection.insert_one(user_data)


def fetch_user(query):
    return users_collection.find_one(query)


def update_user(query, updates):
    return users_collection.update_one(query, updates)


def insert_report(report_data):
    return reports_collection.insert_one(report_data)


def fetch_report(query):
    return reports_collection.find_one(query)

def fetch_reports_by_user(user_id, limit=50):
    return list(
        reports_collection.find({'user_id': user_id})
        .sort('created_at', -1)
        .limit(int(limit))
    )

def count_reports_by_user(user_id):
    return reports_collection.count_documents({'user_id': user_id})

def fetch_latest_report_by_user(user_id):
    return reports_collection.find_one({'user_id': user_id}, sort=[('created_at', -1)])


def insert_prediction(prediction_data):
    return predictions_collection.insert_one(prediction_data)


def fetch_prediction(query):
    return predictions_collection.find_one(query)


def insert_prediction_record(user_id, report_id, prediction_result, risk_level, summary):
    from datetime import datetime
    record = {
        'user_id': user_id,
        'report_id': report_id,
        'prediction_result': prediction_result,
        'risk_level': risk_level,
        'summary': summary,
        'created_at': datetime.utcnow()
    }
    return predictions_collection.insert_one(record)


def fetch_predictions_by_user(user_id):
    return list(predictions_collection.find({'user_id': user_id}))


def fetch_user_reports_metrics(user_id, marker):
    """
    Fetch historical values of a specific marker for a user, sorted by created_at.
    Returns list of (created_at, value)
    """
    reports = reports_collection.find({'user_id': user_id}).sort('created_at', 1)
    trend = []
    for r in reports:
        metrics = r.get('metrics', {})
        if marker in metrics:
            trend.append((r.get('created_at'), metrics[marker]))
    return trend


def insert_alert(user_id, report_id, alerts):
    from datetime import datetime
    alert_doc = {
        'user_id': user_id,
        'report_id': report_id,
        'alerts': alerts,
        'created_at': datetime.utcnow()
    }
    return db['alerts'].insert_one(alert_doc)
