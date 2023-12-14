function setCookie(cname, cvalue, exdays) {
  const d = new Date();
  d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
  let expires = "expires="+d.toUTCString();
  document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

function getCookie(cname) {
  let name = cname + "=";
  let ca = document.cookie.split(';');
  for(let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) == ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
}

function checkCookie() {
  let user = getCookie("username");
  if (user != "") {
    alert("Welcome again " + user);
  } else {
    user = prompt("Please enter your name:", "");
    if (user != "" && user != null) {
      setCookie("username", user, 365);
    }
  }
}


let ws;
let pongReceived = false;
let pingSent = false;
let reconnect = false;
function onmessage(message){
	if( message.data == "pong" ){
		pongReceived = true;
		return;
	}

	if(message.data == "reject"){
		alert("Access denied");
		return;
	}

	if( message.data == "reconnect" ){
		reconnect = true;
		return;
	}

	else if( message.data == "authorize" ){
		passcode = prompt("Enter pairing code");
		ws.send( "passcode:" + passcode );
		return;
	}

	splitted_message = message.data.split(":")

	if( splitted_message[0] == "accept" || splitted_message[0]=="merge" )
	{
		setCookie( "uuid", splitted_message[1], 365 );
		ws.send("identify:" + splitted_message[1])
		return;
	}
	//alert(message.data);
	let buttons = JSON.parse(message.data);
	for( let i=1; i <= 16; i++ ){
		let button = buttons[i-1];
		document.getElementById("Button" + i).innerHTML = ""
		if( button.image )
		{
			document.getElementById("Button"+i).innerHTML += "<img style=\"object-fit:contain;width:100%;height:80%;\" src = \"" + button.image + "\"><br>";
		}
		document.getElementById("Button"+i).innerHTML += button.name;
		console.log(button)
		
	}
}


function ping(){
	if( pingSent && !pongReceived ){
		setTimeout(init, 5000);
		return;
	}
	ws.send("ping");
	pingSent = true;
	pongReceived = false;
	setTimeout(ping, 1000);
}

function authorize(){
	ws.send( "request:" );
}

function onopen(event){
	let uuid = getCookie("uuid");
	if( uuid == "" ){
		authorize();
	}
	else{
		ws.send( "identify:" + uuid );
	}
}

function onclose(event){
	if( reconnect ){
		setTimeout( init, 100 );
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
	ws.onopen = onopen;
	ws.onclose = onclose;

	//alert(ws);

	//pingSent = false;
	//setTimeout(ping, 1000);
}

function Click(id){
	ws.send(id);
}