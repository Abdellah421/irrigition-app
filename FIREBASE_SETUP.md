# Firebase Setup Guide for Smart Irrigation App

## Prerequisites
- A Google account
- Python 3.7+ installed
- Firebase project created

## Step 1: Create a Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create a project" or "Add project"
3. Enter a project name (e.g., "smart-irrigation-app")
4. Choose whether to enable Google Analytics (optional)
5. Click "Create project"

## Step 2: Set Up Firestore Database

1. In your Firebase project, go to "Firestore Database" in the left sidebar
2. Click "Create database"
3. Choose "Start in test mode" for development (you can secure it later)
4. Select a location for your database (choose the closest to your users)
5. Click "Done"

## Step 3: Generate Service Account Key

1. In Firebase Console, go to "Project settings" (gear icon)
2. Go to the "Service accounts" tab
3. Click "Generate new private key"
4. Download the JSON file
5. Rename it to `serviceAccountKey.json`
6. Place it in your project root directory (same level as `app.py`)

**⚠️ Security Note:** Never commit this file to version control. Add `serviceAccountKey.json` to your `.gitignore` file.

## Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 5: Database Schema

The application uses the following Firestore collections:

### Users Collection (`users/{user_id}`)
```json
{
  "user_id": "uuid-string",
  "nom": "Doe",
  "prenom": "John",
  "email_or_phone": "john@example.com",
  "password": "hashed-password",
  "superficie": "100",
  "plante": "Tomate",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "thresholds": {
    "enabled": false,
    "min_moisture": 30,
    "max_moisture": 60
  },
  "notifications": [
    {
      "id": "uuid-string",
      "text": "Irrigation started",
      "timestamp": "2024-01-01T00:00:00Z",
      "read": false
    }
  ],
  "irrigation_events": [
    {
      "id": "uuid-string",
      "type": "start",
      "timestamp": "2024-01-01T00:00:00Z",
      "details": {
        "command": "voice",
        "moisture_level": 25
      }
    }
  ]
}
```

### User Credentials Collection (`user_credentials/{email_or_phone}`)
```json
{
  "user_id": "uuid-string",
  "password": "hashed-password"
}
```

## Step 6: Security Rules (Optional)

For production, set up Firestore security rules:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can only read/write their own data
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // User credentials are protected
    match /user_credentials/{email} {
      allow read, write: if false; // Only server-side access
    }
  }
}
```

## Step 7: Environment Variables (Optional)

For better security, you can use environment variables:

1. Create a `.env` file:
```
FIREBASE_CREDENTIALS_PATH=serviceAccountKey.json
FLASK_SECRET_KEY=your-secret-key-here
```

2. Update `firebase_config.py`:
```python
import os
from dotenv import load_dotenv

load_dotenv()

def initialize_firebase():
    cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'serviceAccountKey.json')
    # ... rest of the function
```

## Step 8: Test the Setup

1. Run your Flask application:
```bash
python app.py
```

2. Go to `http://localhost:5000`
3. Register a new user
4. Check the Firebase Console to see the data being created

## Troubleshooting

### Common Issues:

1. **"serviceAccountKey.json not found"**
   - Make sure the file is in the project root directory
   - Check the file name spelling

2. **"Permission denied"**
   - Ensure your service account has the necessary permissions
   - Check if Firestore is enabled in your Firebase project

3. **"Connection timeout"**
   - Check your internet connection
   - Verify the Firebase project region

### Debug Mode:

To enable debug logging, add this to your `app.py`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Production Considerations

1. **Password Hashing**: Implement proper password hashing (e.g., bcrypt)
2. **Authentication**: Use Firebase Authentication instead of custom auth
3. **Security Rules**: Implement proper Firestore security rules
4. **Environment Variables**: Use environment variables for sensitive data
5. **Backup**: Set up regular database backups
6. **Monitoring**: Enable Firebase monitoring and alerts

## Example Usage

### Creating a User:
```python
from firebase_config import create_user

user_data = {
    'nom': 'Doe',
    'prenom': 'John',
    'email_or_phone': 'john@example.com',
    'password': 'password123',
    'superficie': '100',
    'plante': 'Tomate'
}

user_id = create_user(user_data)
print(f"User created with ID: {user_id}")
```

### Getting User Data:
```python
from firebase_config import get_user_by_credentials

user = get_user_by_credentials('john@example.com', 'password123')
if user:
    print(f"Welcome {user['prenom']} {user['nom']}")
```

### Adding Notifications:
```python
from firebase_config import add_notification

add_notification(user_id, "Irrigation started automatically")
```

### Logging Irrigation Events:
```python
from firebase_config import add_irrigation_event

add_irrigation_event(user_id, 'start', {
    'command': 'manual',
    'moisture_level': 25,
    'temperature': 22.5
})
``` 