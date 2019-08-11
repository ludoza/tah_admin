from flask import current_app
import paho.mqtt.client as mqtt



# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    #current_app.logger.debug(f'Connected with result code {rc}') # eish need context to use current_app here
    MQTTClient._connected = True
    if MQTTClient._on_connect:
        MQTTClient._on_connect(client, userdata, flags, rc)



# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    #current_app.logger.debug(msg.topic+" "+str(msg.payload))
    pass

def on_disconnect(client, userdata, rc):
    #current_app.logger.debug(f'Disconnect with result code {rc}')
    MQTTClient._connected = False



def on_publish(client, userdata, mid):
    #current_app.logger.debug('Publish {mid}')
    pass



def on_connect_publish_payloads(client, userdata, flags, rc):
    MQTTClient.publish_payloads()

 
 
class MQTTClient:
    _client = None
    _connected = False
    _on_connect = None
    _payloads = [] # contains tuples of ( 'topic', 'payload', )



    @classmethod
    def publish(cls, topic, payload):
        cls._payloads.append((topic, payload,))



    @classmethod
    def create_client(cls, cb_on_connect = None):
        if cls._client:
            del cls._client
        client = mqtt.Client()
        cls._client = client
        
        client.enable_logger(current_app.logger)
        client.on_connect = on_connect
        if cb_on_connect:
            cls._on_connect = cb_on_connect
        client.on_disconnect = on_disconnect
        client.on_message = on_message
        client.on_publish = on_publish
        client.username_pw_set('rugraat', 'rugraat')
        client.connect(current_app.config['MQTT_SERVER'], current_app.config['MQTT_PORT'], 60)
        client.loop_start()


        
    @classmethod
    def publish_payloads(cls):
        if not cls._connected:
            cls.create_client(on_connect_publish_payloads)
            return False
        if len(cls._payloads) == 0:
            return True
        
        payload = cls._payloads.pop()
        while payload:
            cls._client.publish(topic=payload[0], payload=payload[1])
            if cls._connected:
                if len(cls._payloads) == 0:
                    payload = False
                else:
                    payload = cls._payloads.pop()    
            else:
                cls.create_client(on_connect_publish_payloads)
                return False
        return True