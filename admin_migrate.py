"""
Admin migration endpoint - accessible via web browser
Allows running database migration without SSH access
"""

from flask import Blueprint, jsonify, request
from functools import wraps
import logging

admin_migrate_bp = Blueprint('admin_migrate', __name__)

# Simple secret key for admin access (change this!)
MIGRATION_SECRET = "migrate-arcade-2024-secure"

def require_migration_secret(f):
    """Decorator to require secret key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        secret = request.args.get('secret') or request.headers.get('X-Migration-Secret')
        if secret != MIGRATION_SECRET:
            return jsonify({"error": "Unauthorized - invalid secret"}), 403
        return f(*args, **kwargs)
    return decorated_function


@admin_migrate_bp.route('/admin/migrate-arcade', methods=['GET', 'POST'])
@require_migration_secret
def migrate_arcade():
    """
    Run arcade database migration via web endpoint

    Usage:
        https://your-site.com/admin/migrate-arcade?secret=migrate-arcade-2024-secure
    """

    output = []
    success = True

    def log(message):
        output.append(message)
        logging.info(message)

    try:
        log("🔧 Starting Arcade Database Migration...")
        log("=" * 60)

        # Import the migration function
        from fix_production_db import migrate_production_db

        # Run migration
        migration_success = migrate_production_db()

        if migration_success:
            log("\n✅ Database migration completed successfully!")

            # Now initialize badges and powerups
            log("\n🎮 Initializing badges and power-ups...")

            from modules.arcade_enhancements import initialize_badges, initialize_powerups

            try:
                initialize_badges()
                log("✅ Initialized 12 arcade badges")
            except Exception as e:
                log(f"⚠️  Badge initialization: {e}")

            try:
                initialize_powerups()
                log("✅ Initialized 5 power-ups")
            except Exception as e:
                log(f"⚠️  Powerup initialization: {e}")

            log("\n" + "=" * 60)
            log("🎉 MIGRATION COMPLETE!")
            log("\nYou can now:")
            log("  • Visit /arcade to see all features")
            log("  • Visit /arcade/badges to see badge collection")
            log("  • Visit /arcade/powerups to see power-up shop")
            log("  • Visit /arcade/challenges to see daily challenge")
            log("=" * 60)

        else:
            success = False
            log("❌ Migration failed - check logs above")

    except Exception as e:
        success = False
        log(f"\n❌ ERROR: {str(e)}")
        import traceback
        log(traceback.format_exc())

    return jsonify({
        "success": success,
        "output": "\n".join(output)
    })


@admin_migrate_bp.route('/admin/check-arcade-tables', methods=['GET'])
@require_migration_secret
def check_arcade_tables():
    """
    Check which arcade tables exist

    Usage:
        https://your-site.com/admin/check-arcade-tables?secret=migrate-arcade-2024-secure
    """

    try:
        from models import db

        # Get list of all tables
        inspector = db.inspect(db.engine)
        all_tables = inspector.get_table_names()

        # Filter for arcade-related tables
        arcade_tables = [t for t in all_tables if any(keyword in t.lower() for keyword in
            ['arcade', 'game', 'badge', 'powerup', 'challenge', 'streak'])]

        # Check for specific expected tables
        expected_tables = [
            'arcade_games',
            'game_sessions',
            'game_leaderboards',
            'arcade_badges',
            'student_badges',
            'powerups',
            'student_powerups',
            'daily_challenges',
            'student_challenge_progress',
            'game_streaks'
        ]

        table_status = {}
        for table in expected_tables:
            table_status[table] = table in all_tables

        # Check for game_mode column in game_sessions
        game_mode_exists = False
        powerups_used_exists = False

        if 'game_sessions' in all_tables:
            columns = [col['name'] for col in inspector.get_columns('game_sessions')]
            game_mode_exists = 'game_mode' in columns
            powerups_used_exists = 'powerups_used' in columns

        return jsonify({
            "total_tables": len(all_tables),
            "arcade_related_tables": arcade_tables,
            "expected_tables": table_status,
            "game_sessions_columns": {
                "game_mode": game_mode_exists,
                "powerups_used": powerups_used_exists
            },
            "migration_needed": not all(table_status.values()) or not game_mode_exists
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500
