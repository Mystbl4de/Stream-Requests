var socket = new WebSocket(API_Socket);
socket.onopen = function()
{
	// Format your Authentication Information
	var auth = {
		author: "AnkhHeart",
		website: "https://Streamlabs.com",
		api_key: API_Key,
		events: ["NEW"]
	}
	socket.send(JSON.stringify(auth));
};
socket.onmessage = function (message)
{
	let input = JSON.parse(message.data);
	if (input['event'] == "NEW"){
		let mylist = JSON.parse(input['data']);
		let output = "";
		mylist.forEach(element => {
			output += element + "<br>";
		});
		document.body.innerHTML = output;
	}

}
