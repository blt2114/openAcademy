import pymongo
from pymongo import MongoClient 
import sys
from random import randint
import time

SCREEN_LEN = 25 #number of spaces per row and column
WORLD_LEN = 3

# The minimum number of these resources on each screen, below which they
# will begin replenishing automatically.
min_mines=5
min_potions=5
min_arrows=7

# establish connection with game db
client=MongoClient()
world=client.game.world
users=client.game.users
RED = {'X': 0, 'Y': 1}
BLUE = {'X':2, 'Y': 1}

def add_resource(X,Y,resource_type):
    x=randint(0,SCREEN_LEN-1)
    y=randint(0,SCREEN_LEN-1)
    pos={"X":X,"Y":Y,"y":y,"x":x}
    while True:
        write_result=world.update(
            {
                "X":pos["X"],
                "Y":pos["Y"],
                "tiles":{
                    "$not":{
                        "$elemMatch":{
                            "x":pos['x'],
                            "y":pos['y'],
                        }
                    }
                },
                "users":{
                    "$not":{
                        "$elemMatch":{
                            "x":pos['x'],
                            "y":pos['y'],
                        }
                    }
                }
            },{
                "$push":{
                    "tiles":{'type':resource_type,'x':x,'y':y}
                }
            },
            False # no upserting
        )
        if write_result["updatedExisting"]:
            break
        else:
            x=randint(0,SCREEN_LEN-1)
            y=randint(0,SCREEN_LEN-1)
            pos={"X":X,"Y":Y,"y":y,"x":x}

def replenish():
    for X in range(0,WORLD_LEN):
        for Y in range(0,WORLD_LEN):
            screen = world.find_one({'X': X, 'Y':Y})
            tiles = screen['tiles']
            num_mines=0
            num_potions=0
            num_arrows=0
            for tile in tiles:
                if tile['type'] == 'potion':
                    num_potions+=1
                    continue
                if tile['type'] == 'p_arrow':
                    num_arrows+=1
                    continue
                if tile['type'] == 'p_mine':
                    num_mines+=1
                    continue

            print "num_arrow"+ str(num_arrows)
            print "min_potions"+ str(min_potions)
            if num_mines <min_mines:
                add_resource(X,Y,'p_mine')
            if num_potions <min_potions:
                add_resource(X,Y,'potion')
            if num_arrows <min_arrows:
                print "replenishing arrows"
                add_resource(X,Y,'p_arrow')

while True:
    time.sleep(5)
    replenish()

