"""
Production Database Fix for Render.com
This script safely migrates the production database to add arcade enhancements
Run this ONCE on your Render server via SSH or add to build command
"""

import os
import sys
import sqlite3
from pathlib import Path

def get_db_path():
    """Find the database file"""
    possible_paths = [
        'instance/cozmiclearning.db',
        'persistent_db/cozmiclearning.db',
        '/opt/render/project/src/instance/cozmiclearning.db',
        '/opt/render/project/src/persistent_db/cozmiclearning.db',
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    # If not found, check environment variable
    if 'DB_PATH' in os.environ:
        return os.environ['DB_PATH']

    return None

def check_table_exists(cursor, table_name):
    """Check if a table exists"""
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    return cursor.fetchone() is not None

def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    return column_name in columns

def migrate_production_db():
    """Safely migrate production database"""

    print("🔧 Production Database Migration for Arcade Enhancements")
    print("=" * 70)

    db_path = get_db_path()

    if not db_path:
        print("❌ ERROR: Could not find database file")
        print("\nSearched locations:")
        print("  - instance/cozmiclearning.db")
        print("  - persistent_db/cozmiclearning.db")
        print("  - /opt/render/project/src/instance/cozmiclearning.db")
        print("\nPlease set DB_PATH environment variable or check database location")
        sys.exit(1)

    print(f"📁 Database found: {db_path}")

    # Backup first
    backup_path = f"{db_path}.backup_{int(os.path.getmtime(db_path))}"
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup created: {backup_path}")
    except Exception as e:
        print(f"⚠️  Could not create backup: {e}")
        print("   Continuing anyway...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if game_sessions exists
        if check_table_exists(cursor, 'game_sessions'):
            print("\n📋 Migrating game_sessions table...")

            # Add columns if they don't exist
            if not check_column_exists(cursor, 'game_sessions', 'game_mode'):
                cursor.execute("ALTER TABLE game_sessions ADD COLUMN game_mode VARCHAR(20) DEFAULT 'timed'")
                print("  ✅ Added game_mode column")
            else:
                print("  ⏭️  game_mode column already exists")

            if not check_column_exists(cursor, 'game_sessions', 'powerups_used'):
                cursor.execute("ALTER TABLE game_sessions ADD COLUMN powerups_used TEXT")
                print("  ✅ Added powerups_used column")
            else:
                print("  ⏭️  powerups_used column already exists")
        else:
            print("\n📋 Creating game_sessions table...")
            cursor.execute("""
                CREATE TABLE game_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    game_key VARCHAR(50),
                    grade_level VARCHAR(10),
                    difficulty VARCHAR(20),
                    game_mode VARCHAR(20) DEFAULT 'timed',
                    score INTEGER,
                    time_seconds INTEGER,
                    accuracy FLOAT,
                    questions_answered INTEGER,
                    questions_correct INTEGER,
                    powerups_used TEXT,
                    xp_earned INTEGER DEFAULT 0,
                    tokens_earned INTEGER DEFAULT 0,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students(id)
                )
            """)
            print("  ✅ game_sessions table created")

        # Create other arcade tables
        tables_to_create = {
            'arcade_games': """
                CREATE TABLE IF NOT EXISTS arcade_games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_key VARCHAR(50) UNIQUE,
                    name VARCHAR(100),
                    description VARCHAR(255),
                    subject VARCHAR(50),
                    icon VARCHAR(50),
                    difficulty_levels VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            'game_leaderboards': """
                CREATE TABLE IF NOT EXISTS game_leaderboards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    game_key VARCHAR(50),
                    grade_level VARCHAR(10),
                    high_score INTEGER,
                    best_time INTEGER,
                    best_accuracy FLOAT,
                    total_plays INTEGER DEFAULT 0,
                    last_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students(id)
                )
            """,
            'arcade_badges': """
                CREATE TABLE IF NOT EXISTS arcade_badges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    badge_key VARCHAR(50) UNIQUE,
                    name VARCHAR(100),
                    description VARCHAR(255),
                    icon VARCHAR(50),
                    category VARCHAR(50),
                    requirement_type VARCHAR(50),
                    requirement_value INTEGER,
                    game_key VARCHAR(50),
                    tier VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            'student_badges': """
                CREATE TABLE IF NOT EXISTS student_badges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    badge_id INTEGER,
                    game_key VARCHAR(50),
                    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students(id),
                    FOREIGN KEY (badge_id) REFERENCES arcade_badges(id)
                )
            """,
            'powerups': """
                CREATE TABLE IF NOT EXISTS powerups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    powerup_key VARCHAR(50) UNIQUE,
                    name VARCHAR(100),
                    description VARCHAR(255),
                    icon VARCHAR(50),
                    token_cost INTEGER,
                    effect_duration INTEGER,
                    uses_per_game INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            'student_powerups': """
                CREATE TABLE IF NOT EXISTS student_powerups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    powerup_id INTEGER,
                    quantity INTEGER DEFAULT 1,
                    FOREIGN KEY (student_id) REFERENCES students(id),
                    FOREIGN KEY (powerup_id) REFERENCES powerups(id)
                )
            """,
            'daily_challenges': """
                CREATE TABLE IF NOT EXISTS daily_challenges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_key VARCHAR(50),
                    challenge_date DATE UNIQUE,
                    target_score INTEGER,
                    target_accuracy FLOAT,
                    target_time INTEGER,
                    grade_level VARCHAR(10),
                    bonus_xp INTEGER DEFAULT 100,
                    bonus_tokens INTEGER DEFAULT 50,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            'student_challenge_progress': """
                CREATE TABLE IF NOT EXISTS student_challenge_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    challenge_id INTEGER,
                    completed BOOLEAN DEFAULT 0,
                    completed_at TIMESTAMP,
                    best_score INTEGER,
                    best_accuracy FLOAT,
                    best_time INTEGER,
                    FOREIGN KEY (student_id) REFERENCES students(id),
                    FOREIGN KEY (challenge_id) REFERENCES daily_challenges(id)
                )
            """,
            'game_streaks': """
                CREATE TABLE IF NOT EXISTS game_streaks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER UNIQUE,
                    current_streak INTEGER DEFAULT 0,
                    longest_streak INTEGER DEFAULT 0,
                    last_played_date DATE,
                    FOREIGN KEY (student_id) REFERENCES students(id)
                )
            """
        }

        for table_name, create_sql in tables_to_create.items():
            if not check_table_exists(cursor, table_name):
                print(f"\n📋 Creating {table_name} table...")
                cursor.execute(create_sql)
                print(f"  ✅ {table_name} created")
            else:
                print(f"  ⏭️  {table_name} already exists")

        # Create indices
        print("\n📊 Creating indices...")
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_game_session_student_id ON game_sessions(student_id)",
            "CREATE INDEX IF NOT EXISTS idx_game_session_game_key ON game_sessions(game_key)",
            "CREATE INDEX IF NOT EXISTS idx_game_leaderboard_student_id ON game_leaderboards(student_id)",
            "CREATE INDEX IF NOT EXISTS idx_student_badge_student_id ON student_badges(student_id)",
            "CREATE INDEX IF NOT EXISTS idx_student_powerup_student_id ON student_powerups(student_id)",
            "CREATE INDEX IF NOT EXISTS idx_game_streak_student_id ON game_streaks(student_id)",
        ]

        for index_sql in indices:
            cursor.execute(index_sql)

        print("  ✅ All indices created")

        conn.commit()

        print("\n" + "=" * 70)
        print("✅ MIGRATION SUCCESSFUL!")
        print("\nNext step: Populate badges and powerups")
        print("Run: python3 init_arcade_enhancements.py")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n❌ ERROR during migration: {e}")
        conn.rollback()
        print("\nDatabase has been rolled back to previous state")
        return False

    finally:
        conn.close()

if __name__ == "__main__":
    success = migrate_production_db()
    sys.exit(0 if success else 1)
