
from datetime import datetime, timezone

from sqlalchemy import (
    Index,
    CheckConstraint
)
from sqlalchemy.types import JSON

from app.extensions import db


def utc_now():
    return datetime.now(timezone.utc)


# =====================================================
# 1. LEARNING NOTE MODEL
# Stores personal and AI-generated study notes.
# =====================================================

class LearningNote(db.Model):

    __tablename__ = "learning_notes"

    __table_args__ = (
        Index(
            "ix_learning_notes_user_updated",
            "user_id",
            "updated_at"
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    document_id = db.Column(
        db.Integer,
        db.ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    title = db.Column(
        db.String(255),
        nullable=False
    )

    content = db.Column(
        db.Text,
        nullable=False
    )

    note_type = db.Column(
        db.String(30),
        nullable=False,
        default="personal"
    )

    tags = db.Column(
        JSON,
        nullable=True
    )

    is_favorite = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "learning_notes",
            lazy="dynamic",
            passive_deletes=True
        )
    )

    document = db.relationship(
        "Document",
        backref=db.backref(
            "learning_notes",
            lazy="dynamic",
            passive_deletes=True
        )
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "document_id": self.document_id,
            "title": self.title,
            "content": self.content,
            "note_type": self.note_type,
            "tags": self.tags,
            "is_favorite": self.is_favorite,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at else None
            ),
            "updated_at": (
                self.updated_at.isoformat()
                if self.updated_at else None
            )
        }

    def __repr__(self):
        return f"<LearningNote {self.id}: {self.title}>"


# =====================================================
# 2. FLASHCARD MODEL
# Stores question-and-answer study cards.
# =====================================================

