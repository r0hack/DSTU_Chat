/* 
Created by: Roma and Maga

Name: DSTU-Chat
*/

var instanse = false;
var state = 0;
var mes;

function Chat () {
    this.update = updateChat;
    this.send = sendChat;
	this.getState = getStateOfChat;
}


function getStateOfChat(){
	if(!instanse){
		 instanse = true;
		 $.ajax({
			   type: "POST",
  			   url: "process",
			   data: {  
			   			'function': 'getState',
						},
			   dataType: "json",
			
			   success: function(data){
				   state = data.state;
				   instanse = false;
			   },
			});
	}	 
}


function updateChat(){
	 if(!instanse){
		 instanse = true;
	     $.ajax({
			   type: "POST",
  			   url: "process",
			   data: {  
  						'function': 'update',
  						'state': state
						},
			   dataType: "json",
			   success: function(data){
				   if(data.text){
						for (var i = 0; i < data.text.length; i++) {
                            $('#chat-area').append($("<p>"+ data.text[i] +"</p>"));
                        }								  
				   }
				   document.getElementById('chat-area').scrollTop = document.getElementById('chat-area').scrollHeight;
				   instanse = false;
				   state = data.state;
			   },
			});
	 }
	 else {
		 setTimeout(updateChat, 1500);
	 }
}


function sendChat(message, nickname)
{       
    updateChat();
     $.ajax({
		   type: "POST",
  		   url: "process",
  		   data: {  
  		   			'function': 'send',
  					'message': message,
  					'nickname': nickname
  				 },
		   dataType: "json",
		   success: function(data){
			   updateChat();
		   },
		});
}
