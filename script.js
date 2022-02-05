
let ws;
function onmessage(message){
	let labels = JSON.parse(message.data)
	for( let i=1; i <= 16; i++ ){
		document.getElementById("Button"+i).innerText = labels[i-1];
	}
}

function init(){
	//alert("Hello");
	let url = document.getElementById( "script" ).src;
	console.log(url);
	url = url.substr( url.startsWith( "https://" ) ? 8: url.startsWith( "http://" ) ? 7 : 0 )
	console.log(url);
	url = url.substr( 0, url.length - 15 );
	console.log(url);

	ws = new WebSocket("ws://" + url + ":8765");
	ws.onmessage = onmessage;
	ws.onopen = function(){
		ws.send("get");
	}
	
	//alert(ws);
}

function Click(id){
	ws.send(id);
}