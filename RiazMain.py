class Screen
  9     def __init__(self, X , Y):
 10         self.X = X
 11         self.Y = Y
 12         self.tiles = genTiles() 
 13         self.users = 
 14 
 15 def genTiles():
 16     #generate 20 random tiles
 17     screen=[]
 18     for x in range(20):
 19         for y in range(20):
 20             c = randint(1, 6)
 21             if c >= 5:
 22                 screen.append({'x':x,'y':y}
 23     return  {"screen":screen}
