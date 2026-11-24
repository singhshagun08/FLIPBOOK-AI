
from datetime import datetime, timezone

from flask import Blueprint, current_app, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import Document, Quiz, QuizQuestion, QuizAttempt
from app.services.learning_service import (
    get_learning_service,
    LearningServiceError,
)
from app.utils.responses import success_response, error_response


learning_bp = Blueprint("learning", __name__)


def get_current_user_id():
    try:
        return int(get_jwt_identity())
    except (TypeError, ValueError):
        return None


def get_owned_quiz(quiz_id, user_id):
    return Quiz.query.filter_by(
        id=quiz_id,
        user_id=user_id
    ).first()


# ============================================================
# 1. GENERATE AI QUIZ
# POST /api/learning/quizzes/generate
# ============================================================

@learning_bp.route(
    "/quizzes/generate",
    methods=["POST"]
)
@jwt_required()
def generate_quiz():

    user_id = get_current_user_id()

    if user_id is None:
        return error_response(
            "Invalid authenticated user.",
            status_code=401
        )

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return error_response(
            "A valid JSON object is required.",
            status_code=400
        )

    allowed_fields = {
        "document_ids",
        "number_of_questions",
        "difficulty",
        "title",
        "time_limit_minutes",
        "passing_score"
    }

    if not set(data).issubset(allowed_fields):
        return error_response(
            "Invalid quiz generation fields.",
            status_code=400
        )

    document_ids = data.get("document_ids")
    number_of_questions = data.get(
        "number_of_questions", 10
    )
    difficulty = data.get("difficulty", "medium")
    title = data.get("title")
    time_limit_minutes = data.get("time_limit_minutes")
    passing_score = data.get("passing_score", 50.0)

    if not isinstance(document_ids, list) or not document_ids:
        return error_response(
            "Select at least one document.",
            status_code=400
        )

    if (
        not isinstance(number_of_questions, int)
        or isinstance(number_of_questions, bool)
        or not 1 <= number_of_questions <= 30
    ):
        return error_response(
            "number_of_questions must be between 1 and 30.",
            status_code=400
        )

    if difficulty not in ("easy", "medium", "hard"):
        return error_response(
            "Difficulty must be easy, medium, or hard.",
            status_code=400
        )

    if title is not None and (
        not isinstance(title, str)
        or not title.strip()
        or len(title.strip()) > 255
    ):
        return error_response(
            "Title must contain between 1 and 255 characters.",
            status_code=400
        )

    if (
        time_limit_minutes is not None
        and (
            not isinstance(time_limit_minutes, int)
            or isinstance(time_limit_minutes, bool)
            or time_limit_minutes <= 0
        )
    ):
        return error_response(
            "time_limit_minutes must be a positive integer or null.",
            status_code=400
        )

    if (
        isinstance(passing_score, bool)
        or not isinstance(passing_score, (int, float))
        or not 0 <= passing_score <= 100
    ):
        return error_response(
            "passing_score must be between 0 and 100.",
            status_code=400
        )

    try:
        result = get_learning_service().generate_quiz(
            user_id=user_id,
            document_ids=document_ids,
            number_of_questions=number_of_questions,
            difficulty=difficulty,
            title=title,
            time_limit_minutes=time_limit_minutes,
            passing_score=passing_score
        )

        return success_response(
            message="AI quiz generated successfully.",
            data=result,
            status_code=201
        )

    except LearningServiceError as exc:
        return error_response(
            message=str(exc),
            status_code=400
        )

    except Exception:
        db.session.rollback()

        current_app.logger.exception(
            "Quiz generation API failed."
        )

        return error_response(
            "Unable to generate quiz.",
            status_code=500
        )


# ============================================================
# 2. LIST SAVED QUIZZES
# GET /api/learning/quizzes
# ============================================================

