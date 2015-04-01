import pymongo
from pymongo import MongoClient 

client = MongoClient()
world = client.game.world
users = client.game.users

print "drop world", world.drop()
print "drop users", users.drop()
