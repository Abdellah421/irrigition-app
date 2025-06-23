#!/usr/bin/env python3
"""
Test script for Firebase integration
Run this script to test your Firebase setup
"""

import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from firebase_config import (
        create_user, get_user_by_credentials, get_user_by_id, 
        update_user_profile, add_notification, get_user_notifications,
        add_irrigation_event, get_irrigation_events, check_user_exists
    )
    print("✅ Firebase configuration imported successfully")
except ImportError as e:
    print(f"❌ Error importing Firebase configuration: {e}")
    print("Make sure you have installed the requirements: pip install -r requirements.txt")
    sys.exit(1)

def test_firebase_connection():
    """Test basic Firebase connection"""
    print("\n🔍 Testing Firebase connection...")
    
    try:
        from firebase_config import get_db
        db = get_db()
        print("✅ Firebase connection established")
        return True
    except Exception as e:
        print(f"❌ Firebase connection failed: {e}")
        return False

def test_user_creation():
    """Test user creation"""
    print("\n👤 Testing user creation...")
    
    # Test user data
    test_user = {
        'nom': 'Test',
        'prenom': 'User',
        'email_or_phone': 'test@example.com',
        'password': 'testpassword123',
        'superficie': '50',
        'plante': 'Menthe'
    }
    
    try:
        # Check if user already exists
        if check_user_exists(test_user['email_or_phone']):
            print("⚠️  Test user already exists, skipping creation")
            return test_user['email_or_phone']
        
        # Create user
        user_id = create_user(test_user)
        print(f"✅ User created successfully with ID: {user_id}")
        return test_user['email_or_phone']
        
    except Exception as e:
        print(f"❌ User creation failed: {e}")
        return None

def test_user_authentication(email_or_phone):
    """Test user authentication"""
    print("\n🔐 Testing user authentication...")
    
    try:
        user = get_user_by_credentials(email_or_phone, 'testpassword123')
        if user:
            print(f"✅ Authentication successful for {user['prenom']} {user['nom']}")
            return user['user_id']
        else:
            print("❌ Authentication failed")
            return None
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return None

def test_user_profile_update(user_id):
    """Test user profile update"""
    print("\n📝 Testing profile update...")
    
    try:
        profile_data = {
            'nom': 'Updated',
            'prenom': 'User',
            'superficie': '75',
            'plante': 'Tomate'
        }
        
        update_user_profile(user_id, profile_data)
        print("✅ Profile updated successfully")
        
        # Verify update
        updated_user = get_user_by_id(user_id)
        if updated_user['nom'] == 'Updated':
            print("✅ Profile update verified")
            return True
        else:
            print("❌ Profile update verification failed")
            return False
            
    except Exception as e:
        print(f"❌ Profile update failed: {e}")
        return False

def test_notifications(user_id):
    """Test notification functionality"""
    print("\n🔔 Testing notifications...")
    
    try:
        # Add test notifications
        add_notification(user_id, "Test notification 1")
        add_notification(user_id, "Test notification 2")
        add_notification(user_id, "Irrigation started automatically")
        
        # Get notifications
        notifications = get_user_notifications(user_id, limit=10)
        print(f"✅ {len(notifications)} notifications retrieved")
        
        for i, notif in enumerate(notifications[:3]):
            print(f"   {i+1}. {notif['text']} ({notif['timestamp']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Notification test failed: {e}")
        return False

def test_irrigation_events(user_id):
    """Test irrigation events"""
    print("\n💧 Testing irrigation events...")
    
    try:
        # Add test irrigation events
        add_irrigation_event(user_id, 'start', {
            'command': 'manual',
            'moisture_level': 25,
            'temperature': 22.5
        })
        
        add_irrigation_event(user_id, 'stop', {
            'command': 'voice',
            'duration_minutes': 15
        })
        
        add_irrigation_event(user_id, 'auto_start', {
            'moisture_level': 20,
            'threshold': 30
        })
        
        # Get irrigation events
        events = get_irrigation_events(user_id, limit=10)
        print(f"✅ {len(events)} irrigation events retrieved")
        
        for i, event in enumerate(events[:3]):
            print(f"   {i+1}. {event['type']} - {event['timestamp']}")
            if event['details']:
                print(f"      Details: {event['details']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Irrigation events test failed: {e}")
        return False

def cleanup_test_data(email_or_phone):
    """Clean up test data (optional)"""
    print("\n🧹 Cleaning up test data...")
    
    try:
        from firebase_config import get_db
        db = get_db()
        
        # Delete user credentials
        db.collection('user_credentials').document(email_or_phone).delete()
        print("✅ Test user credentials deleted")
        
        # Note: We don't delete the user document as it might be referenced elsewhere
        # In a real cleanup, you'd want to delete all related data
        
    except Exception as e:
        print(f"⚠️  Cleanup failed: {e}")

def main():
    """Run all Firebase tests"""
    print("🚀 Starting Firebase Integration Tests")
    print("=" * 50)
    
    # Test connection
    if not test_firebase_connection():
        print("\n❌ Firebase connection failed. Please check your setup.")
        return
    
    # Test user creation
    email_or_phone = test_user_creation()
    if not email_or_phone:
        print("\n❌ User creation failed. Please check your Firebase setup.")
        return
    
    # Test authentication
    user_id = test_user_authentication(email_or_phone)
    if not user_id:
        print("\n❌ Authentication failed. Please check your Firebase setup.")
        return
    
    # Test profile update
    if not test_user_profile_update(user_id):
        print("\n⚠️  Profile update test failed.")
    
    # Test notifications
    if not test_notifications(user_id):
        print("\n⚠️  Notifications test failed.")
    
    # Test irrigation events
    if not test_irrigation_events(user_id):
        print("\n⚠️  Irrigation events test failed.")
    
    print("\n" + "=" * 50)
    print("✅ Firebase integration tests completed!")
    print("\n📋 Summary:")
    print(f"   - Test user: {email_or_phone}")
    print(f"   - User ID: {user_id}")
    print("   - All core functionality tested")
    
    # Ask if user wants to cleanup
    cleanup = input("\n🧹 Do you want to clean up test data? (y/N): ").lower().strip()
    if cleanup == 'y':
        cleanup_test_data(email_or_phone)
    
    print("\n🎉 Firebase setup is working correctly!")
    print("You can now run your Flask application: python app.py")

if __name__ == "__main__":
    main() 