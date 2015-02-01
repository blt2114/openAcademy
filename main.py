#Driver Function
import pymongo
import bottle #micro-framework
import sys
from random import randint
from bottle import route, run, template
def generate_tiles():
    #generate 20 random tiles
    tiles=[]
    for x in range(20):
        for y in range(20):
            c = randint(1,6)
            if c >= 5:
                tiles.append({'x':x,'y':y})
    return tiles 

#@bottle.get('/login'):
connection = pymongo.Connection("mongodb://localhost", safe = True)
db = connection.test
world = db.world
users = db.users
db.users.insert({'x': 0, 'y': 0})

@bottle.get("/generate_screen")
def build_screen():
    screen1 = {}
    screen1['tiles'] = generate_tiles()
    screen1['users'] = [{'x': 0, 'y':0}]
    db.world.insert(screen1)
    screen1.pop('_id', None)
    return {'screen':screen1}

bottle.debug(True)
bottle.run(host='localhost', port=8080)


