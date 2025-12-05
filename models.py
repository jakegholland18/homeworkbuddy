from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ============================================================
# PARENT ACCOUNTS
# ============================================================

class Parent(db.Model):
    __tablename__ = "parents"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(255))

    # Unique access code for student linking (e.g., "ABC123")
    access_code = db.Column(db.String(10), unique=True, nullable=True)

    # Subscription fields
    plan = db.Column(db.String(50))           # free/basic/premium
    billing = db.Column(db.String(20))        # monthly/yearly
    trial_start = db.Column(db.DateTime)
    trial_end = db.Column(db.DateTime)
    subscription_active = db.Column(db.Boolean, default=False)

    # Time limits (Phase 3)
    daily_limit_minutes = db.Column(db.Integer, nullable=True)  # null = no limit

    # Email preferences (Phase 4)
    email_reports_enabled = db.Column(db.Boolean, default=True)
    last_report_sent = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # One parent → many students
    students = db.relationship("Student", backref="parent_ref", lazy=True)


# ============================================================
# TEACHER ACCOUNTS
# ============================================================

class Teacher(db.Model):
    __tablename__ = "teachers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(255))

    # Subscription fields (optional for teacher accounts)
    plan = db.Column(db.String(50))
    billing = db.Column(db.String(20))
    trial_start = db.Column(db.DateTime)
    trial_end = db.Column(db.DateTime)
    subscription_active = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    classes = db.relationship("Class", backref="teacher", lazy=True)
    assigned_practices = db.relationship("AssignedPractice", backref="teacher_ref", lazy=True)


# ============================================================
# CLASSROOMS
# ============================================================

class Class(db.Model):
    __tablename__ = "classes"

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), nullable=False)

    class_name = db.Column(db.String(120))
    grade_level = db.Column(db.String(20))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    students = db.relationship("Student", backref="class_ref", lazy=True)
    assignments = db.relationship("AssignedPractice", backref="class_ref", lazy=True)


# ============================================================
# STUDENTS
# ============================================================

class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)

    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"))
    parent_id = db.Column(db.Integer, db.ForeignKey("parents.id"))

    student_name = db.Column(db.String(120))
    student_email = db.Column(db.String(120))
    password_hash = db.Column(db.String(255))  # For secure authentication
    date_of_birth = db.Column(db.Date)  # For age verification and COPPA compliance

    # Subscription fields
    plan = db.Column(db.String(50))           # free/basic/premium
    billing = db.Column(db.String(20))        # monthly/yearly
    trial_start = db.Column(db.DateTime)
    trial_end = db.Column(db.DateTime)
    subscription_active = db.Column(db.Boolean, default=False)

    # Differentiation engine ability tier
    ability_level = db.Column(db.String(20), default="on_level")  
    # below / on_level / advanced

    # Auto-updated from analytics
    average_score = db.Column(db.Float, default=0.0)

    # Time tracking (Phase 3)
    last_login = db.Column(db.DateTime, nullable=True)
    today_minutes = db.Column(db.Integer, default=0)  # resets daily

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    assessment_results = db.relationship("AssessmentResult", backref="student", lazy=True)


# ============================================================
# ANALYTICS — RESULTS & SCORES
# ============================================================

class AssessmentResult(db.Model):
    __tablename__ = "assessment_results"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"))

    subject = db.Column(db.String(50))
    topic = db.Column(db.String(200))

    score_percent = db.Column(db.Float)
    num_correct = db.Column(db.Integer)
    num_questions = db.Column(db.Integer)

    difficulty_level = db.Column(db.String(20))  # easy / medium / hard
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ============================================================
# TEACHER-ASSIGNED PRACTICE SETS
# ============================================================

class AssignedPractice(db.Model):
    __tablename__ = "assigned_practice"

    id = db.Column(db.Integer, primary_key=True)

    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), nullable=False)

    title = db.Column(db.String(200))
    subject = db.Column(db.String(50))
    topic = db.Column(db.String(200))
    instructions = db.Column(db.Text)
    open_date = db.Column(db.DateTime, nullable=True)  # When assignment becomes visible to students
    due_date = db.Column(db.DateTime, nullable=True)   # When assignment closes

    # Assignment type for gradebook categorization
    assignment_type = db.Column(db.String(50), default="practice")  # practice / quiz / test / homework

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Differentiation level
    differentiation_mode = db.Column(db.String(50), default="none")
    # none / adaptive / gap_fill / mastery / scaffold

    # 🔥 NEW — Full AI preview mission data (steps, hints, final message)
    preview_json = db.Column(db.Text, nullable=True)

    # 🔥 NEW — Teacher must approve before publishing to students
    is_published = db.Column(db.Boolean, default=False)

    # Manual questions (optional)
    questions = db.relationship("AssignedQuestion", backref="practice", lazy=True)
    
    # Student submissions for grading
    submissions = db.relationship("StudentSubmission", backref="assignment", lazy=True)


