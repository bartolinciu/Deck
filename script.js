
let ws;
function onmessage(message){
	console.log(message.data);
}

function init(){
	//alert("Hello");
	let url = document.getElementById( "script" ).src;
	console.log(url);
	url = url.substr( url.startsWith( "https://" ) ? 8: url.startsWith( "http://" ) ? 7 : 0 )
	console.log(url);
	url = url.substr( 0, url.length - 10 );
	console.log(url);

	ws = new WebSocket("ws://192.168.1.163:8765");
	ws.onmessage = onmessage;
	//alert(ws);
}

function Click(id){
	ws.send(id);
}