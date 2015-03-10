$(function() {
    var SCREEN_LEN=25;
    var damageSound = new Audio('smash.mp3');
    var scoreSound = new Audio('score.mp3');
    var potionSound = new Audio('potion.mp3');
    var gridSize = { x:SCREEN_LEN, y:SCREEN_LEN };
    // Draws the terrain and people  onto the map
    window.onkeydown = function move(keyEvent) {
        var squareLength = 20;
        var svgSize = getSvgSize(gridSize, squareLength);
        var action  = "";
        if (keyEvent.keyCode == 37) {
            action = "left";
        }
        else if (keyEvent.keyCode == 38) {
            action = "up";
        }
        else if (keyEvent.keyCode == 39) {
	    action = "right";
        }
        else if (keyEvent.keyCode == 40) {
            action = "down";
        }
        // To drop a tile, press a
        //TODO add sounds for pick up/place actons
	else if (keyEvent.keyCode == 32) {
            action = "place_tile";
        }
	else if (keyEvent.keyCode == 65){
	    action = "pickup_left";
	}
	else if (keyEvent.keyCode == 83){
	    action = "pickup_down";
	}
	else if (keyEvent.keyCode == 68){
	    action = "pickup_right";
	}
	else if (keyEvent.keyCode == 87){
	    action = "pickup_up"
	}
	
	if (action == "up" || action == "left" || action == "right" || action == "down"){
	    $.ajax({
		type: "POST",
		url: "/move",
		data: JSON.stringify({"action":action}),
		contentType: "application/json; charset=utf-8",
		dataType: "json",
	    });
	}

	else{
	    $.ajax({
		type: "POST",
		url: "/act",
		data: JSON.stringify({"action":action}),
		contentType: "application/json; charset=utf-8",
		dataType: "json",
	    });
	}

        getMap();
        //getMap(gridSize,drawMap,updatePlayerInfo);
    }
    function drawMap(map){
        $("svg").remove();
        var svgContainer = d3.select(".display")
            .append("svg")
            .attr("width", svgSize.width)
            .attr("height", svgSize.height);
        var scales = getScale(gridSize, svgSize);

        drawCells(svgContainer, scales, map.grass, "grass");
        drawCells(svgContainer, scales, map.rock, "rock");
        drawCells(svgContainer, scales, map.potion, "potion");
        drawCells(svgContainer, scales, map.person, "person");
        drawCells(svgContainer, scales, map.player, "player");//  the current player

        var groups = { path:svgContainer.append("g"),
            position:svgContainer.append("g") };

        $('#commands').focus();

    }

    function getSvgSize(gridSize, squareLength) {
        var width = gridSize.x * squareLength;
        var height = gridSize.y * squareLength;
        return { width:width, height:height };
    }

    function playSound(sound){
        soundObj=null;
        if (sound == "score"){
            soundObj=scoreSound;
        }
        if (sound == "potion"){
            soundObj = potionSound;
        }
        if (sound == "damage"){
            soundObj = damageSound;
        }
        if (soundObj!=null){
            soundObj.pause();
            soundObj.currentTime=0;
            soundObj.play();
        }

    }
    /*
     * function isBorder(x, y, gridSize) {
     return x==0 || y == 0 || x == (gridSize.x-1) || y == (gridSize.y-1);
     }*/

    // Queries to server for the user's view and passes the result to the callback
    //function getMap(gridSize, map_cb,player_info_cb) {
    function getMap() {
        var screenJSON;
        //Use JQuery to make an AJAX request for the JSON screen object
        $.getJSON('load_screen', function(data) { 
            screen_data=data["screen"];

            player_data = data["player"];
	    player_x = player_data["x"];
	    player_y = player_data["y"];
            var map = completeMap(gridSize,screen_data["tiles"],screen_data["users"],player_x,player_y);
            drawMap(map);

	    //print player_data
	    //console.log("SUP ", player_data['x'])
            updatePlayerInfo(player_data);

            sound = data["sound"];
            playSound(sound);
        })
    }

    // Construct the map obj using the terrain and users arrays
    function completeMap(gridSize,terrain,users, player_x, player_y){
	//, current_player){
        var map = { grid:[], grass:[], rock:[], potion:[],person:[],player:[] };
        for (var x =0 ; x<gridSize.x;x++){
            map.grid[x]=[];
        } 
        var tiles =[];
        // by default all tiles sent are rock
        for (var i =0;i<terrain.length;i++){
            var x_pos=terrain[i].x;
            var y_pos=terrain[i].y;
            var type = terrain[i].type;
            cell ={x:x_pos,y:y_pos,type:type}; 
            tiles.push(cell);
            map.grid[x_pos][y_pos]=cell;
            map[type].push(cell);
        }

        for (var i =0;i<users.length;i++){
            var x_pos=users[i].x;
            var y_pos=users[i].y;
	//if (users[i] == currentPlayer){
        if ((x_pos == player_x) && (y_pos == player_y)){
		cell ={x:x_pos,y:y_pos,type:"player"}; 
                console.log("map.grid: ",map.grid);
                map.grid[x_pos][y_pos]=cell;
                map["player"].push(cell);
            }else{
                cell ={x:x_pos,y:y_pos,type:"person"}; 
                console.log("map.grid: ",map.grid);
                map.grid[x_pos][y_pos]=cell;
                map["person"].push(cell);
            }
            tiles.push(cell);
        }
        for (x = 0; x < gridSize.x; x++) {
            map.grid[x] = [];
            for (y = 0; y < gridSize.y; y++) {
                var type="grass";
                var used = false;
                for (var i = 0;i < tiles.length;i++){
                    if (tiles[i].x===x && tiles[i].y === y){
                        used =true;
                    }
                }
                if (!used){
                    var cell = { x:x, y:y , type:type };
                    map.grid[x][y] = cell;
                    map[type].push(cell);
                }
            }

        }
        return map;
    }

    function getScale(gridSize, svgSize) {
        var xScale = d3.scale.linear().domain([0,gridSize.x]).range([0,svgSize.width]);
        var yScale = d3.scale.linear().domain([0,gridSize.y]).range([0,svgSize.height]);
        return { x:xScale, y:yScale };
    }

    function updatePlayerInfo(playerData){
        var health = document.getElementById("health");
        health.value=playerData["health"];

        var score = document.getElementById("score");
        score.innerHTML = playerData["score"];
    }

    function drawCells(svgContainer, scales, data, cssClass) {
        var gridGroup = svgContainer.append("g");
        var cells = gridGroup.selectAll("rect")
            .data(data)
            .enter()
            .append("rect");
        var cellAttributes = cells
            .attr("x", function (d) { return scales.x(d.x); })
            .attr("y", function (d) { return scales.y(d.y); })
            .attr("width", function (d) { return squareLength; })
            .attr("height", function (d) { return squareLength; })
            .attr("class", cssClass);
    }
    var squareLength = 20;
    var gridSize = { x:SCREEN_LEN, y:SCREEN_LEN };

    var svgSize = getSvgSize(gridSize, squareLength);
    getMap();
    //       getMap(gridSize, drawMap,updatePlayerInfo);
    window.setInterval(function(){
        getMap();
        //            getMap(gridSize,drawMap,updatePlayerInfo);
    },500);
}
);
