$(function() {
    // Draws the terrain and people  onto the map
    function drawMap(map){
        var svgContainer = d3.select(".display")
        .append("svg")
        .attr("width", svgSize.width)
        .attr("height", svgSize.height);
        var scales = getScale(gridSize, svgSize);

        drawCells(svgContainer, scales, map.grass, "grass");
        drawCells(svgContainer, scales, map.rock, "rock");
        drawCells(svgContainer, scales, map.lava, "lava");
        drawCells(svgContainer, scales, map.person, "person");

        var groups = { path:svgContainer.append("g"),
        position:svgContainer.append("g") };

        $('#commands').focus();

    }

    function getSvgSize(gridSize, squareLength) {
        var width = gridSize.x * squareLength;
        var height = gridSize.y * squareLength;
        return { width:width, height:height };
    }

    /*
     * function isBorder(x, y, gridSize) {
        return x==0 || y == 0 || x == (gridSize.x-1) || y == (gridSize.y-1);
    }*/

    // Queries to server for the user's view and passes the result to the callback
    function getMap(gridSize, ratios, cb) {
        var screenJSON;
        //Use JQuery to make an AJAX request for the JSON screen object
        $.getJSON('genMap/', function(data) { 
            var map = completeMap(gridSize,ratios,data["tiles"],data["users"]);
            cb(map);
        })
    }

    // Construct the map obj using the terrain and users arrays
    function completeMap(gridSize,ratios,terrain,users){
        var map = { grid:[], grass:[], rock:[], lava:[],person:[] };
        for (var x =0 ; x<gridSize.x;x++){
            map.grid[x]=[];
        } 
        var tiles =[];
        // by default all tiles sent are rock
        for (var i =0;i<terrain.length;i++){
            var x_pos=terrain[i].x;
            var y_pos=terrain[i].y;
            cell ={x:x_pos,y:y_pos,type:"rock"}; 
            tiles.push(cell);
            map.grid[x_pos][y_pos]=cell;
            map["rock"].push(cell);
        }
        
        for (var i =0;i<users.length;i++){
            var x_pos=users[i].x;
            var y_pos=users[i].y;
            cell ={x:x_pos,y:y_pos,type:"person"}; 
            tiles.push(cell);
            map.grid[x_pos][y_pos]=cell;
            map["person"].push(cell);
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
    var squareLength = 40;
    var circleRadius = 15;
    var ratios = { rock:0.05, lava:0.05 };
    var gridSize = { x:20, y:15 };

    var svgSize = getSvgSize(gridSize, squareLength);
    buildMap(gridSize, ratios,drawMap);
}
);