# ============================================================
# QUESTIONS INSIDE A PRACTICE SET
# ============================================================

class AssignedQuestion(db.Model):
    __tablename__ = "assigned_questions"

    id = db.Column(db.Integer, primary_key=True)
    practice_id = db.Column(db.Integer, db.ForeignKey("assigned_practice.id"), nullable=False)

    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), default="free")  # free / multiple_choice

    # MC options
    choice_a = db.Column(db.String(255))
    choice_b = db.Column(db.String(255))
    choice_c = db.Column(db.String(255))
    choice_d = db.Column(db.String(255))

    correct_answer = db.Column(db.String(255))
    explanation = db.Column(db.Text)
    difficulty_level = db.Column(db.String(20))  # easy / medium / hard

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ============================================================
# TEACHER LESSON PLANS
# ============================================================

class LessonPlan(db.Model):
    __tablename__ = "lesson_plans"

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), nullable=False)

    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(50))
    topic = db.Column(db.String(200))
    grade = db.Column(db.String(20))

    # Six-section structure stored as JSON
    sections_json = db.Column(db.Text)  # {overview, key_facts, christian_view, agreement, difference, practice}
    
    # Full raw text for export/display
    full_text = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    teacher = db.relationship("Teacher", backref="lesson_plans", lazy=True)


# ============================================================
# MESSAGING SYSTEM
# ============================================================

class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    
    # Sender info
    sender_type = db.Column(db.String(20), nullable=False)  # 'teacher' or 'parent'
    sender_id = db.Column(db.Integer, nullable=False)  # ID of teacher or parent
    
    # Recipient info
    recipient_type = db.Column(db.String(20), nullable=False)  # 'teacher' or 'parent'
    recipient_id = db.Column(db.Integer, nullable=False)  # ID of teacher or parent
    
    # Student context (which student is this about)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=True)
    
    # Message content
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    
    # Progress report attachment (optional JSON data)
    progress_report_json = db.Column(db.Text, nullable=True)
    
    # Thread management
    thread_id = db.Column(db.Integer, nullable=True)  # For grouping replies
    
    # Status
    is_read = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student = db.relationship("Student", backref="messages", lazy=True)


# ============================================================
# STUDENT SUBMISSIONS & GRADES
# ============================================================

class StudentSubmission(db.Model):
    __tablename__ = "student_submissions"

    id = db.Column(db.Integer, primary_key=True)
    
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assigned_practice.id"), nullable=False)
    
    # Submission status
    status = db.Column(db.String(20), default="not_started")  # not_started / in_progress / submitted / graded
    
    # Grading
    score = db.Column(db.Float, nullable=True)  # Percentage score (0-100)
    points_earned = db.Column(db.Float, nullable=True)
    points_possible = db.Column(db.Float, nullable=True)
    
    # Answers submitted (JSON of question_id: answer pairs)
    answers_json = db.Column(db.Text, nullable=True)
    
    # Teacher feedback
    feedback = db.Column(db.Text, nullable=True)
    
    # Timestamps
    started_at = db.Column(db.DateTime, nullable=True)
    submitted_at = db.Column(db.DateTime, nullable=True)
    graded_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student_rel = db.relationship("Student", backref="submissions", lazy=True)


# ============================================================
# QUESTION LOGGING & MODERATION
# ============================================================

