#Driver Function
import pymongo
import bottle #micro-framework
import sys
import random


#route to get the screen rendering
@bottle.get("/genMap/")
def retrunScreen():
        #generate 20 random tiles
        for i in range (1,20):
                num1=random.randint(0,19);
                num2=random.randint(0,19);
                tile = {'x':num1,'y':num2,'type':{}}
                screen.append(tile) 
                print screen
                return  screen
bottle.debug(True)
bottle.run(host='localhost', port=8080)


