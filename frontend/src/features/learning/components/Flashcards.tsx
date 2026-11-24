import { useEffect, useMemo, useState } from "react";

import {
  Layers,
  Sparkles,
  RotateCw,
  CheckCircle2,
  CircleHelp,
  FileDown,
  Search,
  RefreshCw,
  Loader2,
  FileText,
  BookOpen,
  Trash2,
} from "lucide-react";

import learningApi from "../../../services/api/learning.api";
import documentsApi from "../../../services/api/documents.api";

import type { Document } from "../../../services/api/documents.api";

import type { Flashcard, QuizDifficulty } from "../types/learning.types";

type ExportFormat = "cards" | "revision";

const Flashcards = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [flashcards, setFlashcards] = useState<Flashcard[]>([]);

  const [selectedDocumentIds, setSelectedDocumentIds] = useState<number[]>([]);
  const [numberOfCards, setNumberOfCards] = useState(10);
  const [difficulty, setDifficulty] = useState<QuizDifficulty>("medium");

  const [filterDifficulty, setFilterDifficulty] = useState("all");
  const [filterMastered, setFilterMastered] = useState("all");
  const [search, setSearch] = useState("");

  const [flippedCards, setFlippedCards] = useState<Set<number>>(new Set());

  const [loadingDocuments, setLoadingDocuments] = useState(true);
  const [loadingCards, setLoadingCards] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [reviewingId, setReviewingId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // ----------------------------------------------------------
  // LOAD DOCUMENTS
  // ----------------------------------------------------------

  const loadDocuments = async () => {
    try {
      setLoadingDocuments(true);

      const response = await documentsApi.getAll({
        page: 1,
        per_page: 100,
      });

      setDocuments(response.data.documents || []);
    } catch (err) {
      console.error("Failed to load documents:", err);
      setError("Unable to load your documents.");
    } finally {
      setLoadingDocuments(false);
    }
  };

  // ----------------------------------------------------------
  // LOAD FLASHCARDS
  // ----------------------------------------------------------

  const loadFlashcards = async () => {
    try {
      setLoadingCards(true);

      const response = await learningApi.getFlashcards();

      setFlashcards(response.data.flashcards || []);
    } catch (err) {
      console.error("Failed to load flashcards:", err);
      setError("Unable to load flashcards.");
    } finally {
      setLoadingCards(false);
    }
  };

  useEffect(() => {
    void loadDocuments();
    void loadFlashcards();
  }, []);

  // ----------------------------------------------------------
  // GENERATE FLASHCARDS
  // ----------------------------------------------------------

  const handleGenerate = async () => {
    setError("");
    setSuccess("");

    if (selectedDocumentIds.length === 0) {
      setError("Please select at least one PDF document.");
      return;
    }

    try {
      setGenerating(true);

      const response = await learningApi.generateFlashcards({
        document_ids: selectedDocumentIds,
        number_of_cards: numberOfCards,
        difficulty,
      });

      const generatedCards = response.data.flashcards || [];

      setSuccess(`Successfully generated ${generatedCards.length} flashcards!`);

      await loadFlashcards();
    } catch (err: any) {
      console.error("Flashcard generation failed:", err);

      setError(
        err.response?.data?.message ||
          err.message ||
          "Failed to generate flashcards. Please try again.",
      );
    } finally {
      setGenerating(false);
    }
  };

  // ----------------------------------------------------------
  // REVIEW FLASHCARD
  // ----------------------------------------------------------

  const handleReview = async (flashcardId: number, mastered: boolean) => {
    try {
      setReviewingId(flashcardId);
      setError("");
      setSuccess("");

      const response = await learningApi.reviewFlashcard(flashcardId, {
        mastered,
      });

      const updatedFlashcard = response.data.flashcard;

      setFlashcards((previous) =>
        previous.map((card) =>
          card.id === flashcardId ? updatedFlashcard : card,
        ),
      );

      setSuccess(
        mastered
          ? "Flashcard marked as mastered."
          : "Flashcard marked for review.",
      );
    } catch (err: any) {
      console.error("Flashcard review failed:", err);

      setError(
        err.response?.data?.message || "Unable to update flashcard progress.",
      );
    } finally {
      setReviewingId(null);
    }
  };

  // ----------------------------------------------------------
  // DELETE FLASHCARD
  // ----------------------------------------------------------

  const handleDelete = async (flashcardId: number) => {
    const confirmed = window.confirm(
      "Are you sure you want to permanently delete this flashcard? This action cannot be undone.",
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeletingId(flashcardId);
      setError("");
      setSuccess("");

      await learningApi.deleteFlashcard(flashcardId);

      setFlashcards((previous) =>
        previous.filter((card) => card.id !== flashcardId),
      );

      setFlippedCards((previous) => {
        const next = new Set(previous);
        next.delete(flashcardId);
        return next;
      });

      setSuccess("Flashcard deleted successfully.");
    } catch (err: any) {
      console.error("Flashcard deletion failed:", err);

      setError(
        err.response?.data?.message ||
          "Unable to delete flashcard. Please try again.",
      );
    } finally {
      setDeletingId(null);
    }
  };

  // ----------------------------------------------------------
  // FLIP CARD
  // ----------------------------------------------------------

  const toggleFlip = (id: number) => {
    setFlippedCards((previous) => {
      const next = new Set(previous);

      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }

      return next;
    });
  };

  // ----------------------------------------------------------
  // FILTER FLASHCARDS
  // ----------------------------------------------------------

  const filteredFlashcards = useMemo(() => {
    return flashcards.filter((card) => {
      const matchesDifficulty =
        filterDifficulty === "all" || card.difficulty === filterDifficulty;

      const matchesMastery =
        filterMastered === "all" ||
        (filterMastered === "mastered" && card.is_mastered) ||
        (filterMastered === "review" && !card.is_mastered);

      const searchText = search.toLowerCase();

      const matchesSearch =
        card.question.toLowerCase().includes(searchText) ||
        card.answer.toLowerCase().includes(searchText);

      return matchesDifficulty && matchesMastery && matchesSearch;
    });
  }, [flashcards, filterDifficulty, filterMastered, search]);

  const masteredCount = flashcards.filter((card) => card.is_mastered).length;

  const reviewCount = flashcards.length - masteredCount;

  // ----------------------------------------------------------
  // PDF EXPORT
  // ----------------------------------------------------------

  const escapeHtml = (value: string) => {
    return value.replace(/[&<>"']/g, (character) => {
      const entities: Record<string, string> = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      };

      return entities[character];
    });
  };

  const handleExportPDF = (format: ExportFormat) => {
    if (filteredFlashcards.length === 0) {
      setError("There are no flashcards available to export.");
      return;
    }

    const printWindow = window.open("", "_blank");

    if (!printWindow) {
      setError("Please allow pop-ups to download your PDF.");
      return;
    }

    const cardsHTML = filteredFlashcards
      .map((card, index) => {
        const question = escapeHtml(card.question);
        const answer = escapeHtml(card.answer);
        const explanation = escapeHtml(card.explanation || "");
        const difficultyLabel = escapeHtml(card.difficulty);

        if (format === "cards") {
          return `
            <article class="card">
              <div class="card-number">FLASHCARD ${index + 1}</div>

              <div class="front">
                <span class="side-label">QUESTION</span>
                <h2>${question}</h2>
              </div>

              <div class="back">
                <span class="side-label">ANSWER</span>
                <p>${answer}</p>
                ${
                  explanation ? `<p class="explanation">${explanation}</p>` : ""
                }
              </div>

              <div class="meta">
                Difficulty: ${difficultyLabel}
                ${card.is_mastered ? "| Mastered" : "| Needs Review"}
              </div>
            </article>
          `;
        }

        return `
          <article class="revision-card">
            <div class="revision-heading">
              <span>Question ${index + 1}</span>
              <span>${difficultyLabel}</span>
            </div>

            <h3>${question}</h3>

            <div class="answer">
              <strong>Answer:</strong>
              <p>${answer}</p>
              ${explanation ? `<p class="explanation">${explanation}</p>` : ""}
            </div>
          </article>
        `;
      })
      .join("");

    const title =
      format === "cards" ? "Printable Flashcards" : "Flashcard Revision Sheet";

    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>${title} - FLIPBOOK-AI</title>
          <meta charset="UTF-8" />

          <style>
            * {
              box-sizing: border-box;
            }

            body {
              font-family: Arial, sans-serif;
              color: #1e293b;
              margin: 28px;
            }

            header {
              border-bottom: 2px solid #7c3aed;
              padding-bottom: 16px;
              margin-bottom: 24px;
            }

            header h1 {
              margin: 0 0 8px;
              color: #5b21b6;
            }

            header p {
              color: #64748b;
              font-size: 12px;
            }

            .card {
              border: 1px solid #cbd5e1;
              border-radius: 12px;
              padding: 20px;
              margin-bottom: 20px;
              page-break-inside: avoid;
            }

            .card-number {
              color: #7c3aed;
              font-weight: bold;
              font-size: 11px;
              margin-bottom: 14px;
            }

            .front, .back {
              padding: 14px;
              border-radius: 8px;
              margin-bottom: 10px;
              background: #f8fafc;
            }

            .side-label {
              font-size: 10px;
              font-weight: bold;
              color: #7c3aed;
            }

            .front h2 {
              font-size: 17px;
              margin-bottom: 4px;
            }

            .back p {
              font-size: 14px;
              line-height: 1.6;
            }

            .explanation {
              color: #64748b;
              font-size: 12px !important;
            }

            .meta {
              color: #64748b;
              font-size: 10px;
            }

            .revision-card {
              border-bottom: 1px solid #cbd5e1;
              padding: 16px 0;
              page-break-inside: avoid;
            }

            .revision-heading {
              display: flex;
              justify-content: space-between;
              color: #7c3aed;
              font-size: 11px;
              font-weight: bold;
            }

            .revision-card h3 {
              font-size: 16px;
            }

            .answer {
              background: #f8fafc;
              padding: 12px;
              border-radius: 8px;
              line-height: 1.6;
            }

            footer {
              margin-top: 28px;
              font-size: 10px;
              color: #94a3b8;
              text-align: center;
            }

            @media print {
              body {
                margin: 12mm;
              }

              .card, .revision-card {
                break-inside: avoid;
              }
            }
          </style>
        </head>

        <body>
          <header>
            <h1>FLIPBOOK-AI</h1>
            <h2>${title}</h2>

            <p>
              Generated on ${new Date().toLocaleDateString()}
              | Total cards: ${filteredFlashcards.length}
            </p>
          </header>

          ${cardsHTML}

          <footer>
            Generated with FLIPBOOK-AI Learning Studio
          </footer>

          <script>
            window.onload = function() {
              window.print();
            };
          </script>
        </body>
      </html>
    `);

    printWindow.document.close();
    setError("");
  };

  // ----------------------------------------------------------
  // UI
  // ----------------------------------------------------------

  return (
    <div className="space-y-6">
      {/* HEADER */}

      <div className="rounded-2xl border border-violet-100 bg-gradient-to-r from-violet-50 to-indigo-50 p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-violet-100 p-3">
              <Layers className="h-7 w-7 text-violet-700" />
            </div>

            <div>
              <h2 className="text-xl font-bold text-slate-900">
                AI Flashcards
              </h2>

              <p className="text-sm text-slate-600">
                Turn your PDFs into interactive learning cards.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => {
              void loadFlashcards();
              void loadDocuments();
            }}
            disabled={loadingCards || loadingDocuments}
            className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium hover:bg-slate-50 disabled:opacity-50"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* NOTIFICATIONS */}

      {error && (
        <div
          role="alert"
          className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"
        >
          {error}
        </div>
      )}

      {success && (
        <div
          role="status"
          className="rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-700"
        >
          {success}
        </div>
      )}

      {/* GENERATOR */}

      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm md:p-6">
        <div className="mb-5 flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-violet-600" />

          <h3 className="text-lg font-semibold text-slate-900">
            Generate Flashcards
          </h3>
        </div>

        <div className="grid gap-5 md:grid-cols-3">
          {/* DOCUMENT SELECT */}

          <div className="md:col-span-3">
            <label
              htmlFor="flashcard-documents"
              className="mb-2 block text-sm font-medium text-slate-700"
            >
              Select PDF documents
            </label>

            {loadingDocuments ? (
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
                Loading your processed PDFs...
              </div>
            ) : (
              <div
                id="flashcard-documents"
                className="overflow-hidden rounded-xl border border-slate-200 bg-white"
              >
                {documents
                  .filter((document) =>
                    ["completed", "processed"].includes(
                      document.processing_status?.toLowerCase(),
                    ),
                  )
                  .map((document) => {
                    const isSelected = selectedDocumentIds.includes(
                      document.id,
                    );
                    const fileName =
                      document.title ||
                      document.original_filename ||
                      `Document ${document.id}`;

                    return (
                      <label
                        key={document.id}
                        className={`flex cursor-pointer items-center gap-3 border-b border-slate-100 px-4 py-3 transition last:border-b-0 ${
                          isSelected
                            ? "bg-violet-50"
                            : "bg-white hover:bg-slate-50"
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => {
                            setSelectedDocumentIds((previous) =>
                              isSelected
                                ? previous.filter((id) => id !== document.id)
                                : [...previous, document.id],
                            );
                          }}
                          className="h-4 w-4 rounded border-slate-300 text-violet-600 accent-violet-600 focus:ring-violet-500"
                        />

                        <span
                          className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${
                            isSelected
                              ? "bg-violet-100 text-violet-700"
                              : "bg-slate-100 text-slate-500"
                          }`}
                        >
                          <FileText className="h-5 w-5" />
                        </span>

                        <span className="min-w-0 flex-1">
                          <span className="block truncate text-sm font-medium text-slate-800">
                            {fileName}
                          </span>
                          <span className="mt-0.5 block text-xs text-slate-500">
                            Processed PDF
                          </span>
                        </span>

                        {isSelected && (
                          <span className="text-xs font-semibold text-violet-700">
                            Selected
                          </span>
                        )}
                      </label>
                    );
                  })}

                {documents.filter((document) =>
                  ["completed", "processed"].includes(
                    document.processing_status?.toLowerCase(),
                  ),
                ).length === 0 && (
                  <p className="p-4 text-sm text-amber-600">
                    No processed PDF documents found. Upload and process a PDF
                    first.
                  </p>
                )}
              </div>
            )}

            <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
              <p className="text-xs text-slate-500">
                Select one or more processed PDF documents.
              </p>
              <p className="text-xs font-medium text-violet-700">
                {selectedDocumentIds.length} selected
              </p>
            </div>
          </div>

          {/* CARD COUNT */}

          <div>
            <label
              htmlFor="flashcard-count"
              className="mb-2 block text-sm font-medium text-slate-700"
            >
              Number of flashcards
            </label>

            <select
              id="flashcard-count"
              value={numberOfCards}
              onChange={(event) => setNumberOfCards(Number(event.target.value))}
              className="w-full rounded-xl border border-slate-300 p-3 text-sm outline-none focus:border-violet-500"
            >
              {[5, 10, 15, 20, 25, 30].map((count) => (
                <option key={count} value={count}>
                  {count} cards
                </option>
              ))}
            </select>
          </div>

          {/* DIFFICULTY */}

          <div>
            <label
              htmlFor="flashcard-difficulty"
              className="mb-2 block text-sm font-medium text-slate-700"
            >
              Difficulty
            </label>

            <select
              id="flashcard-difficulty"
              value={difficulty}
              onChange={(event) =>
                setDifficulty(event.target.value as QuizDifficulty)
              }
              className="w-full rounded-xl border border-slate-300 p-3 text-sm outline-none focus:border-violet-500"
            >
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </div>

          {/* GENERATE BUTTON */}

          <div className="flex items-end">
            <button
              type="button"
              onClick={handleGenerate}
              disabled={generating || loadingDocuments}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-violet-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {generating ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  Generate with AI
                </>
              )}
            </button>
          </div>
        </div>
      </section>

      {/* STATISTICS */}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <p className="text-sm text-slate-500">Total Flashcards</p>

          <p className="mt-2 text-2xl font-bold text-slate-900">
            {flashcards.length}
          </p>
        </div>

        <div className="rounded-xl border border-green-200 bg-green-50 p-5">
          <p className="text-sm text-green-700">Mastered</p>

          <p className="mt-2 text-2xl font-bold text-green-800">
            {masteredCount}
          </p>
        </div>

        <div className="rounded-xl border border-amber-200 bg-amber-50 p-5">
          <p className="text-sm text-amber-700">Needs Review</p>

          <p className="mt-2 text-2xl font-bold text-amber-800">
            {reviewCount}
          </p>
        </div>
      </div>

      {/* FLASHCARD LIST */}

      <section className="space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-lg font-semibold text-slate-900">
              My Flashcards
            </h3>

            <p className="text-sm text-slate-500">
              Click any card to reveal its answer.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => handleExportPDF("cards")}
              disabled={filteredFlashcards.length === 0}
              className="flex items-center gap-2 rounded-lg border border-violet-200 bg-white px-3 py-2 text-sm font-medium text-violet-700 hover:bg-violet-50 disabled:opacity-50"
            >
              <FileDown className="h-4 w-4" />
              Printable Cards
            </button>

            <button
              type="button"
              onClick={() => handleExportPDF("revision")}
              disabled={filteredFlashcards.length === 0}
              className="flex items-center gap-2 rounded-lg bg-violet-600 px-3 py-2 text-sm font-medium text-white hover:bg-violet-700 disabled:opacity-50"
            >
              <FileText className="h-4 w-4" />
              Revision PDF
            </button>
          </div>
        </div>

        {/* FILTERS */}

        <div className="grid gap-3 sm:grid-cols-3">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />

            <input
              type="text"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search flashcards..."
              aria-label="Search flashcards"
              className="w-full rounded-xl border border-slate-300 py-2.5 pl-9 pr-3 text-sm outline-none focus:border-violet-500"
            />
          </div>

          <select
            value={filterDifficulty}
            onChange={(event) => setFilterDifficulty(event.target.value)}
            aria-label="Filter by difficulty"
            className="rounded-xl border border-slate-300 px-3 py-2.5 text-sm"
          >
            <option value="all">All difficulties</option>
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>

          <select
            value={filterMastered}
            onChange={(event) => setFilterMastered(event.target.value)}
            aria-label="Filter by mastery"
            className="rounded-xl border border-slate-300 px-3 py-2.5 text-sm"
          >
            <option value="all">All flashcards</option>
            <option value="mastered">Mastered</option>
            <option value="review">Needs Review</option>
          </select>
        </div>

        {/* LOADING */}

        {loadingCards ? (
          <div className="flex justify-center rounded-xl border border-slate-200 bg-white p-12">
            <Loader2 className="h-7 w-7 animate-spin text-violet-600" />
          </div>
        ) : filteredFlashcards.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
            <BookOpen className="mx-auto mb-3 h-10 w-10 text-slate-400" />

            <h4 className="font-semibold text-slate-800">
              No flashcards found
            </h4>

            <p className="mt-2 text-sm text-slate-500">
              Generate flashcards from your processed PDFs to start learning.
            </p>
          </div>
        ) : (
          /* FLASHCARD GRID */

          <div className="grid gap-5 md:grid-cols-2">
            {filteredFlashcards.map((card) => {
              const isFlipped = flippedCards.has(card.id);
              const isReviewing = reviewingId === card.id;
              const isDeleting = deletingId === card.id;
              const isBusy = isReviewing || isDeleting;

              return (
                <div
                  key={card.id}
                  className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"
                >
                  {/* CLICK TO FLIP */}

                  <button
                    type="button"
                    onClick={() => toggleFlip(card.id)}
                    aria-label={
                      isFlipped
                        ? "Show flashcard question"
                        : "Reveal flashcard answer"
                    }
                    className="flex min-h-56 w-full flex-col items-center justify-center bg-gradient-to-br from-violet-50 to-indigo-50 p-6 text-center transition hover:from-violet-100 hover:to-indigo-100"
                  >
                    <div className="mb-4 flex w-full items-center justify-between">
                      <span className="rounded-full bg-white px-3 py-1 text-xs font-medium capitalize text-violet-700">
                        {card.difficulty}
                      </span>

                      {card.is_mastered ? (
                        <span className="flex items-center gap-1 text-xs text-green-700">
                          <CheckCircle2 className="h-4 w-4" />
                          Mastered
                        </span>
                      ) : (
                        <span className="text-xs text-amber-700">
                          Needs Review
                        </span>
                      )}
                    </div>

                    <span className="mb-3 text-xs font-semibold uppercase tracking-wider text-violet-600">
                      {isFlipped ? "Answer" : "Question"}
                    </span>

                    <p className="text-lg font-semibold leading-7 text-slate-900">
                      {isFlipped ? card.answer : card.question}
                    </p>

                    {isFlipped && card.explanation && (
                      <p className="mt-4 text-sm leading-6 text-slate-600">
                        {card.explanation}
                      </p>
                    )}

                    <span className="mt-5 flex items-center gap-2 text-xs text-violet-600">
                      <RotateCw className="h-3.5 w-3.5" />
                      Click to {isFlipped ? "see question" : "reveal answer"}
                    </span>
                  </button>

                  {/* ACTIONS */}

                  <div className="flex flex-wrap items-center justify-between gap-3 p-4">
                    <span className="text-xs text-slate-500">
                      Reviewed {card.review_count} times
                    </span>

                    <div className="flex flex-wrap gap-2">
                      {/* REVIEW AGAIN */}

                      <button
                        type="button"
                        disabled={isBusy}
                        onClick={() => handleReview(card.id, false)}
                        className="flex items-center gap-1 rounded-lg border border-amber-200 px-3 py-2 text-xs font-medium text-amber-700 hover:bg-amber-50 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        <CircleHelp className="h-3.5 w-3.5" />
                        Review Again
                      </button>

                      {/* MASTERED */}

                      <button
                        type="button"
                        disabled={isBusy}
                        onClick={() => handleReview(card.id, true)}
                        className="flex items-center gap-1 rounded-lg bg-green-600 px-3 py-2 text-xs font-medium text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {isReviewing ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                          <CheckCircle2 className="h-3.5 w-3.5" />
                        )}
                        Mastered
                      </button>

                      {/* DELETE */}

                      <button
                        type="button"
                        disabled={isBusy}
                        onClick={() => handleDelete(card.id)}
                        className="flex items-center gap-1 rounded-lg border border-red-200 px-3 py-2 text-xs font-medium text-red-600 transition hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {isDeleting ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                          <Trash2 className="h-3.5 w-3.5" />
                        )}

                        {isDeleting ? "Deleting..." : "Delete"}
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
};

export default Flashcards;
