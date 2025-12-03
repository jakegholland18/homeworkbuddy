# modules/teacher_tools.py
"""
Teacher tooling: assignments, quizzes, lesson plans, messaging, analytics, and reports.

Depends on:
- practice_helper.generate_practice_session and apply_differentiation
- shared_ai.study_buddy_ai for lesson plan generation
- models for AssessmentResult and relationships
"""
from datetime import datetime
from typing import Dict, List, Optional

from modules.practice_helper import generate_practice_session, apply_differentiation
from modules.shared_ai import study_buddy_ai, build_character_voice, grade_depth_instruction
from modules.answer_formatter import format_answer
from models import db, Student, Teacher, Class, AssessmentResult


def assign_practice(subject: str, grade: str, differentiation_mode: str, student_ids: List[int], character: str) -> Dict:
    """Create a practice session payload for a set of students using differentiation."""
    prompt = {
        "subject": subject,
        "grade": grade,
        "mode": differentiation_mode,
    }
    session = generate_practice_session(subject, grade, mode=differentiation_mode)
    payload = {"created_at": datetime.utcnow().isoformat(), "session": session, "student_ids": student_ids}
    return payload


def generate_quiz(subject: str, grade: str, differentiation_mode: str, num_questions: int = 6) -> Dict:
    """Generate a short quiz using the practice engine with mode impacting difficulty."""
    session = generate_practice_session(subject, grade, mode=differentiation_mode, steps=num_questions)
    return {"created_at": datetime.utcnow().isoformat(), "quiz": session}


def generate_lesson_plan(subject: str, topic: str, grade: str, character: str) -> Dict:
    """Generate a six-section lesson plan using shared_ai pattern."""
    prompt = (
        f"Create a teacher-friendly lesson plan for {subject} on '{topic}'. "
        f"Use the six-section format. {grade_depth_instruction(grade)}"
    )
    result = study_buddy_ai(prompt, grade, character)
    if isinstance(result, dict) and result.get("raw_text"):
        raw = result["raw_text"]
    else:
        raw = str(result)
    # Format into sections to render on subject page or teacher view
    sections = format_answer(raw_text=raw)
    return {"raw": raw, "sections": sections}


def message_parents(class_id: int, teacher_id: int, message: str) -> Dict:
    """Stub: persist a message to parents of a class. Returns summary."""
    # In a future pass, add a Messages table. For now, return payload.
    return {"class_id": class_id, "teacher_id": teacher_id, "message": message, "sent_at": datetime.utcnow().isoformat()}


def get_class_analytics(class_id: int) -> Dict:
    """Compute class analytics from AssessmentResult: averages, ability tiers, per-subject breakdown, and trend deltas."""
    students = Student.query.filter_by(class_id=class_id).all()
    summary: Dict = {"class_id": class_id, "students": [], "subjects": {}, "flags": []}

    # Per-student analytics
    for s in students:
        results = (
            AssessmentResult.query.filter_by(student_id=s.id)
            .order_by(AssessmentResult.created_at.desc())
            .limit(20)
            .all()
        )
        last10 = results[:10]
        prev10 = results[10:20]
        scores_last = [r.score for r in last10 if r.score is not None]
        scores_prev = [r.score for r in prev10 if r.score is not None]
        avg_last = sum(scores_last) / len(scores_last) if scores_last else 0
        avg_prev = sum(scores_prev) / len(scores_prev) if scores_prev else 0
        delta = round(avg_last - avg_prev, 2)

        # Ability tier based on last10
        if avg_last < 60:
            tier = "struggling"
        elif avg_last < 85:
            tier = "on_level"
        else:
            tier = "advanced"

        # Per-subject breakdown (last10)
        subject_avgs: Dict[str, float] = {}
        subject_groups: Dict[str, List[float]] = {}
        for r in last10:
            subj = getattr(r, "subject", "unknown") or "unknown"
            if r.score is None:
                continue
            subject_groups.setdefault(subj, []).append(r.score)
        for subj, arr in subject_groups.items():
            subject_avgs[subj] = round(sum(arr) / len(arr), 2)

        # Flag low subjects for intervention
        weak_subjects = [subj for subj, a in subject_avgs.items() if a < 70]
        suggested_mode = "adaptive" if tier == "on_level" else ("scaffold" if tier == "struggling" else "mastery")

        summary["students"].append({
            "student_id": s.id,
            "name": getattr(s, "name", "Student"),
            "avg": round(avg_last, 2),
            "prev_avg": round(avg_prev, 2),
            "delta": delta,
            "ability": tier,
            "subjects": subject_avgs,
            "weak_subjects": weak_subjects,
            "suggested_mode": suggested_mode,
        })

        # Aggregate class-level subjects
        for subj, a in subject_avgs.items():
            agg = summary["subjects"].setdefault(subj, {"scores": []})
            agg["scores"].append(a)

        # Class flags: student with steep negative trend or multiple weak subjects
        if delta < -10 or len(weak_subjects) >= 2:
            summary["flags"].append({
                "student_id": s.id,
                "name": getattr(s, "name", "Student"),
                "delta": delta,
                "weak_subjects": weak_subjects,
            })

    # Compute class-level subject averages
    for subj, agg in summary["subjects"].items():
        arr = agg.get("scores", [])
        summary["subjects"][subj] = {"avg": round(sum(arr) / len(arr), 2) if arr else 0, "n": len(arr)}

    return summary


def build_progress_report(student_id: int) -> Dict:
    """Return a simple progress report for a student based on last 10 results."""
    results = (
        AssessmentResult.query.filter_by(student_id=student_id)
        .order_by(AssessmentResult.created_at.desc())
        .limit(10)
        .all()
    )
    scores = [r.score for r in results if r.score is not None]
    avg = sum(scores) / len(scores) if scores else 0
    return {"student_id": student_id, "avg": avg, "results": [{"score": r.score, "subject": r.subject, "created_at": r.created_at.isoformat()} for r in results]}
