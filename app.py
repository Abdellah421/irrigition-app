from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_socketio import SocketIO, emit
import os
import datetime
import json
import paho.mqtt.client as mqtt
import threading
import time
import requests
from bs4 import BeautifulSoup
import urllib.parse
from firebase_config import (
    create_user, get_user_by_credentials, get_user_by_id, update_user_profile,
    add_notification, get_user_notifications, add_irrigation_event, check_user_exists
)

# Translation dictionary for Arabic and French
translations = {
    'ar': {
        'login': 'تسجيل الدخول',
        'register': 'إنشاء حساب',
        'profile': 'الملف الشخصي',
        'notifications': 'الإشعارات',
        'guide': 'الدليل العملي',
        'logout': 'خروج',
        'welcome': 'مرحباً',
        'manual_control': 'التحكم اليدوي',
        'start': 'ابدأ',
        'stop': 'أوقف',
        'latest_image': 'أحدث صورة للنبتة',
        'no_image': 'لم يتم تحميل أي صورة بعد.',
        'update': 'تحديث',
        'home': 'الرئيسية',
        'esp32_conn': 'اتصال ESP32',
        'esp32': 'ESP32',
        'esp32_ip': 'عنوان ESP32',
        'last_update': 'آخر تحديث',
        'never': 'أبداً',
        'disconnected': 'غير متصل',
        'sensor_stats': 'إحصائيات المستشعرات',
        'temperature': 'درجة الحرارة',
        'humidity': 'الرطوبة',
        'soil': 'التربة',
        'light': 'الضوء',
        'voice_control': 'التحكم الصوتي',
        'voice_instruction': 'اضغط على الزر وقل "ابدأ الري"، "أوقف الري"، أو "تحقق من الحالة".',
        'activate': 'تفعيل',
        'manual_instruction': 'استخدم الأزرار أدناه للتحكم في الري يدوياً.',
        'notifications_section': 'الإشعارات',
        'guide_section': 'الدليل العملي',
        'humidity_chart': 'تطور الرطوبة',
        'weekdays': ['الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد'],
        'humidity_label': 'الرطوبة (%)',
    },
    'fr': {
        'login': 'Connexion',
        'register': 'Créer un compte',
        'profile': 'Profil',
        'notifications': 'Notifications',
        'guide': 'Guide pratique',
        'logout': 'Quitter',
        'welcome': 'Bienvenue',
        'manual_control': 'Commande Manuelle',
        'start': 'Démarrer',
        'stop': 'Arrêter',
        'latest_image': 'Dernière Image de la Plante',
        'no_image': "Aucune image n'a encore été téléchargée.",
        'update': 'Mettre à jour',
        'home': 'Accueil',
        'esp32_conn': 'Connexion ESP32',
        'esp32': 'ESP32',
        'esp32_ip': 'IP ESP32',
        'last_update': 'Dernière mise à jour',
        'never': 'Jamais',
        'disconnected': 'Déconnecté',
        'sensor_stats': 'Statistiques capteurs',
        'temperature': 'Température',
        'humidity': 'Humidité',
        'soil': 'Sol',
        'light': 'Lumière',
        'voice_control': 'Commande Vocale',
        'voice_instruction': 'Cliquez sur le bouton et dites "Démarre l\'irrigation", "Arrête l\'irrigation", ou "Vérifie le statut".',
        'activate': 'Activer',
        'manual_instruction': 'Utilisez les boutons ci-dessous pour contrôler l\'irrigation manuellement.',
        'notifications_section': 'Notifications',
        'guide_section': 'Guide pratique',
        'humidity_chart': "Évolution de l'humidité",
        'weekdays': ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'],
        'humidity_label': 'Humidité (%)',
    }
}

# --- Uploads Configuration ---
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
socketio = SocketIO(app, cors_allowed_origins="*")

# Create upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Simulated sensor data
sensor_data = {
    'sol': 'Normal',
    'humidite': '45%',
    'temperature': '22°C',
    'lumiere': 'Modérée',
}

# Simulated notifications
notifications = [
    "Le sol est trop sec !",
    "Pluie prévue demain, pensez à protéger vos plantes."
]

# Simulated guide
guides = {
    'Tomate': "Arrosez régulièrement, évitez l'excès d'eau.",
    'Menthe': "Préfère l'ombre partielle et un sol humide.",
    'default': "Consultez les besoins spécifiques de votre plante."
}

# Store latest ESP32 data in a file (data.json) for persistence
DATA_FILE = "data.json"

# --- MQTT Configuration ---
MQTT_BROKER_URL = "broker.hivemq.com"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC_DATA = "irrigateq/esp32/data"
MQTT_TOPIC_STATUS = "irrigateq/esp32/status"
MQTT_TOPIC_COMMAND = "irrigateq/flask/command"

