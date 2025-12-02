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

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # One parent can have multiple students (children)
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    classes = db.relationship("Class", backref="teacher", lazy=True)
    assigned_practices = db.relationship("AssignedPractice", backref="teacher_ref", lazy=True)


# ============================================================
# CLASSES
# ============================================================

class Class(db.Model):
    __tablename__ = "classes"

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"))
    class_name = db.Column(db.String(120))
    grade_level = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    students = db.relationship("Student", backref="class_ref", lazy=True)
    assignments = db.relationship("AssignedPractice", backref="class_ref", lazy=True)


# ============================================================
# STUDENTS (UPDATED WITH parent_id)
# ============================================================

class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)

    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"))
    parent_id = db.Column(db.Integer, db.ForeignKey("parents.id"))   # NEW FIELD

    student_name = db.Column(db.String(120))
    student_email = db.Column(db.String(120))

    ability_level = db.Column(db.String(20), default="on_level")
    average_score = db.Column(db.Float, default=0.0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    assessment_results = db.relationship("AssessmentResult", backref="student", lazy=True)


# ============================================================
# ANALYTICS: SCORES / RESULTS
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
    difficulty_level = db.Column(db.String(20))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ============================================================
# TEACHER-ASSIGNED PRACTICE SETS
# ============================================================

class AssignedPractice(db.Model):
    """
    A practice set assigned by a teacher to a class.
    Example: 'Fractions Test – Due Friday'
    """
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

    questions = db.relationship("AssignedQuestion", backref="practice", lazy=True)


# ============================================================
# INDIVIDUAL QUESTIONS IN A PRACTICE SET
# ============================================================

class AssignedQuestion(db.Model):
    """
    Stores each question for an AssignedPractice set.
    Supports multiple-choice or free response.
    """
    __tablename__ = "assigned_questions"

    id = db.Column(db.Integer, primary_key=True)
    practice_id = db.Column(db.Integer, db.ForeignKey("assigned_practice.id"), nullable=False)

    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), default="free")  # free / multiple_choice

    # Multiple choice options
    choice_a = db.Column(db.String(255))
    choice_b = db.Column(db.String(255))
    choice_c = db.Column(db.String(255))
    choice_d = db.Column(db.String(255))

    correct_answer = db.Column(db.String(255))
    explanation = db.Column(db.Text)
    difficulty_level = db.Column(db.String(20))  # easy / med / hard

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


