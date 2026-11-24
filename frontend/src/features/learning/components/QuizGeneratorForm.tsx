import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  FileText,
  Sparkles,
  Clock,
  Target,
  BookOpen,
  Loader2,
} from "lucide-react";

import documentsApi from "../../../services/api/documents.api";
import learningApi from "../../../services/api/learning.api";
import { getApiErrorMessage } from "../../../services/api/client";

import type { Document } from "../../../services/api/documents.api";
import type {
  QuizDifficulty,
  GenerateQuizPayload,
} from "../types/learning.types";

const QuizGeneratorForm = () => {
  const navigate = useNavigate();

  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocuments, setSelectedDocuments] = useState<number[]>([]);
  const [difficulty, setDifficulty] = useState<QuizDifficulty>("easy");
  const [numberOfQuestions, setNumberOfQuestions] = useState(5);
  const [timeLimit, setTimeLimit] = useState(10);
  const [passingScore, setPassingScore] = useState(60);

  const [loadingDocuments, setLoadingDocuments] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        setLoadingDocuments(true);
        setError("");

        const response = await documentsApi.getAll({
          page: 1,
          per_page: 100,
        });

        const completedDocuments = response.data.documents.filter(
          (document) => document.processing_status === "completed",
        );

        setDocuments(completedDocuments);
      } catch (err) {
        setError(getApiErrorMessage(err));
      } finally {
        setLoadingDocuments(false);
      }
    };

    fetchDocuments();
  }, []);

  const toggleDocument = (documentId: number) => {
    setSelectedDocuments((current) =>
      current.includes(documentId)
        ? current.filter((id) => id !== documentId)
        : [...current, documentId],
    );
  };

  const handleGenerate = async () => {
    if (selectedDocuments.length === 0) {
      setError("Please select at least one processed PDF.");
      return;
    }

    const payload: GenerateQuizPayload = {
      document_ids: selectedDocuments,
      number_of_questions: numberOfQuestions,
      difficulty,
      time_limit_minutes: timeLimit,
      passing_score: passingScore,
    };

    try {
      setGenerating(true);
      setError("");
      setSuccessMessage("");

      const response = await learningApi.generateQuiz(payload);

      if (!response.success || !response.data?.quiz?.id) {
        throw new Error(response.message || "Quiz generation failed.");
      }

      setSuccessMessage("Quiz generated successfully!");

      navigate(`/learning/quizzes/${response.data.quiz.id}`);
    } catch (err) {
      setError(
        err instanceof Error && err.message
          ? err.message
          : getApiErrorMessage(err),
      );
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-violet-500" />
          <h2 className="text-xl font-semibold text-slate-900">
            AI Quiz Generator
          </h2>
        </div>
        <p className="mt-1 text-sm text-slate-500">
          Generate quizzes from your uploaded and processed PDF documents.
        </p>
      </div>

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {successMessage && (
        <div className="rounded-xl border border-green-200 bg-green-50 p-4 text-sm text-green-700">
          {successMessage}
        </div>
      )}

      {/* DOCUMENT SELECTION */}
      <section className="rounded-2xl border border-slate-200 bg-white p-5">
        <div className="mb-4 flex items-center gap-2">
          <FileText className="h-5 w-5 text-violet-600" />
          <h3 className="font-semibold text-slate-900">
            1. Select PDF documents
          </h3>
        </div>

        {loadingDocuments ? (
          <div className="flex items-center gap-2 py-6 text-sm text-slate-500">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading your documents...
          </div>
        ) : documents.length === 0 ? (
          <div className="rounded-xl bg-slate-50 p-5 text-center">
            <BookOpen className="mx-auto mb-2 h-8 w-8 text-slate-400" />
            <p className="font-medium text-slate-700">
              No processed documents found
            </p>
            <p className="mt-1 text-sm text-slate-500">
              Upload a PDF and wait for processing to complete before generating
              a quiz.
            </p>
          </div>
        ) : (
          <div className="max-h-64 space-y-2 overflow-y-auto">
            {documents.map((document) => (
              <label
                key={document.id}
                className={`flex cursor-pointer items-center gap-3 rounded-xl border p-3 transition ${
                  selectedDocuments.includes(document.id)
                    ? "border-violet-400 bg-violet-50"
                    : "border-slate-200 hover:border-violet-200"
                }`}
              >
                <input
                  type="checkbox"
                  checked={selectedDocuments.includes(document.id)}
                  onChange={() => toggleDocument(document.id)}
                  className="h-4 w-4 accent-violet-600"
                />

                <FileText className="h-5 w-5 shrink-0 text-violet-500" />

                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-slate-800">
                    {document.title || document.original_filename}
                  </p>
                  <p className="text-xs text-slate-500">
                    {document.page_count ?? 0} pages
                  </p>
                </div>

                <span className="text-xs font-medium text-green-600">
                  Processed
                </span>
              </label>
            ))}
          </div>
        )}

        <p className="mt-3 text-xs text-slate-500">
          {selectedDocuments.length} document(s) selected
        </p>
      </section>

      {/* DIFFICULTY */}
      <section className="rounded-2xl border border-slate-200 bg-white p-5">
        <h3 className="mb-4 font-semibold text-slate-900">
          2. Choose difficulty
        </h3>

        <div className="grid grid-cols-3 gap-3">
          {(["easy", "medium", "hard"] as QuizDifficulty[]).map((level) => (
            <button
              key={level}
              type="button"
              onClick={() => setDifficulty(level)}
              className={`rounded-xl border p-3 text-sm font-medium capitalize transition ${
                difficulty === level
                  ? "border-violet-500 bg-violet-50 text-violet-700"
                  : "border-slate-200 text-slate-600 hover:border-violet-300"
              }`}
            >
              {level}
            </button>
          ))}
        </div>
      </section>

      {/* QUESTION COUNT */}
      <section className="rounded-2xl border border-slate-200 bg-white p-5">
        <h3 className="mb-4 font-semibold text-slate-900">
          3. Number of questions
        </h3>

        <div className="grid grid-cols-4 gap-3">
          {[5, 10, 15, 20].map((count) => (
            <button
              key={count}
              type="button"
              onClick={() => setNumberOfQuestions(count)}
              className={`rounded-xl border p-3 text-sm font-semibold transition ${
                numberOfQuestions === count
                  ? "border-violet-500 bg-violet-50 text-violet-700"
                  : "border-slate-200 text-slate-600 hover:border-violet-300"
              }`}
            >
              {count}
            </button>
          ))}
        </div>
      </section>

      {/* TIME LIMIT */}
      <section className="rounded-2xl border border-slate-200 bg-white p-5">
        <div className="mb-3 flex items-center gap-2">
          <Clock className="h-5 w-5 text-violet-600" />
          <h3 className="font-semibold text-slate-900">4. Time limit</h3>
        </div>

        <select
          value={timeLimit}
          onChange={(event) => setTimeLimit(Number(event.target.value))}
          className="w-full rounded-xl border border-slate-200 bg-white p-3 text-sm outline-none focus:border-violet-500"
        >
          <option value={5}>5 minutes</option>
          <option value={10}>10 minutes</option>
          <option value={15}>15 minutes</option>
          <option value={20}>20 minutes</option>
          <option value={30}>30 minutes</option>
          <option value={45}>45 minutes</option>
          <option value={60}>60 minutes</option>
        </select>
      </section>

      {/* PASSING SCORE */}
      <section className="rounded-2xl border border-slate-200 bg-white p-5">
        <div className="mb-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Target className="h-5 w-5 text-violet-600" />
            <h3 className="font-semibold text-slate-900">5. Passing score</h3>
          </div>

          <span className="font-semibold text-violet-700">{passingScore}%</span>
        </div>

        <input
          type="range"
          min="30"
          max="100"
          step="5"
          value={passingScore}
          onChange={(event) => setPassingScore(Number(event.target.value))}
          className="w-full accent-violet-600"
        />

        <div className="flex justify-between text-xs text-slate-400">
          <span>30%</span>
          <span>100%</span>
        </div>
      </section>

      {/* SUMMARY */}
      <section className="rounded-2xl border border-violet-100 bg-violet-50 p-5">
        <h3 className="mb-3 font-semibold text-slate-900">
          Quiz configuration
        </h3>

        <div className="grid grid-cols-2 gap-3 text-sm">
          <p className="text-slate-600">
            Questions:{" "}
            <strong className="text-slate-900">{numberOfQuestions}</strong>
          </p>
          <p className="text-slate-600">
            Difficulty:{" "}
            <strong className="capitalize text-slate-900">{difficulty}</strong>
          </p>
          <p className="text-slate-600">
            Duration:{" "}
            <strong className="text-slate-900">{timeLimit} min</strong>
          </p>
          <p className="text-slate-600">
            Passing: <strong className="text-slate-900">{passingScore}%</strong>
          </p>
        </div>
      </section>

      {/* GENERATE */}
      <button
        type="button"
        onClick={handleGenerate}
        disabled={
          generating ||
          loadingDocuments ||
          documents.length === 0 ||
          selectedDocuments.length === 0
        }
        className="flex w-full items-center justify-center gap-2 rounded-xl bg-violet-600 px-5 py-3.5 font-semibold text-white transition hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {generating ? (
          <>
            <Loader2 className="h-5 w-5 animate-spin" />
            Generating quiz...
          </>
        ) : (
          <>
            <Sparkles className="h-5 w-5" />
            Generate AI Quiz
          </>
        )}
      </button>
    </div>
  );
};

export default QuizGeneratorForm;
