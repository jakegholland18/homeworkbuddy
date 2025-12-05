"""
Database migration: Add password reset token fields
Run this script to add reset_token and reset_token_expires columns to Student, Parent, and Teacher tables
"""

import sqlite3
import os

def run_migration():
    """Add password reset token fields to all user tables"""

    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'cozmiclearning.db')

    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if columns already exist
        cursor.execute("PRAGMA table_info(students)")
        student_columns = [col[1] for col in cursor.fetchall()]

        migrations_run = []

        # Check which tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]

        # Add reset token columns to students table
        if 'students' in existing_tables:
            if 'reset_token' not in student_columns:
                print("Adding reset_token and reset_token_expires to students table...")
                cursor.execute("ALTER TABLE students ADD COLUMN reset_token VARCHAR(255)")
                cursor.execute("ALTER TABLE students ADD COLUMN reset_token_expires DATETIME")
                migrations_run.append("students")
            else:
                print("✓ Students table already has reset token columns")
        else:
            print("⚠ Students table doesn't exist yet")

        # Add reset token columns to parents table
        if 'parents' in existing_tables:
            cursor.execute("PRAGMA table_info(parents)")
            parent_columns = [col[1] for col in cursor.fetchall()]

            if 'reset_token' not in parent_columns:
                print("Adding reset_token and reset_token_expires to parents table...")
                cursor.execute("ALTER TABLE parents ADD COLUMN reset_token VARCHAR(255)")
                cursor.execute("ALTER TABLE parents ADD COLUMN reset_token_expires DATETIME")
                migrations_run.append("parents")
            else:
                print("✓ Parents table already has reset token columns")
        else:
            print("⚠ Parents table doesn't exist yet")

        # Add reset token columns to teachers table
        if 'teachers' in existing_tables:
            cursor.execute("PRAGMA table_info(teachers)")
            teacher_columns = [col[1] for col in cursor.fetchall()]

            if 'reset_token' not in teacher_columns:
                print("Adding reset_token and reset_token_expires to teachers table...")
                cursor.execute("ALTER TABLE teachers ADD COLUMN reset_token VARCHAR(255)")
                cursor.execute("ALTER TABLE teachers ADD COLUMN reset_token_expires DATETIME")
                migrations_run.append("teachers")
            else:
                print("✓ Teachers table already has reset token columns")
        else:
            print("⚠ Teachers table doesn't exist yet")

        conn.commit()
        conn.close()

        if migrations_run:
            print(f"\n✅ Migration complete! Added reset token fields to: {', '.join(migrations_run)}")
        else:
            print("\n✅ All tables already up to date!")

        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Running password reset token migration...\n")
    success = run_migration()
    exit(0 if success else 1)
