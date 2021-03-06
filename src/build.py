import pymongo
from pymongo import MongoClient
import bottle
import sys
from bson.objectid import ObjectId
from carry import *
from spawn import *


def build(user, dir):
    pos = {'X': user['X'], 'Y': user['Y'], 'x':user['x'],'y':user['y']}
    build_generator(user, pos)

def can_build(user,dir):
    if dir != "special":
        return False
    pos = {'X': user['X'], 'Y': user['Y'], 'x':user['x'],'y':user['y']}
    return is_generator(pos)

def is_generator(pos):
    if pos['x'] > 0 and pos['y'] > 0 and pos['x'] < SCREEN_LEN  and pos['y'] < SCREEN_LEN:
        pattern = []
        pattern.append({'X':pos['X'],'Y':pos['Y'],'x':pos['x'] -1, 'y':pos['y']-1})
        pattern.append({'X':pos['X'],'Y':pos['Y'],'x':pos['x'] -1, 'y':pos['y']+1})
        pattern.append(pos)
        pattern.append({'X':pos['X'],'Y':pos['Y'],'x':pos['x'] +1, 'y':pos['y']-1})
        pattern.append({'X':pos['X'],'Y':pos['Y'],'x':pos['x'] +1, 'y':pos['y']+1})
        for p in pattern:
            if not rock_at(p):
                return False
        return True
    return False

def build_generator(user, pos):
    pattern = []
    pattern.append({'X':pos['X'],'Y':pos['Y'],'x':pos['x'] -1, 'y':pos['y']-1})
    pattern.append({'X':pos['X'],'Y':pos['Y'],'x':pos['x'] -1, 'y':pos['y']+1})
    pattern.append(pos)
    pattern.append({'X':pos['X'],'Y':pos['Y'],'x':pos['x'] +1, 'y':pos['y']-1})
    pattern.append({'X':pos['X'],'Y':pos['Y'],'x':pos['x'] +1, 'y':pos['y']+1})
    for p in pattern:
        world.update({"X":p['X'],'Y':p['Y']},{'$pull': {'tiles': {'x':p['x'],'y':p['y'],'type':'rock'}}})
        world.update({"X":p['X'],'Y':p['Y']},{'$push': {'tiles': {'x':p['x'],'y':p['y'],'type':'structure'}}})
    gen = {'type': 'generator', 'x': pos['x'], 'y': pos['y'], 'team': user['team']}
    screen = get_screen(user)
    add_lava_if_aligned(gen, screen)
    world.update({"_id":screen['_id']}, {"$push":{"structures": gen}})
        
def add_lava_if_aligned(gen, screen):
    #generators = world.find({'_id':screen['_id']},{'structures' : 1, '_id': 0})
    generators = screen['structures']
    aligned_gens = []
    for g in generators:
        print "g", g
        if g['type'] == 'generator' and g['team'] == gen['team']:
            if g['x'] == gen['x']:         
                a = g['y']
                b = gen['y']
                if g['y'] > gen['y']:
                    a = gen['y']
                    b = g['y']
                for x in range(gen['x']-1,gen['x']+2):
                    for y in range(a+2,b-1):
                        world.update({"X":screen['X'],'Y':screen['Y']},{'$pull':{'tiles':{'x':x, 'y': y,}}})
                        world.update({"X":screen['X'],'Y':screen['Y']},{"$push":{'tiles':{'x':x, 'y': y, 'type': gen['team']+'_lava'}}})
            elif g['y'] == gen['y']:
                a = g['x']
                b = gen['x']
                if g['x'] > gen['x']:
                    a = gen['x']
                    b = g['x']
                for x in range(a+2, b-1):
                    for y in range(gen['y']-1, gen['y']+2):
                        world.update({"X":screen['X'],'Y':screen['Y']},{'$pull':{'tiles':{'x':x, 'y': y,}}})
                        world.update({"X":screen['X'],'Y':screen['Y']},{"$push":{'tiles':{'x':x, 'y': y, 'type': gen['team']+'_lava'}}})
                

