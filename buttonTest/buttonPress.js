window.onkeydown = function move(keyEvent) {
	console.log(keyEvent.keyCode);
	if (keyEvent.keyCode == 37) {
		window.location.replace("/move/left");
	}
	else if (keyEvent.keyCode == 38) {
		window.location.replace("/move/up");
	}
	else if (keyEvent.keyCode == 39) {
		window.location.replace("/move/right");
	}
	else if (keyEvent.keyCode == 40) {
		window.location.replace("/move/down");
	}
};