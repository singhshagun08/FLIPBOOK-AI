import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  BookOpen,
  Search,
  RefreshCw,
  ClipboardList,
  Clock,
  CalendarDays,
  Play,
  AlertCircle,
} from "lucide-react";

import { learningApi } from "../../../services/api/learning.api";
import type { Quiz } from "../types/learning.types";

type DifficultyFilter = "all" | "easy" | "medium" | "hard";

const MyQuizzes = () => {
  const navigate = useNavigate();

  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [search, setSearch] = useState("");
  const [difficulty, setDifficulty] = useState<DifficultyFilter>("all");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchQuizzes = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await learningApi.getQuizzes({
        page: 1,
        per_page: 100,
      });

      if (!response.success) {
        throw new Error(response.message || "Failed to load quizzes.");
      }

      setQuizzes(response.data?.quizzes ?? []);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to load your quizzes.",
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQuizzes();
  }, []);

  const filteredQuizzes = useMemo(() => {
    return quizzes.filter((quiz) => {
      const matchesSearch = quiz.title
        .toLowerCase()
        .includes(search.toLowerCase());

      const matchesDifficulty =
        difficulty === "all" || quiz.difficulty === difficulty;

      return matchesSearch && matchesDifficulty;
    });
  }, [quizzes, search, difficulty]);

  const formatDate = (date?: string) => {
    if (!date) return "Date unavailable";

    const parsedDate = new Date(date);

    if (Number.isNaN(parsedDate.getTime())) {
      return "Date unavailable";
    }

    return parsedDate.toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  };

  const difficultyStyle: Record<string, string> = {
    easy: "bg-green-100 text-green-700",
    medium: "bg-yellow-100 text-yellow-700",
    hard: "bg-red-100 text-red-700",
  };

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">My Quizzes</h2>
          <p className="mt-1 text-sm text-slate-500">
            View and practice quizzes generated from your PDFs.
          </p>
        </div>

        <button
          type="button"
          onClick={fetchQuizzes}
          disabled={loading}
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* SEARCH AND FILTER */}
      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />

          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search quizzes..."
            className="w-full rounded-xl border border-slate-200 bg-white py-3 pl-10 pr-4 text-sm outline-none transition focus:border-violet-400 focus:ring-2 focus:ring-violet-100"
          />
        </div>

        <select
          value={difficulty}
          onChange={(e) => setDifficulty(e.target.value as DifficultyFilter)}
          className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-violet-400"
        >
          <option value="all">All difficulties</option>
          <option value="easy">Easy</option>
          <option value="medium">Medium</option>
          <option value="hard">Hard</option>
        </select>
      </div>

      {/* QUIZ COUNT */}
      <div className="flex items-center gap-2 text-sm text-slate-500">
        <ClipboardList className="h-4 w-4 text-violet-600" />
        {filteredQuizzes.length} quiz
        {filteredQuizzes.length !== 1 ? "zes" : ""} found
      </div>

      {/* LOADING */}
      {loading && (
        <div className="rounded-2xl border border-slate-200 bg-white p-12 text-center">
          <RefreshCw className="mx-auto h-8 w-8 animate-spin text-violet-600" />
          <p className="mt-3 text-sm text-slate-500">Loading your quizzes...</p>
        </div>
      )}

      {/* ERROR */}
      {!loading && error && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-5">
          <div className="flex items-center gap-2 text-red-700">
            <AlertCircle className="h-5 w-5" />
            <p className="font-medium">Could not load quizzes</p>
          </div>

          <p className="mt-2 text-sm text-red-600">{error}</p>

          <button
            type="button"
            onClick={fetchQuizzes}
            className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
          >
            Try again
          </button>
        </div>
      )}

      {/* EMPTY STATE */}
      {!loading && !error && quizzes.length === 0 && (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center">
          <BookOpen className="mx-auto h-12 w-12 text-violet-400" />

          <h3 className="mt-4 text-lg font-semibold text-slate-900">
            No quizzes yet
          </h3>

          <p className="mt-2 text-sm text-slate-500">
            Generate your first quiz from an uploaded PDF.
          </p>
        </div>
      )}

      {/* NO SEARCH RESULTS */}
      {!loading &&
        !error &&
        quizzes.length > 0 &&
        filteredQuizzes.length === 0 && (
          <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center">
            <Search className="mx-auto h-10 w-10 text-slate-300" />
            <p className="mt-3 font-medium text-slate-700">
              No matching quizzes found
            </p>
            <p className="mt-1 text-sm text-slate-500">
              Try another search or difficulty filter.
            </p>
          </div>
        )}

      {/* QUIZ CARDS */}
      {!loading && !error && filteredQuizzes.length > 0 && (
        <div className="grid gap-5 md:grid-cols-2">
          {filteredQuizzes.map((quiz) => (
            <div
              key={quiz.id}
              className="rounded-2xl border border-slate-200 bg-white p-5 transition hover:border-violet-300 hover:shadow-md"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="rounded-xl bg-violet-100 p-3">
                  <BookOpen className="h-6 w-6 text-violet-700" />
                </div>

                <span
                  className={`rounded-full px-3 py-1 text-xs font-semibold capitalize ${
                    difficultyStyle[quiz.difficulty] ||
                    "bg-slate-100 text-slate-600"
                  }`}
                >
                  {quiz.difficulty}
                </span>
              </div>

              <h3 className="mt-4 text-lg font-semibold text-slate-900">
                {quiz.title}
              </h3>

              {quiz.description && (
                <p className="mt-2 line-clamp-2 text-sm text-slate-500">
                  {quiz.description}
                </p>
              )}

              <div className="mt-5 flex flex-wrap gap-4 text-xs text-slate-500">
                <span className="flex items-center gap-1.5">
                  <ClipboardList className="h-4 w-4" />
                  {quiz.total_questions} Questions
                </span>

                <span className="flex items-center gap-1.5">
                  <Clock className="h-4 w-4" />
                  {quiz.time_limit_minutes
                    ? `${quiz.time_limit_minutes} min`
                    : "No time limit"}
                </span>

                <span className="flex items-center gap-1.5">
                  <CalendarDays className="h-4 w-4" />
                  {formatDate(quiz.created_at)}
                </span>
              </div>

              <div className="mt-5 border-t border-slate-100 pt-4">
                <button
                  type="button"
                  onClick={() => navigate(`/learning/quizzes/${quiz.id}`)}
                  className="flex w-full items-center justify-center gap-2 rounded-xl bg-violet-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-violet-700"
                >
                  <Play className="h-4 w-4" />
                  Start Quiz
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default MyQuizzes;
