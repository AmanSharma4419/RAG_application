from pymongo import MongoClient

MONGO_URL = "mongodb://admin:admin@mongo:27017/myragdb?authSource=admin"
client = MongoClient(MONGO_URL)

db = client["myragdb"]

files_collection = db["files"]
