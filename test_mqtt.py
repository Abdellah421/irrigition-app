import paho.mqtt.client as mqtt
import json
import time

# MQTT Configuration
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC_DATA = "irrigateq/esp32/data"
MQTT_TOPIC_STATUS = "irrigateq/esp32/status"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker!")
    else:
        print(f"Failed to connect, return code {rc}")

# Create MQTT client
client = mqtt.Client()
client.on_connect = on_connect

# Connect to broker
print(f"Connecting to MQTT broker {MQTT_BROKER}...")
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Start the loop
client.loop_start()

try:
    # First send online status
    print("Sending online status...")
    client.publish(MQTT_TOPIC_STATUS, "online")
    
    # Send some test sensor data
    test_data = {
        "temperature": "25.5",
        "humidite": "65",
        "sol": "Humide",
        "lumiere": "Élevée"
    }
    
    print("Sending test sensor data...")
    client.publish(MQTT_TOPIC_DATA, json.dumps(test_data))
    
    # Keep the script running for a moment to ensure message is sent
    time.sleep(2)
    
except KeyboardInterrupt:
    print("Test stopped by user")
finally:
    # Send offline status before disconnecting
    client.publish(MQTT_TOPIC_STATUS, "offline")
    client.loop_stop()
    client.disconnect()
    print("Disconnected from MQTT broker") 