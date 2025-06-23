import firebase_admin
from firebase_admin import credentials, firestore
import os
from datetime import datetime
import uuid

# Initialize Firebase Admin SDK
def initialize_firebase():
    """Initialize Firebase Admin SDK with service account credentials"""
    try:
        # Check if Firebase app is already initialized
        firebase_admin.get_app()
        print("Firebase already initialized")
    except ValueError:
        # Initialize Firebase with service account key
        # You need to place your serviceAccountKey.json in the project root
        cred_path = "serviceAccountKey.json"
        
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("Firebase initialized successfully")
        else:
            print(f"Warning: {cred_path} not found. Please add your Firebase service account key.")
            # For development, you can use default credentials
            firebase_admin.initialize_app()
            print("Firebase initialized with default credentials")

# Get Firestore client
def get_db():
    """Get Firestore database client"""
    return firestore.client()

# User Management Functions
def create_user(user_data):
    """Create a new user in Firestore"""
    db = get_db()
    
    # Generate a unique user ID
    user_id = str(uuid.uuid4())
    
    # Prepare user document
    user_doc = {
        'user_id': user_id,
        'nom': user_data['nom'],
        'prenom': user_data['prenom'],
        'email_or_phone': user_data['email_or_phone'],
        'password': user_data['password'],  # In production, hash this password
        'superficie': user_data['superficie'],
        'plante': user_data['plante'],
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
        'thresholds': {
            'enabled': False,
            'min_moisture': 30,
            'max_moisture': 60
        },
        'notifications': [],
        'irrigation_events': []
    }
    
    # Save to Firestore
    db.collection('users').document(user_id).set(user_doc)
    
    # Also save with email/phone as key for easy login lookup
    db.collection('user_credentials').document(user_data['email_or_phone']).set({
        'user_id': user_id,
        'password': user_data['password']
    })
    
    return user_id

def get_user_by_credentials(email_or_phone, password):
    """Get user by email/phone and password"""
    db = get_db()
    
    # First, check credentials
    cred_doc = db.collection('user_credentials').document(email_or_phone).get()
    
    if not cred_doc.exists:
        return None
    
    cred_data = cred_doc.to_dict()
    
    if cred_data['password'] != password:
        return None
    
    # Get user data
    user_doc = db.collection('users').document(cred_data['user_id']).get()
    
    if not user_doc.exists:
        return None
    
    return user_doc.to_dict()

def get_user_by_id(user_id):
    """Get user by user ID"""
    db = get_db()
    user_doc = db.collection('users').document(user_id).get()
    
    if not user_doc.exists:
        return None
    
    return user_doc.to_dict()

def update_user_profile(user_id, profile_data):
    """Update user profile"""
    db = get_db()
    
    update_data = {
        'nom': profile_data['nom'],
        'prenom': profile_data['prenom'],
        'superficie': profile_data['superficie'],
        'plante': profile_data['plante'],
        'updated_at': datetime.now()
    }
    
    db.collection('users').document(user_id).update(update_data)

def update_user_thresholds(user_id, thresholds_data):
    """Update user irrigation thresholds"""
    db = get_db()
    
    update_data = {
        'thresholds': thresholds_data,
        'updated_at': datetime.now()
    }
    
    db.collection('users').document(user_id).update(update_data)

def add_notification(user_id, notification_text):
    """Add a notification to user's notification history"""
    db = get_db()
    
    notification = {
        'id': str(uuid.uuid4()),
        'text': notification_text,
        'timestamp': datetime.now(),
        'read': False
    }
    
    # Add to user's notifications array
    user_ref = db.collection('users').document(user_id)
    user_ref.update({
        'notifications': firestore.ArrayUnion([notification])
    })

def get_user_notifications(user_id, limit=50):
    """Get user's notifications"""
    db = get_db()
    user_doc = db.collection('users').document(user_id).get()
    
    if not user_doc.exists:
        return []
    
    user_data = user_doc.to_dict()
    notifications = user_data.get('notifications', [])
    
    # Sort by timestamp (newest first) and limit
    notifications.sort(key=lambda x: x['timestamp'], reverse=True)
    return notifications[:limit]

def add_irrigation_event(user_id, event_type, details=None):
    """Add an irrigation event to user's history"""
    db = get_db()
    
    event = {
        'id': str(uuid.uuid4()),
        'type': event_type,  # 'start', 'stop', 'auto_start', 'auto_stop'
        'timestamp': datetime.now(),
        'details': details or {}
    }
    
    # Add to user's irrigation events array
    user_ref = db.collection('users').document(user_id)
    user_ref.update({
        'irrigation_events': firestore.ArrayUnion([event])
    })

def get_irrigation_events(user_id, limit=100):
    """Get user's irrigation events history"""
    db = get_db()
    user_doc = db.collection('users').document(user_id).get()
    
    if not user_doc.exists:
        return []
    
    user_data = user_doc.to_dict()
    events = user_data.get('irrigation_events', [])
    
    # Sort by timestamp (newest first) and limit
    events.sort(key=lambda x: x['timestamp'], reverse=True)
    return events[:limit]

def check_user_exists(email_or_phone):
    """Check if a user with given email/phone already exists"""
    db = get_db()
    doc = db.collection('user_credentials').document(email_or_phone).get()
    return doc.exists

def test_connection():
    """Test Firebase connection by attempting to access Firestore"""
    try:
        db = get_db()
        # Try to access a collection to test connection
        db.collection('test').limit(1).get()
        return True
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False

# Initialize Firebase when module is imported
initialize_firebase() 