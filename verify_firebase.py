#!/usr/bin/env python3
"""
Simple Firebase verification script
Run this after setting up your serviceAccountKey.json file
"""

import os
import sys

def check_service_account_file():
    """Check if serviceAccountKey.json exists"""
    if not os.path.exists('serviceAccountKey.json'):
        print("❌ serviceAccountKey.json not found!")
        print("\nTo fix this:")
        print("1. Go to Firebase Console: https://console.firebase.google.com/")
        print("2. Select your project")
        print("3. Go to Project Settings (gear icon)")
        print("4. Go to Service Accounts tab")
        print("5. Click 'Generate new private key'")
        print("6. Download and rename to 'serviceAccountKey.json'")
        print("7. Place it in this directory")
        return False
    
    print("✅ serviceAccountKey.json found")
    return True

def test_firebase_connection():
    """Test Firebase connection"""
    try:
        from firebase_config import initialize_firebase, test_connection
        
        print("\n🔍 Testing Firebase connection...")
        initialize_firebase()
        
        if test_connection():
            print("✅ Firebase connection successful!")
            return True
        else:
            print("❌ Firebase connection failed")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you have installed the requirements:")
        print("pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Firebase connection error: {e}")
        return False

def main():
    print("🚀 Firebase Setup Verification")
    print("=" * 40)
    
    # Check if service account file exists
    if not check_service_account_file():
        sys.exit(1)
    
    # Test Firebase connection
    if test_firebase_connection():
        print("\n🎉 Firebase is properly configured!")
        print("You can now run your Flask app: python app.py")
    else:
        print("\n❌ Firebase setup incomplete")
        print("Please check the error messages above and try again")
        sys.exit(1)

if __name__ == "__main__":
    main() 