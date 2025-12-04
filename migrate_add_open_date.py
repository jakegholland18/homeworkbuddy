#!/usr/bin/env python3
"""
Database Migration: Add open_date column to assigned_practice table

This script adds the new open_date column to support assignment scheduling.
Run this once to update your existing database.

Usage:
    python migrate_add_open_date.py
"""

import sqlite3
import os
from datetime import datetime

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "persistent_db", "cozmiclearning.db")

def migrate():
    print("=" * 80)
    print("DATABASE MIGRATION: Add open_date column")
    print("=" * 80)
    print(f"Database: {DB_PATH}")
    print()

    if not os.path.exists(DB_PATH):
        print("❌ Database not found at:", DB_PATH)
        print("This migration should be run on the server, not locally.")
        return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(assigned_practice)")
        columns = [row[1] for row in cursor.fetchall()]

        if "open_date" in columns:
            print("✅ Column 'open_date' already exists. No migration needed.")
            conn.close()
            return True

        # Add the column
        print("Adding 'open_date' column to assigned_practice table...")
        cursor.execute("""
            ALTER TABLE assigned_practice
            ADD COLUMN open_date TIMESTAMP
        """)

        conn.commit()
        print("✅ Successfully added 'open_date' column!")

        # Verify
        cursor.execute("PRAGMA table_info(assigned_practice)")
        columns = [row[1] for row in cursor.fetchall()]

        if "open_date" in columns:
            print("✅ Verification successful: Column exists in database")
            print()
            print("=" * 80)
            print("MIGRATION COMPLETE")
            print("=" * 80)
            conn.close()
            return True
        else:
            print("❌ Verification failed: Column not found after migration")
            conn.close()
            return False

    except sqlite3.OperationalError as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        conn.close()
        return False

if __name__ == "__main__":
    success = migrate()
    exit(0 if success else 1)