@learning_bp.route(
    "/quizzes",
    methods=["GET"]
)
@jwt_required()
def list_quizzes():

    user_id = get_current_user_id()

    if user_id is None:
        return error_response(
            "Invalid authenticated user.",
            status_code=401
        )

    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)

        if page is None or page < 1:
            return error_response(
                "Page must be positive.",
                status_code=400
            )

        if per_page is None or not 1 <= per_page <= 100:
            return error_response(
                "per_page must be between 1 and 100.",
                status_code=400
            )

        pagination = Quiz.query.filter_by(
            user_id=user_id
        ).order_by(
            Quiz.created_at.desc()
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        return success_response(
            message="Quizzes retrieved successfully.",
            data={
                "quizzes": [
                    quiz.to_dict()
                    for quiz in pagination.items
                ],
                "pagination": {
                    "page": pagination.page,
                    "per_page": pagination.per_page,
                    "total": pagination.total,
                    "pages": pagination.pages,
                    "has_next": pagination.has_next,
                    "has_previous": pagination.has_prev
                }
            }
        )

    except Exception:
        current_app.logger.exception(
            "Quiz listing failed."
        )

        return error_response(
            "Unable to retrieve quizzes.",
            status_code=500
        )


# ============================================================
# 3. GET QUIZ QUESTIONS
# GET /api/learning/quizzes/<quiz_id>
# ============================================================

@learning_bp.route(
    "/quizzes/<int:quiz_id>",
    methods=["GET"]
)
@jwt_required()
def get_quiz(quiz_id):

    user_id = get_current_user_id()

    if user_id is None:
        return error_response(
            "Invalid authenticated user.",
            status_code=401
        )

    quiz = get_owned_quiz(quiz_id, user_id)

    if quiz is None:
        return error_response(
            "Quiz not found.",
            status_code=404
        )

    try:
        return success_response(
            message="Quiz retrieved successfully.",
            data={
                "quiz": quiz.to_dict(),
                "questions": [
                    question.to_dict(include_answer=False)
                    for question in quiz.questions
                ]
            }
        )

    except Exception:
        current_app.logger.exception(
            "Quiz retrieval failed."
        )

        return error_response(
            "Unable to retrieve quiz.",
            status_code=500
        )


# ============================================================
# 4. SUBMIT QUIZ ANSWERS
# POST /api/learning/quizzes/<quiz_id>/submit
# ============================================================

@learning_bp.route(
    "/quizzes/<int:quiz_id>/submit",
    methods=["POST"]
)
@jwt_required()
def submit_quiz(quiz_id):

    user_id = get_current_user_id()

    if user_id is None:
        return error_response(
            "Invalid authenticated user.",
            status_code=401
        )

    quiz = get_owned_quiz(quiz_id, user_id)

    if quiz is None:
        return error_response(
            "Quiz not found.",
            status_code=404
        )

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return error_response(
            "A valid JSON object is required.",
            status_code=400
        )

    if not set(data).issubset({
        "answers",
        "time_taken_seconds"
    }):
        return error_response(
            "Invalid submission fields.",
            status_code=400
        )

    answers = data.get("answers")

    if not isinstance(answers, dict):
        return error_response(
            "Answers must be a JSON object.",
            status_code=400
        )

    time_taken = data.get("time_taken_seconds")

    if (
        time_taken is not None
        and (
            not isinstance(time_taken, int)
            or isinstance(time_taken, bool)
            or time_taken < 0
        )
    ):
        return error_response(
            "time_taken_seconds must be a non-negative integer.",
            status_code=400
        )

    questions = quiz.questions

    if not questions:
        return error_response(
            "This quiz has no questions.",
            status_code=400
        )

    valid_question_ids = {
        str(question.id)
        for question in questions
    }

    if not set(answers).issubset(valid_question_ids):
        return error_response(
            "Submission contains invalid question IDs.",
            status_code=400
        )

    score = 0.0
    total_marks = 0.0
    answer_results = []

    for question in questions:

        submitted_answer = answers.get(
            str(question.id)
        )

        correct_answer = question.correct_answer

        if isinstance(correct_answer, str):
            is_correct = (
                isinstance(submitted_answer, str)
                and submitted_answer.strip().upper()
                == correct_answer.strip().upper()
            )
        else:
            is_correct = submitted_answer == correct_answer

        total_marks += question.marks

        if is_correct:
            score += question.marks

        answer_results.append({
            "question_id": question.id,
            "submitted_answer": submitted_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "marks_obtained": (
                question.marks if is_correct else 0
            ),
            "total_marks": question.marks,
            "explanation": question.explanation
        })

    percentage = (
        (score / total_marks) * 100
        if total_marks > 0
        else 0
    )

    is_passed = percentage >= quiz.passing_score

    try:
        now = datetime.now(timezone.utc)

        attempt = QuizAttempt(
            user_id=user_id,
            quiz_id=quiz.id,
            score=score,
            total_marks=total_marks,
            percentage=round(percentage, 2),
            answers=answers,
            is_passed=is_passed,
            time_taken_seconds=time_taken,
            started_at=None,
            completed_at=now
        )

        db.session.add(attempt)
        db.session.commit()

        return success_response(
            message="Quiz submitted successfully.",
            data={
                "attempt": attempt.to_dict(),
                "results": answer_results,
                "summary": {
                    "correct_answers": sum(
                        1 for item in answer_results
                        if item["is_correct"]
                    ),
                    "total_questions": len(questions),
                    "score": score,
                    "total_marks": total_marks,
                    "percentage": round(percentage, 2),
                    "is_passed": is_passed,
                    "passing_score": quiz.passing_score
                }
            },
            status_code=201
        )

    except Exception:
        db.session.rollback()

        current_app.logger.exception(
            "Quiz submission failed."
        )

        return error_response(
            "Unable to submit quiz.",
            status_code=500
        )


# ============================================================
# 5. GET QUIZ ATTEMPT HISTORY
# GET /api/learning/attempts
# ============================================================

@learning_bp.route(
    "/attempts",
    methods=["GET"]
)
@jwt_required()
def list_quiz_attempts():

    user_id = get_current_user_id()

    if user_id is None:
        return error_response(
            "Invalid authenticated user.",
            status_code=401
        )

    try:
        # -----------------------------------------
        # 1. Read query parameters
        # -----------------------------------------

        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        quiz_id = request.args.get("quiz_id", type=int)
        performance = request.args.get("performance", "all")

        # -----------------------------------------
        # 2. Validate parameters
        # -----------------------------------------

        if page is None or page < 1:
            return error_response(
                "Page must be a positive integer.",
                status_code=400
            )

        if per_page is None or not 1 <= per_page <= 100:
            return error_response(
                "per_page must be between 1 and 100.",
                status_code=400
            )

        if quiz_id is not None and quiz_id < 1:
            return error_response(
                "Invalid quiz ID.",
                status_code=400
            )

        if performance not in ("all", "passed", "failed"):
            return error_response(
                "Performance must be all, passed, or failed.",
                status_code=400
            )

        # -----------------------------------------
        # 3. Build user-specific query
        # -----------------------------------------

        query = QuizAttempt.query.filter_by(
            user_id=user_id
        )

        if quiz_id is not None:
            query = query.filter(
                QuizAttempt.quiz_id == quiz_id
            )

        if performance == "passed":
            query = query.filter(
                QuizAttempt.is_passed.is_(True)
            )

        elif performance == "failed":
            query = query.filter(
                QuizAttempt.is_passed.is_(False)
            )

        # -----------------------------------------
        # 4. Apply pagination
        # -----------------------------------------

        pagination = query.order_by(
            QuizAttempt.created_at.desc()
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        # -----------------------------------------
        # 5. Prepare attempt history
        # -----------------------------------------

        attempt_history = []

        for attempt in pagination.items:

            attempt_data = attempt.to_dict()

            attempt_data["quiz"] = (
                attempt.quiz.to_dict()
                if attempt.quiz else None
            )

            attempt_history.append(attempt_data)

        # -----------------------------------------
        # 6. Return response
        # -----------------------------------------

        return success_response(
            message="Quiz attempt history retrieved successfully.",
            data={
                "attempts": attempt_history,
                "pagination": {
                    "page": pagination.page,
                    "per_page": pagination.per_page,
                    "total": pagination.total,
                    "pages": pagination.pages,
                    "has_next": pagination.has_next,
                    "has_previous": pagination.has_prev
                }
            }
        )

    except Exception:
        current_app.logger.exception(
            "Quiz attempt history retrieval failed."
        )

        return error_response(
            "Unable to retrieve quiz attempts.",
            status_code=500
        )
