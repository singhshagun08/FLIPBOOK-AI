import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Clock,
  Loader2,
  Send,
  AlertCircle,
  BookOpen,
} from "lucide-react";

import learningApi from "../../../services/api/learning.api";
import { getApiErrorMessage } from "../../../services/api/client";

import type { Quiz, QuizQuestion } from "../types/learning.types";

const QuizTakingPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const quizId = Number(id);

  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [questions, setQuestions] = useState<QuizQuestion[]>([]);

  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});

  const [timeRemaining, setTimeRemaining] = useState(0);

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const submissionStarted = useRef(false);
  const startTime = useRef<number | null>(null);

  // =========================================
  // FETCH QUIZ
  // =========================================

  useEffect(() => {
    let isMounted = true;

    const fetchQuiz = async () => {
      try {
        setLoading(true);
        setError("");

        if (!id || !Number.isInteger(quizId) || quizId <= 0) {
          throw new Error("Invalid quiz ID.");
        }

        const response = await learningApi.getQuiz(quizId);

        if (!response.success || !response.data?.quiz) {
          throw new Error(response.message || "Unable to load quiz.");
        }

        const fetchedQuiz = response.data.quiz;
        const fetchedQuestions = fetchedQuiz.questions ?? [];

        console.log("Fetched quiz:", fetchedQuiz);
        console.log("Fetched questions:", fetchedQuestions);

        if (fetchedQuestions.length === 0) {
          throw new Error(
            "This quiz has no saved questions. The AI generation process may not have completed successfully.",
          );
        }

        if (isMounted) {
          setQuiz(fetchedQuiz);
          setQuestions(fetchedQuestions);

          const duration = (fetchedQuiz.time_limit_minutes ?? 10) * 60;

          setTimeRemaining(duration);
          startTime.current = Date.now();
        }
      } catch (err) {
        if (isMounted) {
          setError(getApiErrorMessage(err));
          if (err instanceof Error) {
            setError(err.message);
          }
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchQuiz();

    return () => {
      isMounted = false;
    };
  }, [id, quizId]);

  // =========================================
  // SUBMIT QUIZ
  // =========================================

  const handleSubmit = useCallback(
    async (automatic = false) => {
      if (!quiz || submitting || submissionStarted.current) {
        return;
      }

      if (!automatic) {
        const confirmed = window.confirm(
          "Are you sure you want to submit your quiz?",
        );

        if (!confirmed) return;
      }

      submissionStarted.current = true;
      setSubmitting(true);
      setError("");

      try {
        const elapsedSeconds = startTime.current
          ? Math.floor((Date.now() - startTime.current) / 1000)
          : 0;

        const response = await learningApi.submitQuiz(quiz.id, {
          answers,
          time_taken_seconds: Math.max(0, elapsedSeconds),
        });

        if (!response.success || !response.data) {
          throw new Error(response.message || "Quiz submission failed.");
        }

        navigate(`/learning/quizzes/${quiz.id}/results`, {
          replace: true,
          state: {
            result: response.data,
            quiz,
          },
        });
      } catch (err) {
        submissionStarted.current = false;
        setSubmitting(false);
        setError(getApiErrorMessage(err));
      }
    },
    [answers, navigate, quiz, submitting],
  );

  // =========================================
  // COUNTDOWN TIMER
  // =========================================

  useEffect(() => {
    if (!quiz || loading || submitting || submissionStarted.current) {
      return;
    }

    if (timeRemaining <= 0) {
      handleSubmit(true);
      return;
    }

    const timer = window.setTimeout(() => {
      setTimeRemaining((previous) => Math.max(0, previous - 1));
    }, 1000);

    return () => window.clearTimeout(timer);
  }, [quiz, loading, submitting, timeRemaining, handleSubmit]);

  // =========================================
  // SELECT ANSWER
  // =========================================

  const selectAnswer = (questionId: number, optionKey: string) => {
    setAnswers((previous) => ({
      ...previous,
      [String(questionId)]: optionKey,
    }));
  };

  // =========================================
  // FORMAT TIMER
  // =========================================

  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;

    return `${String(minutes).padStart(2, "0")}:${String(
      remainingSeconds,
    ).padStart(2, "0")}`;
  };

  // =========================================
  // LOADING STATE
  // =========================================

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="text-center">
          <Loader2 className="mx-auto h-8 w-8 animate-spin text-violet-600" />

          <p className="mt-3 text-sm text-slate-500">Loading your quiz...</p>
        </div>
      </div>
    );
  }

  // =========================================
  // ERROR STATE
  // =========================================

  if (error && !quiz) {
    return (
      <div className="mx-auto max-w-xl rounded-2xl border border-red-200 bg-red-50 p-6 text-center">
        <AlertCircle className="mx-auto h-9 w-9 text-red-500" />

        <h2 className="mt-3 font-semibold text-red-800">Unable to load quiz</h2>

        <p className="mt-2 text-sm text-red-700">{error}</p>

        <button
          type="button"
          onClick={() => navigate("/learning")}
          className="mt-5 rounded-xl bg-violet-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-violet-700"
        >
          Back to Learning Studio
        </button>
      </div>
    );
  }

  if (!quiz || questions.length === 0) {
    return null;
  }

  const currentQuestion = questions[currentQuestionIndex];

  if (!currentQuestion) {
    return null;
  }

  const selectedAnswer = answers[String(currentQuestion.id)];

  const answeredCount = Object.keys(answers).length;

  const progress = (answeredCount / questions.length) * 100;

  const isLastQuestion = currentQuestionIndex === questions.length - 1;

  const optionEntries = Object.entries(currentQuestion.options ?? {});

  // =========================================
  // MAIN QUIZ INTERFACE
  // =========================================

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-4 md:p-6">
      {/* HEADER */}

      <div className="flex flex-wrap items-center justify-between gap-4">
        <button
          type="button"
          onClick={() => {
            const confirmed = window.confirm(
              "Your quiz progress may be lost. Are you sure you want to leave?",
            );

            if (confirmed) navigate("/learning");
          }}
          className="flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-violet-700"
        >
          <ArrowLeft size={17} />
          Back to Learning
        </button>

        <div
          className={`flex items-center gap-2 rounded-xl px-4 py-2 font-semibold ${
            timeRemaining <= 60
              ? "bg-red-50 text-red-600"
              : "bg-violet-50 text-violet-700"
          }`}
        >
          <Clock size={18} />
          {formatTime(timeRemaining)}
        </div>
      </div>

      {/* QUIZ TITLE */}

      <div className="rounded-2xl bg-gradient-to-r from-violet-700 to-indigo-600 p-6 text-white">
        <div className="flex items-center gap-3">
          <BookOpen size={26} />

          <span className="text-sm text-violet-100">FLIPBOOK-AI Quiz</span>
        </div>

        <h1 className="mt-3 text-2xl font-bold">{quiz.title}</h1>

        <p className="mt-2 text-sm text-violet-100">
          {quiz.description || "Answer the questions and test your knowledge."}
        </p>

        <div className="mt-5 flex flex-wrap gap-3 text-xs">
          <span className="rounded-full bg-white/15 px-3 py-1.5 capitalize">
            {quiz.difficulty}
          </span>

          <span className="rounded-full bg-white/15 px-3 py-1.5">
            {questions.length} Questions
          </span>

          <span className="rounded-full bg-white/15 px-3 py-1.5">
            Passing score: {quiz.passing_score}%
          </span>
        </div>
      </div>

      {/* PROGRESS */}

      <div className="rounded-2xl border border-slate-200 bg-white p-5">
        <div className="mb-3 flex items-center justify-between">
          <span className="text-sm font-medium text-slate-700">
            Your progress
          </span>

          <span className="text-sm font-semibold text-violet-700">
            {answeredCount}/{questions.length} answered
          </span>
        </div>

        <div className="h-2 overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full bg-violet-600 transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_280px]">
        {/* QUESTION AREA */}

        <div className="space-y-5">
          <section className="rounded-2xl border border-slate-200 bg-white p-5 md:p-7">
            <div className="mb-5 flex items-center justify-between">
              <span className="rounded-lg bg-violet-50 px-3 py-1.5 text-xs font-semibold text-violet-700">
                Question {currentQuestionIndex + 1} of {questions.length}
              </span>

              <span className="text-xs text-slate-500">
                {currentQuestion.marks} mark(s)
              </span>
            </div>

            <h2 className="text-lg font-semibold leading-relaxed text-slate-900 md:text-xl">
              {currentQuestion.question_text}
            </h2>

            <p className="mt-3 text-xs text-slate-400">Select one answer.</p>

            <div className="mt-6 space-y-3">
              {optionEntries.map(([key, value]) => {
                const isSelected = selectedAnswer === key;

                return (
                  <button
                    key={key}
                    type="button"
                    onClick={() => selectAnswer(currentQuestion.id, key)}
                    className={`flex w-full items-center gap-3 rounded-xl border p-4 text-left transition ${
                      isSelected
                        ? "border-violet-500 bg-violet-50"
                        : "border-slate-200 hover:border-violet-300 hover:bg-slate-50"
                    }`}
                  >
                    <span
                      className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-sm font-semibold ${
                        isSelected
                          ? "bg-violet-600 text-white"
                          : "bg-slate-100 text-slate-600"
                      }`}
                    >
                      {key}
                    </span>

                    <span className="flex-1 text-sm leading-relaxed text-slate-700">
                      {value}
                    </span>

                    {isSelected && (
                      <CheckCircle2
                        size={19}
                        className="shrink-0 text-violet-600"
                      />
                    )}
                  </button>
                );
              })}
            </div>

            {/* QUESTION NAVIGATION */}

            <div className="mt-8 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-5">
              <button
                type="button"
                disabled={currentQuestionIndex === 0}
                onClick={() =>
                  setCurrentQuestionIndex((previous) => previous - 1)
                }
                className="flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
              >
                <ArrowLeft size={16} />
                Previous
              </button>

              {isLastQuestion ? (
                <button
                  type="button"
                  onClick={() => handleSubmit(false)}
                  disabled={submitting}
                  className="flex items-center gap-2 rounded-xl bg-violet-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-violet-700 disabled:opacity-50"
                >
                  {submitting ? (
                    <Loader2 size={17} className="animate-spin" />
                  ) : (
                    <Send size={17} />
                  )}
                  Submit Quiz
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() =>
                    setCurrentQuestionIndex((previous) => previous + 1)
                  }
                  className="flex items-center gap-2 rounded-xl bg-violet-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-violet-700"
                >
                  Next
                  <ArrowRight size={16} />
                </button>
              )}
            </div>
          </section>

          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              {error}
            </div>
          )}
        </div>

        {/* QUESTION NAVIGATOR */}

        <aside className="h-fit rounded-2xl border border-slate-200 bg-white p-5">
          <h3 className="font-semibold text-slate-900">Question Navigator</h3>

          <p className="mt-1 text-xs text-slate-500">Jump to any question.</p>

          <div className="mt-5 grid grid-cols-5 gap-2">
            {questions.map((question, index) => {
              const isAnswered = Boolean(answers[String(question.id)]);

              const isCurrent = currentQuestionIndex === index;

              return (
                <button
                  key={question.id}
                  type="button"
                  onClick={() => setCurrentQuestionIndex(index)}
                  className={`flex h-10 items-center justify-center rounded-lg border text-sm font-semibold transition ${
                    isCurrent
                      ? "border-violet-600 bg-violet-600 text-white"
                      : isAnswered
                        ? "border-green-200 bg-green-50 text-green-700"
                        : "border-slate-200 bg-white text-slate-600 hover:border-violet-300"
                  }`}
                >
                  {index + 1}
                </button>
              );
            })}
          </div>

          <div className="mt-5 space-y-2 border-t border-slate-100 pt-4">
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span className="h-3 w-3 rounded bg-violet-600" />
              Current question
            </div>

            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span className="h-3 w-3 rounded bg-green-100" />
              Answered
            </div>

            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span className="h-3 w-3 rounded border border-slate-300" />
              Not answered
            </div>
          </div>

          <div className="mt-5 rounded-xl bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Remaining questions</p>

            <p className="mt-1 text-xl font-bold text-slate-900">
              {questions.length - answeredCount}
            </p>
          </div>

          <button
            type="button"
            onClick={() => handleSubmit(false)}
            disabled={submitting}
            className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl border border-violet-200 px-4 py-3 text-sm font-semibold text-violet-700 transition hover:bg-violet-50 disabled:opacity-50"
          >
            <Send size={16} />
            Submit Quiz
          </button>
        </aside>
      </div>
    </div>
  );
};

export default QuizTakingPage;
