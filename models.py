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
    due_date = db.Column(db.DateTime)

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





