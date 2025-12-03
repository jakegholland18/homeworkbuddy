#!/usr/bin/env python
"""
Test script to manually expire a student's trial and verify the trial_expired page.
"""

from datetime import datetime, timedelta
from models import db, Student
from app import app

def list_students():
    """Show all students in the database."""
    with app.app_context():
        students = Student.query.all()
        print(f"\n📋 Total students: {len(students)}\n")
        
        if not students:
            print("❌ No students found. Please create a student account first!")
            print("\nTo create a test student:")
            print("1. Visit http://127.0.0.1:5000")
            print("2. Click 'Choose Login Role'")
            print("3. Click 'Student' → 'Sign Up'")
            print("4. Fill in the form and select 'Standalone' mode")
            print("5. Choose a plan (Basic or Premium)")
            print("6. Submit the form\n")
            return []
        
        for i, s in enumerate(students, 1):
            trial_status = "✅ Active" if s.subscription_active else "❌ Inactive"
            
            if s.trial_end:
                now = datetime.utcnow()
                if now > s.trial_end:
                    trial_text = f"🔴 EXPIRED on {s.trial_end.strftime('%Y-%m-%d')}"
                else:
                    days_left = (s.trial_end - now).days
                    trial_text = f"🟢 {days_left} days remaining (ends {s.trial_end.strftime('%Y-%m-%d')})"
            else:
                trial_text = "⚪ No trial set"
            
            print(f"{i}. ID: {s.id}")
            print(f"   Email: {s.student_email}")
            print(f"   Name: {s.student_name}")
            print(f"   Plan: {s.plan} ({s.billing})")
            print(f"   Subscription: {trial_status}")
            print(f"   Trial: {trial_text}")
            print()
        
        return students


def expire_trial(student_id):
    """Manually expire a student's trial for testing."""
    with app.app_context():
        student = Student.query.get(student_id)
        
        if not student:
            print(f"❌ Student with ID {student_id} not found!")
            return False
        
        print(f"\n🔧 Expiring trial for: {student.student_email}")
        print(f"   Current trial_end: {student.trial_end}")
        print(f"   Current subscription_active: {student.subscription_active}")
        
        # Set trial_end to yesterday
        yesterday = datetime.utcnow() - timedelta(days=1)
        student.trial_end = yesterday
        student.subscription_active = False  # Make sure subscription is not active
        
        db.session.commit()
        
        print(f"\n✅ Trial expired successfully!")
        print(f"   New trial_end: {student.trial_end}")
        print(f"   New subscription_active: {student.subscription_active}")
        print(f"\n🧪 Test the expiration:")
        print(f"   1. Visit http://127.0.0.1:5000/choose_login_role")
        print(f"   2. Click 'Student' → 'Login'")
        print(f"   3. Login with: {student.student_email}")
        print(f"   4. You should be redirected to the trial_expired page!")
        print()
        
        return True


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TRIAL EXPIRATION TEST TOOL")
    print("="*60)
    
    students = list_students()
    
    if students:
        print("="*60)
        print("\n📝 To expire a trial, run:")
        print("   python test_trial_expiration.py <student_id>")
        print(f"\n   Example: python test_trial_expiration.py {students[0].id}")
        print()
        
        # If a student ID is provided as argument
        import sys
        if len(sys.argv) > 1:
            try:
                student_id = int(sys.argv[1])
                expire_trial(student_id)
            except ValueError:
                print("❌ Please provide a valid student ID number")
