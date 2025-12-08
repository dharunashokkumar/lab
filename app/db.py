from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["selfmade_labs"]

users = db.users
labs = db.labs
instances = db.lab_instances
