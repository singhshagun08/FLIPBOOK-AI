import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import {
  Trophy,
  CheckCircle2,
  XCircle,
  Clock,
  Target,
  ArrowLeft,
  RotateCcw,
  BookOpen,
  AlertCircle,
} from "lucide-react";

import type {
  Quiz,
  SubmitQuizResult,
  QuizQuestion,
} from "../types/learning.types";

interface QuizResultsLocationState {
  result?: SubmitQuizResult;
  quiz?: Quiz;
}

const QuizResultsPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();

  const state = location.state as QuizResultsLocationState | null;

  const result = state?.result;
  const quiz = state?.quiz;

  // -----------------------------------------
  // Validate Results
  // -----------------------------------------

  if (!result || !quiz) {
    return (
      <div className="mx-auto flex min-h-[400px] max-w-xl flex-col items-center justify-center rounded-2xl border border-slate-200 bg-white p-8 text-center">
        <AlertCircle className="h-12 w-12 text-amber-500" />

        <h2 className="mt-4 text-xl font-bold text-slate-900">
          Results unavailable
        </h2>

        <p className="mt-2 text-sm text-slate-500">
          Quiz result information is missing. Please return to the Learning
          Studio.
        </p>

        <Link
          to="/learning"
          className="mt-6 rounded-xl bg-violet-600 px-5 py-3 text-sm font-semibold text-white hover:bg-violet-700"
        >
          Back to Learning Studio
        </Link>
      </div>
    );
  }

  const { attempt, results, summary } = result;

  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;

    return `${minutes} min ${remainingSeconds} sec`;
  };

  const getQuestion = (questionId: number): QuizQuestion | undefined => {
    return quiz.questions?.find((question) => question.id === questionId);
  };

  // -----------------------------------------
  // Results Page
  // -----------------------------------------

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-4 md:p-6">
      {/* HEADER */}
      <div className="flex items-center justify-between gap-3">
        <button
          type="button"
          onClick={() => navigate("/learning")}
          className="flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-violet-700"
        >
          <ArrowLeft size={17} />
          Learning Studio
        </button>

        <span className="rounded-full bg-violet-50 px-3 py-1.5 text-xs font-semibold text-violet-700">
          Quiz Completed
        </span>
      </div>

      {/* SCORE HERO */}
      <section
        className={`overflow-hidden rounded-2xl p-6 text-white md:p-8 ${
          summary.is_passed
            ? "bg-gradient-to-r from-emerald-600 to-teal-600"
            : "bg-gradient-to-r from-violet-700 to-indigo-600"
        }`}
      >
        <div className="flex flex-col items-center text-center">
          <div className="rounded-full bg-white/15 p-4">
            {summary.is_passed ? <Trophy size={42} /> : <Target size={42} />}
          </div>

          <h1 className="mt-4 text-2xl font-bold md:text-3xl">
            {summary.is_passed
              ? "Congratulations! You Passed!"
              : "Keep Practicing!"}
          </h1>

          <p className="mt-2 text-sm text-white/80">{quiz.title}</p>

          <div className="my-6">
            <p className="text-6xl font-bold tracking-tight">
              {summary.percentage.toFixed(1)}%
            </p>

            <p className="mt-2 text-sm text-white/80">Your final score</p>
          </div>

          <div className="flex flex-wrap justify-center gap-3">
            <span className="rounded-full bg-white/15 px-4 py-2 text-sm">
              {summary.score} / {summary.total_marks} marks
            </span>

            <span className="rounded-full bg-white/15 px-4 py-2 text-sm">
              {summary.correct_answers} / {summary.total_questions} correct
            </span>

            <span className="rounded-full bg-white/15 px-4 py-2 text-sm">
              Passing: {summary.passing_score}%
            </span>
          </div>
        </div>
      </section>

      {/* STATISTICS */}
      <section className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-emerald-50 p-3 text-emerald-600">
              <CheckCircle2 size={22} />
            </div>

            <div>
              <p className="text-sm text-slate-500">Correct answers</p>
              <p className="text-2xl font-bold text-slate-900">
                {summary.correct_answers}
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-red-50 p-3 text-red-600">
              <XCircle size={22} />
            </div>

            <div>
              <p className="text-sm text-slate-500">Incorrect answers</p>
              <p className="text-2xl font-bold text-slate-900">
                {summary.total_questions - summary.correct_answers}
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-violet-50 p-3 text-violet-600">
              <Clock size={22} />
            </div>

            <div>
              <p className="text-sm text-slate-500">Time taken</p>
              <p className="text-xl font-bold text-slate-900">
                {formatTime(attempt.time_taken_seconds)}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ANSWER REVIEW */}
      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Answer Review</h2>

          <p className="mt-1 text-sm text-slate-500">
            Review every question, compare your answers and understand the
            explanations.
          </p>
        </div>

        {results.map((questionResult, index) => {
          const question = getQuestion(questionResult.question_id);

          const selectedAnswer = questionResult.submitted_answer;
          const correctAnswer = questionResult.correct_answer;

          const options = question?.options ?? {};

          return (
            <article
              key={questionResult.question_id}
              className="overflow-hidden rounded-2xl border border-slate-200 bg-white"
            >
              {/* QUESTION HEADER */}
              <div
                className={`flex items-center justify-between gap-3 border-b px-5 py-4 ${
                  questionResult.is_correct
                    ? "border-emerald-100 bg-emerald-50"
                    : "border-red-100 bg-red-50"
                }`}
              >
                <div className="flex items-center gap-2">
                  {questionResult.is_correct ? (
                    <CheckCircle2 size={20} className="text-emerald-600" />
                  ) : (
                    <XCircle size={20} className="text-red-600" />
                  )}

                  <span
                    className={`text-sm font-semibold ${
                      questionResult.is_correct
                        ? "text-emerald-700"
                        : "text-red-700"
                    }`}
                  >
                    Question {index + 1}
                  </span>
                </div>

                <span className="text-xs font-semibold text-slate-600">
                  {questionResult.marks_obtained} / {questionResult.total_marks}{" "}
                  marks
                </span>
              </div>

              {/* QUESTION BODY */}
              <div className="space-y-4 p-5">
                <h3 className="font-semibold leading-relaxed text-slate-900">
                  {question?.question_text ?? `Question ${index + 1}`}
                </h3>

                {/* OPTIONS */}
                <div className="space-y-2">
                  {Object.entries(options).map(([key, value]) => {
                    const isCorrectOption = key === correctAnswer;
                    const isSelectedOption = key === selectedAnswer;

                    let optionStyle =
                      "border-slate-200 bg-white text-slate-700";

                    if (isCorrectOption) {
                      optionStyle =
                        "border-emerald-300 bg-emerald-50 text-emerald-800";
                    } else if (isSelectedOption) {
                      optionStyle = "border-red-300 bg-red-50 text-red-800";
                    }

                    return (
                      <div
                        key={key}
                        className={`flex items-center gap-3 rounded-xl border p-3 ${optionStyle}`}
                      >
                        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white/80 text-sm font-semibold">
                          {key}
                        </span>

                        <span className="flex-1 text-sm">{value}</span>

                        {isCorrectOption && (
                          <CheckCircle2
                            size={19}
                            className="shrink-0 text-emerald-600"
                          />
                        )}

                        {isSelectedOption && !isCorrectOption && (
                          <XCircle
                            size={19}
                            className="shrink-0 text-red-600"
                          />
                        )}
                      </div>
                    );
                  })}
                </div>

                {/* ANSWER SUMMARY */}
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-xl bg-slate-50 p-3">
                    <p className="text-xs font-medium text-slate-500">
                      Your answer
                    </p>

                    <p className="mt-1 text-sm font-semibold text-slate-800">
                      {selectedAnswer
                        ? `${selectedAnswer}: ${options[selectedAnswer] ?? ""}`
                        : "Not answered"}
                    </p>
                  </div>

                  <div className="rounded-xl bg-emerald-50 p-3">
                    <p className="text-xs font-medium text-emerald-700">
                      Correct answer
                    </p>

                    <p className="mt-1 text-sm font-semibold text-emerald-800">
                      {correctAnswer}: {options[correctAnswer] ?? ""}
                    </p>
                  </div>
                </div>

                {/* EXPLANATION */}
                {questionResult.explanation && (
                  <div className="rounded-xl border border-violet-100 bg-violet-50 p-4">
                    <div className="flex items-center gap-2">
                      <BookOpen size={17} className="text-violet-600" />

                      <p className="text-sm font-semibold text-violet-800">
                        Explanation
                      </p>
                    </div>

                    <p className="mt-2 text-sm leading-relaxed text-slate-700">
                      {questionResult.explanation}
                    </p>
                  </div>
                )}
              </div>
            </article>
          );
        })}
      </section>

      {/* ACTION BUTTONS */}
      <section className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-5 sm:flex-row">
        <button
          type="button"
          onClick={() => navigate(`/learning/quizzes/${id}`)}
          className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-violet-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-violet-700"
        >
          <RotateCcw size={17} />
          Retake Quiz
        </button>

        <button
          type="button"
          onClick={() => navigate("/learning")}
          className="flex flex-1 items-center justify-center gap-2 rounded-xl border border-slate-200 px-5 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
        >
          <BookOpen size={17} />
          Back to Learning Studio
        </button>
      </section>
    </div>
  );
};

export default QuizResultsPage;