class QuestionLog(db.Model):
    """
    Logs all student questions and AI interactions for safety review.
    Tracks moderation flags, parent notifications, and admin reviews.
    """
    __tablename__ = "question_logs"

    id = db.Column(db.Integer, primary_key=True)
    
    # Student info
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    
    # Question details
    question_text = db.Column(db.Text, nullable=False)
    sanitized_text = db.Column(db.Text, nullable=True)  # After sanitization
    subject = db.Column(db.String(50), nullable=True)  # Which subject/planet
    context = db.Column(db.String(50), nullable=True)  # "question", "chat", "practice", "powergrid"
    grade_level = db.Column(db.String(10), nullable=True)
    
    # AI response
    ai_response = db.Column(db.Text, nullable=True)
    
    # Moderation results
    flagged = db.Column(db.Boolean, default=False)
    allowed = db.Column(db.Boolean, default=True)  # Whether content was processed
    moderation_reason = db.Column(db.Text, nullable=True)  # Why flagged/blocked
    moderation_data_json = db.Column(db.Text, nullable=True)  # Full moderation details (JSON)
    severity = db.Column(db.String(20), nullable=True)  # "low", "medium", "high"
    
    # Admin review
    reviewed = db.Column(db.Boolean, default=False)
    reviewed_by = db.Column(db.String(100), nullable=True)  # Admin/teacher email
    reviewed_at = db.Column(db.DateTime, nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)
    
    # Parent notification
    parent_notified = db.Column(db.Boolean, default=False)
    parent_notified_at = db.Column(db.DateTime, nullable=True)
    
    # Student appeal system
    appeal_requested = db.Column(db.Boolean, default=False)
    appeal_reason = db.Column(db.Text, nullable=True)
    appeal_status = db.Column(db.String(20), nullable=True)  # "pending", "approved", "denied"
    appeal_reviewed_by = db.Column(db.String(100), nullable=True)
    appeal_reviewed_at = db.Column(db.DateTime, nullable=True)
    appeal_notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student = db.relationship("Student", backref="question_logs", lazy=True)


# ============================================================
# ACHIEVEMENTS & BADGES
# ============================================================

class Achievement(db.Model):
    __tablename__ = "achievements"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    description = db.Column(db.String(255))
    icon = db.Column(db.String(50))  # emoji or icon identifier
    category = db.Column(db.String(50))  # streak, level, mastery, exploration, milestone
    requirement_value = db.Column(db.Integer)  # e.g., 7 for "7-day streak"
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class StudentAchievement(db.Model):
    __tablename__ = "student_achievements"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"))
    achievement_id = db.Column(db.Integer, db.ForeignKey("achievements.id"))
    
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student = db.relationship("Student", backref="earned_achievements")
    achievement = db.relationship("Achievement")


# ============================================================
# ACTIVITY LOG
# ============================================================

class ActivityLog(db.Model):
    __tablename__ = "activity_log"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"))
    
    activity_type = db.Column(db.String(50))  # question_answered, assignment_completed, achievement_earned, level_up
    subject = db.Column(db.String(50), nullable=True)
    description = db.Column(db.String(255))
    xp_earned = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship("Student", backref="activities")


# ============================================================
# ARCADE MODE - LEARNING GAMES
# ============================================================

class ArcadeGame(db.Model):
    """Catalog of available arcade games"""
    __tablename__ = "arcade_games"

    id = db.Column(db.Integer, primary_key=True)
    game_key = db.Column(db.String(50), unique=True)  # speed_math, vocab_builder, etc.
    name = db.Column(db.String(100))
    description = db.Column(db.String(255))
    subject = db.Column(db.String(50))  # math, science, reading, writing
    icon = db.Column(db.String(50))  # emoji
    difficulty_levels = db.Column(db.String(100))  # JSON array of grade ranges
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class GameSession(db.Model):
    """Individual game play sessions with scores"""
    __tablename__ = "game_sessions"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"))
    game_key = db.Column(db.String(50))  # References ArcadeGame.game_key
    
    # Game metadata
    grade_level = db.Column(db.String(10))
    difficulty = db.Column(db.String(20))  # easy, medium, hard
    
    # Performance metrics
    score = db.Column(db.Integer)
    time_seconds = db.Column(db.Integer)
    accuracy = db.Column(db.Float)  # Percentage
    questions_answered = db.Column(db.Integer)
    questions_correct = db.Column(db.Integer)
    
    # Rewards
    xp_earned = db.Column(db.Integer, default=0)
    tokens_earned = db.Column(db.Integer, default=0)
    
    # Timestamps
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    student = db.relationship("Student", backref="game_sessions")


class GameLeaderboard(db.Model):
    """High scores and leaderboard tracking"""
    __tablename__ = "game_leaderboards"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"))
    game_key = db.Column(db.String(50))
    grade_level = db.Column(db.String(10))

    # Best scores
    high_score = db.Column(db.Integer)
    best_time = db.Column(db.Integer)  # Fastest completion in seconds
    best_accuracy = db.Column(db.Float)
    total_plays = db.Column(db.Integer, default=0)

    # Last updated
    last_played = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student = db.relationship("Student", backref="leaderboard_entries")