class Flashcard(db.Model):

    __tablename__ = "flashcards"

    __table_args__ = (
        Index(
            "ix_flashcards_user_document",
            "user_id",
            "document_id"
        ),
        CheckConstraint(
            "difficulty IN ('easy', 'medium', 'hard')",
            name="check_flashcard_difficulty"
        ),
        CheckConstraint(
            "review_count >= 0",
            name="check_flashcard_review_count"
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    document_id = db.Column(
        db.Integer,
        db.ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    question = db.Column(
        db.Text,
        nullable=False
    )

    answer = db.Column(
        db.Text,
        nullable=False
    )

    explanation = db.Column(
        db.Text,
        nullable=True
    )

    difficulty = db.Column(
        db.String(20),
        nullable=False,
        default="medium"
    )

    tags = db.Column(
        JSON,
        nullable=True
    )

    is_mastered = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    review_count = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    next_review_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    last_reviewed_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "flashcards",
            lazy="dynamic",
            passive_deletes=True
        )
    )

    document = db.relationship(
        "Document",
        backref=db.backref(
            "flashcards",
            lazy="dynamic",
            passive_deletes=True
        )
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "document_id": self.document_id,
            "question": self.question,
            "answer": self.answer,
            "explanation": self.explanation,
            "difficulty": self.difficulty,
            "tags": self.tags,
            "is_mastered": self.is_mastered,
            "review_count": self.review_count,
            "next_review_at": (
                self.next_review_at.isoformat()
                if self.next_review_at else None
            ),
            "last_reviewed_at": (
                self.last_reviewed_at.isoformat()
                if self.last_reviewed_at else None
            ),
            "created_at": (
                self.created_at.isoformat()
                if self.created_at else None
            )
        }

    def __repr__(self):
        return f"<Flashcard {self.id}>"


# =====================================================
# 3. QUIZ MODEL
# Stores quiz configuration and metadata.
# =====================================================

class Quiz(db.Model):

    __tablename__ = "quizzes"

    __table_args__ = (
        Index(
            "ix_quizzes_user_created",
            "user_id",
            "created_at"
        ),
        CheckConstraint(
            "total_questions >= 0",
            name="check_quiz_total_questions"
        ),
        CheckConstraint(
            "time_limit_minutes IS NULL OR time_limit_minutes > 0",
            name="check_quiz_time_limit"
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    document_id = db.Column(
        db.Integer,
        db.ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    title = db.Column(
        db.String(255),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    difficulty = db.Column(
        db.String(20),
        nullable=False,
        default="medium"
    )

    total_questions = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    time_limit_minutes = db.Column(
        db.Integer,
        nullable=True
    )

    passing_score = db.Column(
        db.Float,
        nullable=False,
        default=50.0
    )

    is_published = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "quizzes",
            lazy="dynamic",
            passive_deletes=True
        )
    )

    document = db.relationship(
        "Document",
        backref=db.backref(
            "quizzes",
            lazy="dynamic",
            passive_deletes=True
        )
    )

    questions = db.relationship(
        "QuizQuestion",
        back_populates="quiz",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="QuizQuestion.question_number"
    )

    attempts = db.relationship(
        "QuizAttempt",
        back_populates="quiz",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="QuizAttempt.created_at.desc()"
    )

    def to_dict(self, include_questions=False):
        result = {
            "id": self.id,
            "user_id": self.user_id,
            "document_id": self.document_id,
            "title": self.title,
            "description": self.description,
            "difficulty": self.difficulty,
            "total_questions": self.total_questions,
            "time_limit_minutes": self.time_limit_minutes,
            "passing_score": self.passing_score,
            "is_published": self.is_published,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at else None
            )
        }

        if include_questions:
            result["questions"] = [
                question.to_dict()
                for question in self.questions
            ]

        return result

    def __repr__(self):
        return f"<Quiz {self.id}: {self.title}>"


# =====================================================
# 4. QUIZ QUESTION MODEL
# Stores individual quiz questions and answers.
# =====================================================

class QuizQuestion(db.Model):

    __tablename__ = "quiz_questions"

    __table_args__ = (
        Index(
            "ix_quiz_questions_quiz_number",
            "quiz_id",
            "question_number",
            unique=True
        ),
        CheckConstraint(
            "question_number >= 1",
            name="check_question_number"
        ),
        CheckConstraint(
            "marks > 0",
            name="check_question_marks"
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    quiz_id = db.Column(
        db.Integer,
        db.ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    question_number = db.Column(
        db.Integer,
        nullable=False
    )

    question_text = db.Column(
        db.Text,
        nullable=False
    )

    question_type = db.Column(
        db.String(30),
        nullable=False,
        default="multiple_choice"
    )

    options = db.Column(
        JSON,
        nullable=True
    )

    correct_answer = db.Column(
        JSON,
        nullable=False
    )

    explanation = db.Column(
        db.Text,
        nullable=True
    )

    marks = db.Column(
        db.Float,
        nullable=False,
        default=1.0
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    quiz = db.relationship(
        "Quiz",
        back_populates="questions"
    )

    def to_dict(self, include_answer=False):
        result = {
            "id": self.id,
            "quiz_id": self.quiz_id,
            "question_number": self.question_number,
            "question_text": self.question_text,
            "question_type": self.question_type,
            "options": self.options,
            "explanation": self.explanation,
            "marks": self.marks
        }

        if include_answer:
            result["correct_answer"] = self.correct_answer

        return result

    def __repr__(self):
        return f"<QuizQuestion {self.id}>"


# =====================================================
# 5. QUIZ ATTEMPT MODEL
# Stores user quiz attempts and results.
# =====================================================

class QuizAttempt(db.Model):

    __tablename__ = "quiz_attempts"

    __table_args__ = (
        Index(
            "ix_quiz_attempts_user_quiz",
            "user_id",
            "quiz_id"
        ),
        CheckConstraint(
            "score >= 0",
            name="check_quiz_attempt_score"
        ),
        CheckConstraint(
            "total_marks >= 0",
            name="check_quiz_attempt_total_marks"
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    quiz_id = db.Column(
        db.Integer,
        db.ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    score = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    total_marks = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    percentage = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    answers = db.Column(
        JSON,
        nullable=False,
        default=dict
    )

    is_passed = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    time_taken_seconds = db.Column(
        db.Integer,
        nullable=True
    )

    started_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    completed_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "quiz_attempts",
            lazy="dynamic",
            passive_deletes=True
        )
    )

    quiz = db.relationship(
        "Quiz",
        back_populates="attempts"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "quiz_id": self.quiz_id,
            "score": self.score,
            "total_marks": self.total_marks,
            "percentage": self.percentage,
            "answers": self.answers,
            "is_passed": self.is_passed,
            "time_taken_seconds": self.time_taken_seconds,
            "started_at": (
                self.started_at.isoformat()
                if self.started_at else None
            ),
            "completed_at": (
                self.completed_at.isoformat()
                if self.completed_at else None
            ),
            "created_at": (
                self.created_at.isoformat()
                if self.created_at else None
            )
        }

    def __repr__(self):
        return f"<QuizAttempt {self.id}: quiz={self.quiz_id}>"
