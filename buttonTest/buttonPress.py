import pymongo
import bottle

client = pymongo.MongoClient()
db = client.test
app = bottle.Bottle()

@app.route('/buttonTest')
def buttonTest():
	entry = db.location.find_one()
	x = entry["x"]
	y = entry["y"]

	return bottle.template(
		'''
		<head>
		 	<script src="http://ajax.googleapis.com/ajax/libs/jquery/1.11.2/jquery.min.js"></script>
			<script type="text/javascript" src="/static/buttonPress.js"></script>
		</head>
			x: {{x}}, y: {{y}}
		''', 
	x = x, y = y)
	

@app.route('/move/<direction>')
def move(direction):
	entry = db.location.find_one()
	eid = entry["_id"]
	x = entry["x"]
	y = entry["y"]

	if direction == "up":
		db.location.update({"_id": eid}, {"$inc" : {"y" : 1}})
		y+=1
	elif direction == "down":
		db.location.update({"_id": eid}, {"$inc" : {"y" : -1}})
		y-=1
	elif direction == "left":
		db.location.update({"_id": eid}, {"$inc" : {"x" : -1}})
		x-=1
	elif direction == "right":
		db.location.update({"_id": eid}, {"$inc" : {"x" : 1}})
		x+=1

	return bottle.template(
		'''
		<head>
			<script type="text/javascript" src="/static/buttonPress.js"></script>
		</head>
		<body>
			<p>x: {{x}}</p>
			<p>y: {{y}}</p>
		</body>
		''', 
	x = x, y = y)

@app.route('/static/<filename>')
def server_static(filename):
    return bottle.static_file(filename, root='/Users/niteshmenon/Documents')

app.run()