# Stockage des dernières données reçues via MQTT
mqtt_data_cache = {
    "temperature": None,
    "humidite": None,
    "sol": None,
    "last_update": None,
    "mqtt_backend_status": "Connecting...",
    "esp32_mqtt_status": "Unknown"
}

# --- Fonctions Callbacks MQTT ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connecté au broker MQTT!")
        client.subscribe(MQTT_TOPIC_DATA)
        client.subscribe(MQTT_TOPIC_STATUS)
        mqtt_data_cache["mqtt_backend_status"] = "Connecté au broker"
        # Emit connection status to all clients
        socketio.emit('mqtt_status', {'status': 'connected'})
    else:
        print(f"Échec de la connexion MQTT, code: {rc}")
        mqtt_data_cache["mqtt_backend_status"] = f"Échec connexion broker ({rc})"
        socketio.emit('mqtt_status', {'status': 'disconnected', 'error': rc})

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        if msg.topic == MQTT_TOPIC_DATA:
            data = json.loads(payload)
            mqtt_data_cache["temperature"] = data.get("temperature")
            mqtt_data_cache["humidite"] = data.get("humidite")
            mqtt_data_cache["sol"] = data.get("sol")
            mqtt_data_cache["last_update"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print("Données capteurs mises à jour:", mqtt_data_cache)
            
            # Emit sensor data to all connected clients via WebSocket
            socketio.emit('sensor_update', {
                'temperature': data.get("temperature"),
                'humidite': data.get("humidite"),
                'sol': data.get("sol"),
                'timestamp': mqtt_data_cache["last_update"]
            })

        elif msg.topic == MQTT_TOPIC_STATUS:
            mqtt_data_cache["esp32_mqtt_status"] = payload
            print("Statut ESP32 reçu:", payload)
            # Emit ESP32 status to all clients
            socketio.emit('esp32_status', {'status': payload})

    except Exception as e:
        print(f"Erreur lors du traitement du message MQTT: {e}")

# --- Configuration Client MQTT ---
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.on_disconnect = lambda client, userdata, rc: print("Client MQTT déconnecté avec code:", rc)

# --- Fonction pour faire tourner le client MQTT dans un thread séparé ---
def mqtt_client_thread():
    while True:
        try:
            print(f"Tentative de connexion au broker MQTT {MQTT_BROKER_URL}:{MQTT_BROKER_PORT}")
            mqtt_client.connect(MQTT_BROKER_URL, MQTT_BROKER_PORT, 60)
            mqtt_client.loop_forever()
        except Exception as e:
            print(f"Erreur de connexion MQTT: {e}. Reconexion dans 5 secondes...")
            mqtt_data_cache["mqtt_backend_status"] = f"Déconnecté, reconnexion... ({e})"
            socketio.emit('mqtt_status', {'status': 'reconnecting', 'error': str(e)})
            time.sleep(5)

mqtt_thread = threading.Thread(target=mqtt_client_thread, daemon=True)
mqtt_thread.start()

# --- WebSocket Event Handlers ---
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    # Send current data to newly connected client
    emit('current_data', mqtt_data_cache)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('request_data')
def handle_request_data():
    emit('current_data', mqtt_data_cache)

@app.route('/get_data')
def get_data():
    return jsonify(mqtt_data_cache)

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_or_phone = request.form['email_or_phone']
        password = request.form['password']
        user = get_user_by_credentials(email_or_phone, password)
        if user:
            session['user_id'] = user['user_id']
            return redirect(url_for('dashboard'))
        else:
            flash('Identifiants invalides')
    lang = session.get('lang', 'ar')
    t = translations[lang]
    return render_template('login.html', lang=lang, t=t)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        superficie = request.form['superficie']
        plante = request.form['plante']
        email_or_phone = request.form['email_or_phone']
        password = request.form['password']
        if check_user_exists(email_or_phone):
            flash('Utilisateur déjà existant')
        else:
            user_data = {
                'nom': nom,
                'prenom': prenom,
                'superficie': superficie,
                'plante': plante,
                'email_or_phone': email_or_phone,
                'password': password
            }
            try:
                create_user(user_data)
                flash('Compte créé, veuillez vous connecter')
                return redirect(url_for('login'))
            except Exception as e:
                flash(f'Erreur lors de la création du compte: {str(e)}')
    lang = session.get('lang', 'ar')
    t = translations[lang]
    return render_template('register.html', lang=lang, t=t)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = get_user_by_id(session['user_id'])
    if not user:
        session.pop('user_id', None)
        return redirect(url_for('login'))
    notifications = get_user_notifications(session['user_id'], limit=10)
    notification_texts = [n['text'] for n in notifications]
    plant_name = user.get('plante', 'default')
    lang = session.get('lang', 'ar')
    print('Current language:', lang)
    t = translations[lang]
    print('DEBUG t:', t)
    print('DEBUG t[weekdays]:', t.get('weekdays'))
    return render_template('dashboard.html', user=user, notifications=notification_texts, plant_name=plant_name, lang=lang, t=t)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = get_user_by_id(session['user_id'])
    if not user:
        session.pop('user_id', None)
        return redirect(url_for('login'))
    if request.method == 'POST':
        profile_data = {
            'nom': request.form['nom'],
            'prenom': request.form['prenom'],
            'superficie': request.form['superficie'],
            'plante': request.form['plante']
        }
        try:
            update_user_profile(session['user_id'], profile_data)
            flash('Profil mis à jour')
        except Exception as e:
            flash(f'Erreur lors de la mise à jour: {str(e)}')
    lang = session.get('lang', 'ar')
    t = translations[lang]
    return render_template('profile.html', user=user, lang=lang, t=t)

@app.route('/notifications')
def notifications_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    notifications = get_user_notifications(session['user_id'], limit=50)
    notification_texts = [n['text'] for n in notifications]
    lang = session.get('lang', 'ar')
    t = translations[lang]
    return render_template('notifications.html', notifications=notification_texts, lang=lang, t=t)

@app.route('/guide')
def guide():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = get_user_by_id(session['user_id'])
    if not user:
        session.pop('user_id', None)
        return redirect(url_for('login'))
    plante = user['plante'] if user else 'default'
    guide = guides.get(plante, guides['default'])
    lang = session.get('lang', 'ar')
    t = translations[lang]
    return render_template('guide.html', guide=guide, lang=lang, t=t)

@app.route('/voice-command', methods=['POST'])
def voice_command():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Not authenticated"}), 401

    command = request.json.get('command')
    response_message = "Commande non reconnue"

    if command == "start irrigation":
        mqtt_client.publish(MQTT_TOPIC_COMMAND, "START")
        response_message = "Ok, démarrage de l'irrigation."
        
        # Log irrigation event to Firebase
        add_irrigation_event(session['user_id'], 'start', {
            'command': 'manual',
            'moisture_level': 25,
            'temperature': 22.5
        })
        
        # Emit irrigation command to all clients
        socketio.emit('irrigation_command', {'command': 'start', 'message': response_message})
        
    elif command == "stop irrigation":
        mqtt_client.publish(MQTT_TOPIC_COMMAND, "STOP")
        response_message = "Ok, arrêt de l'irrigation."
        
        # Log irrigation event to Firebase
        add_irrigation_event(session['user_id'], 'stop', {'command': 'voice'})
        
        # Emit irrigation command to all clients
        socketio.emit('irrigation_command', {'command': 'stop', 'message': response_message})
        
    elif command == "check status":
        return jsonify({
            "status": "success",
            "message": f"Voici le dernier état : Température {mqtt_data_cache.get('temperature')}, Humidité du sol {mqtt_data_cache.get('sol')}, Humidité de l'air {mqtt_data_cache.get('humidite')}.",
            "data": mqtt_data_cache
        })

    return jsonify({"status": "success", "message": response_message})

@app.route('/upload-image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"status": "error", "message": "No image part in the request"}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No image selected for uploading"}), 400
    if file and allowed_file(file.filename):
        filename = datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '_' + file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # Add notification to Firebase if user is logged in
        if 'user_id' in session:
            add_notification(session['user_id'], f"Nouvelle image téléchargée: {filename}")
        
        # Emit new image notification to all clients
        socketio.emit('new_image', {'filename': filename})
        return jsonify({"status": "success", "message": "Image successfully uploaded"}), 201
    else:
        return jsonify({"status": "error", "message": "Allowed image types are -> png, jpg, jpeg, gif"}), 400

@app.route('/get_latest_image')
def get_latest_image():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Not authenticated"}), 401

    latest_image_url = None
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        image_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if allowed_file(f)]
        if image_files:
            latest_file = sorted(
                image_files,
                key=lambda f: os.path.getmtime(os.path.join(app.config['UPLOAD_FOLDER'], f)),
                reverse=True
            )[0]
            latest_image_url = url_for('static', filename='uploads/' + latest_file)

    return jsonify({"status": "success", "latest_image_url": latest_image_url})

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in ['ar', 'fr']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('dashboard'))

if __name__ == '__main__':
    try:
        socketio.run(app, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print("Arrêt de l'application Flask et du client MQTT.")
        mqtt_client.loop_stop()
        mqtt_client.disconnect() 