from pymongo import MongoClient


def get_db():
    client = MongoClient("db configuration")
    db = client['db name']  # Replace 'your_database_name' with your actual database name
    return db

