import paho.mqtt.client as mqtt
import time
import json
import requests
import threading

# --- Configuration ---
MQTT_BROKER_URL = "broker.hivemq.com"
MQTT_BROKER_PORT = 1883
FLASK_APP_URL = "http://127.0.0.1:5000" # Change if your Flask app runs elsewhere

# Topics
MQTT_TOPIC_DATA = "irrigateq/esp32/data"
MQTT_TOPIC_STATUS = "irrigateq/esp32/status"
MQTT_TOPIC_COMMAND = "irrigateq/flask/command"

# Test image to upload
TEST_IMAGE_PATH = "static/img/image.png" # Make sure this path is correct

# --- MQTT Client for ESP32 Simulation ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("ESP32 Simulator: Connecté au broker MQTT!")
        client.subscribe(MQTT_TOPIC_COMMAND)
        # Publish online status upon connection
        client.publish(MQTT_TOPIC_STATUS, "online", retain=True)
    else:
        print(f"ESP32 Simulator: Échec de la connexion MQTT, code: {rc}")

def on_message(client, userdata, msg):
    command = msg.payload.decode()
    print(f"ESP32 Simulator: Commande reçue du backend: '{command}'")
    if command == "START":
        print("--- ACTION: Démarrage de la pompe ---")
    elif command == "STOP":
        print("--- ACTION: Arrêt de la pompe ---")

def mqtt_publisher_thread():
    """Publishes sensor data periodically."""
    client = mqtt.Client("esp32_simulator_publisher")
    client.connect(MQTT_BROKER_URL, MQTT_BROKER_PORT, 60)
    
    # Simulate changing moisture
    moisture = 55.0
    direction = -1 # Start by drying out
    
    while True:
        # Simulate data
        data = {
            "temperature": round(22.5 + (time.time() % 10) * 0.1, 2),
            "humidite": round(45.0 + (time.time() % 20) * 0.2, 2),
            "sol": f"{round(moisture, 2)}%" # Send as percentage string
        }
        
        # Publish data
        client.publish(MQTT_TOPIC_DATA, json.dumps(data))
        print(f"ESP32 Simulator: Données envoyées: {data}")
        
        # Update moisture for next cycle to test thresholds
        moisture += direction * 2.5
        if moisture <= 25: # Trigger "too dry"
            direction = 1
        elif moisture >= 65: # Trigger "too wet"
            direction = -1
            
        time.sleep(10) # Send data every 10 seconds

def upload_test_image():
    """Uploads a test image to the Flask server."""
    url = f"{FLASK_APP_URL}/upload-image"
    try:
        with open(TEST_IMAGE_PATH, 'rb') as f:
            files = {'image': (TEST_IMAGE_PATH.split('/')[-1], f, 'image/png')}
            response = requests.post(url, files=files)
            print(f"ESP32 Simulator: Tentative d'upload d'image. Statut: {response.status_code}, Réponse: {response.json()}")
    except FileNotFoundError:
        print(f"Erreur: Le fichier image de test '{TEST_IMAGE_PATH}' n'a pas été trouvé.")
    except Exception as e:
        print(f"Erreur lors de l'upload de l'image: {e}")


if __name__ == "__main__":
    # --- Start MQTT Listener ---
    listener_client = mqtt.Client("esp32_simulator_listener")
    listener_client.on_connect = on_connect
    listener_client.on_message = on_message
    
    # Set Last Will and Testament
    listener_client.will_set(MQTT_TOPIC_STATUS, payload="offline", retain=True)
    
    listener_client.connect(MQTT_BROKER_URL, MQTT_BROKER_PORT, 60)
    # Start listener in a non-blocking thread
    listener_client.loop_start()
    
    # --- Start MQTT Publisher in a separate thread ---
    publisher_thread = threading.Thread(target=mqtt_publisher_thread, daemon=True)
    publisher_thread.start()

    print("\n--- Simulateur ESP32 en cours d'exécution ---")
    print(f"Écoute des commandes sur le topic: {MQTT_TOPIC_COMMAND}")
    print(f"Publication des données des capteurs sur: {MQTT_TOPIC_DATA}")
    print("-------------------------------------------\n")

    # --- Main Loop ---
    try:
        # On startup, upload an image
        print("Action initiale: Upload d'une image de test dans 5 secondes...")
        time.sleep(5)
        upload_test_image()

        # Keep the main thread alive to listen for commands
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nArrêt du simulateur ESP32.")
        # The 'will' message will be sent by the broker upon disconnection
        listener_client.loop_stop()
        listener_client.disconnect()
        print("Client MQTT déconnecté.") 