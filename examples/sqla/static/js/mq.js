/* global Paho */
console.log('init mq js module.')

function guidGenerator() {
    var S4 = function() {
       return (((1+Math.random())*0x10000)|0).toString(16).substring(1);
    };
    return (S4()+S4()+"-"+S4()+"-"+S4()+"-"+S4()+"-"+S4()+S4()+S4());
}

//var location = { hostname: window.location.hostname, port: window.location.port }
// Create a client instance
//host.port = location.port == "" ? 80 : Number(location.port)
// var client = new Paho.Client(window.location.hostname, 8081, "clientId-"+ guidGenerator());

var mqtt_server = 'planeteer.mooo.com';
var mqtt_port = 15675;
var client = new Paho.Client(mqtt_server, mqtt_port, "/ws", "clientId-"+ guidGenerator());


// set callback handlers
client.onConnectionLost = onConnectionLost;
client.onMessageArrived = onMessageArrived;

// connect the client
client.connect({userName: 'rugraat', password: 'rugraat', onSuccess:onConnect});


// called when the client connects
function onConnect() {
  // Once a connection has been made, make a subscription and send a message.
  console.log("onConnect");
  var channel = window.location.pathname.split('/').slice(-2)[0];
  client.subscribe(channel);
  var message = new Paho.Message("Hello");
  message.destinationName = channel;
  client.send(message);
}

// called when the client loses its connection
function onConnectionLost(responseObject) {
  if (responseObject.errorCode !== 0) {
    console.log("onConnectionLost:"+responseObject.errorMessage);
  }
  client.connect({onSuccess:onConnect});
}

// called when a message arrives
function onMessageArrived(message) {
  console.log("onMessageArrived:"+message.payloadString);
  var parts = message.payloadString.split(' ');
  var cmd =  parts[0];
  var id_ = parts[1]
  if (cmd == 'update'[0] || cmd == 'insert'[0]) {
       var model = window.location.pathname.split('/').slice(-2)[0];
      $.get('tah/model/' + id_).done(function(data){
          //var $row = $( "td[class=col-id]:contains(" + data.id + ")" ).parent();
          var $row = $( "td[class=col-id]").filter(function() {
            return $(this).text().trim() === id_;
            }).parent();
          $.each(Object.keys(data), function(index, key) {
              var $td = $row.find("td[class=col-" + key +"]")
              $td.find(':first').text(data[key]);
          })
          //$row.fadeTo(100, 0.3, function() { $(this).fadeTo(500, 1.0); });
          var oldbc = $row.css('backgroundColor')
          $row.animate({backgroundColor: '#DAF7A6'}, 100, 'swing', function() { $(this).animate({backgroundColor: oldbc}, 500, 'swing'); } );
      })
  }
}