class HomeschoolLessonPlan(db.Model):
    """AI-generated and manual lesson plans for homeschool parents"""
    __tablename__ = "homeschool_lesson_plans"

    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("parents.id"), nullable=False)

    # Basic Info
    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(50))  # math, science, history, etc.
    grade_level = db.Column(db.String(20))
    topic = db.Column(db.Text)
    duration = db.Column(db.Integer)  # Duration in minutes

    # Lesson Content (stored as JSON for flexibility)
    objectives = db.Column(db.JSON)  # List of learning objectives
    materials = db.Column(db.JSON)  # List of materials needed
    activities = db.Column(db.JSON)  # Structured lesson activities
    discussion_questions = db.Column(db.JSON)  # List of questions
    assessment = db.Column(db.Text)  # Assessment ideas
    homework = db.Column(db.Text)  # Homework/practice suggestions
    extensions = db.Column(db.Text)  # Extension activities

    # Teaching Notes
    notes = db.Column(db.Text)  # Teacher's private notes
    biblical_integration = db.Column(db.Text, nullable=True)  # Optional Bible verses/principles

    # Metadata
    status = db.Column(db.String(20), default='not_started')  # not_started, in_progress, completed
    is_favorite = db.Column(db.Boolean, default=False)
    tags = db.Column(db.JSON)  # Custom tags
    source = db.Column(db.String(20), default='ai_generated')  # ai_generated, manual, imported

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    taught_date = db.Column(db.DateTime, nullable=True)

    # Relationships
    parent = db.relationship("Parent", backref="homeschool_lesson_plans")


# ============================================================
# DATABASE INDICES FOR PERFORMANCE
# ============================================================
# These indices dramatically improve query performance by allowing
# the database to quickly locate rows without scanning entire tables.
#
# Index Strategy:
# 1. Foreign keys (for JOIN operations)
# 2. Frequently queried columns (email lookups, student_id, class_id)
# 3. Columns used in WHERE clauses
# 4. Columns used in ORDER BY
#
# Performance Impact: 100-1000x faster queries on large tables
# ============================================================

# Parent Indices
db.Index('idx_parent_email', Parent.email)
db.Index('idx_parent_access_code', Parent.access_code)

# Teacher Indices
db.Index('idx_teacher_email', Teacher.email)

# Student Indices
db.Index('idx_student_email', Student.student_email)
db.Index('idx_student_parent_id', Student.parent_id)
db.Index('idx_student_class_id', Student.class_id)
db.Index('idx_student_created_at', Student.created_at)  # For recent students queries

# Class Indices
db.Index('idx_class_teacher_id', Class.teacher_id)

# Message Indices (conversation history)
db.Index('idx_message_student_id', Message.student_id)
db.Index('idx_message_created_at', Message.created_at)  # For chronological sorting
db.Index('idx_message_student_created_at', Message.student_id, Message.created_at)  # Composite for student history

# Assigned Practice Indices
db.Index('idx_assigned_practice_class_id', AssignedPractice.class_id)
db.Index('idx_assigned_practice_teacher_id', AssignedPractice.teacher_id)
db.Index('idx_assigned_practice_due_date', AssignedPractice.due_date)
db.Index('idx_assigned_practice_open_date', AssignedPractice.open_date)

# Assigned Question Indices
db.Index('idx_assigned_question_practice_id', AssignedQuestion.practice_id)

# Student Submission Indices
db.Index('idx_student_submission_student_id', StudentSubmission.student_id)
db.Index('idx_student_submission_assignment_id', StudentSubmission.assignment_id)
db.Index('idx_student_submission_submitted_at', StudentSubmission.submitted_at)

# Question Log Indices
db.Index('idx_question_log_student_id', QuestionLog.student_id)
db.Index('idx_question_log_created_at', QuestionLog.created_at)

# Activity Log Indices
db.Index('idx_activity_log_student_id', ActivityLog.student_id)
db.Index('idx_activity_log_created_at', ActivityLog.created_at)
db.Index('idx_activity_log_activity_type', ActivityLog.activity_type)

# Student Achievement Indices
db.Index('idx_student_achievement_student_id', StudentAchievement.student_id)
db.Index('idx_student_achievement_achievement_id', StudentAchievement.achievement_id)

# Game Session Indices
db.Index('idx_game_session_student_id', GameSession.student_id)
db.Index('idx_game_session_game_key', GameSession.game_key)
db.Index('idx_game_session_started_at', GameSession.started_at)

# Game Leaderboard Indices
db.Index('idx_game_leaderboard_student_id', GameLeaderboard.student_id)
db.Index('idx_game_leaderboard_game_key', GameLeaderboard.game_key)
db.Index('idx_game_leaderboard_high_score', GameLeaderboard.high_score)  # For high score queries

# Lesson Plan Indices
db.Index('idx_lesson_plan_parent_id', LessonPlan.parent_id)
db.Index('idx_lesson_plan_subject', LessonPlan.subject)
db.Index('idx_lesson_plan_created_at', LessonPlan.created_at)


