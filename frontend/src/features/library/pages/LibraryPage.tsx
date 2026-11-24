import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  Search,
  FileText,
  Star,
  Trash2,
  RefreshCw,
  FolderOpen,
  FileUp,
  X,
  AlertCircle,
  CheckCircle2,
  Clock,
  LoaderCircle,
  BookOpen,
} from "lucide-react";

import DocumentUpload from "../components/DocumentUpload";

import {
  documentsApi,
  type Document,
} from "../../../services/api/documents.api";

type FilterType = "all" | "favorites";

// =====================================================
// HELPERS
// =====================================================

const formatFileSize = (bytes: number): string => {
  if (!bytes || bytes < 0) return "0 B";

  const units = ["B", "KB", "MB", "GB"];

  const index = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1,
  );

  return `${(bytes / Math.pow(1024, index)).toFixed(
    index === 0 ? 0 : 1,
  )} ${units[index]}`;
};

const formatDate = (date: string): string => {
  const parsedDate = new Date(date);

  if (Number.isNaN(parsedDate.getTime())) {
    return "Unknown date";
  }

  return parsedDate.toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
};

const getStatus = (status: string) => {
  const normalized = status?.toLowerCase() || "unknown";

  if (["completed", "processed", "success"].includes(normalized)) {
    return {
      label: "Processed",
      icon: CheckCircle2,
      className: "bg-emerald-50 text-emerald-700",
    };
  }

  if (["processing", "pending", "queued"].includes(normalized)) {
    return {
      label: normalized === "processing" ? "Processing" : "Pending",
      icon: Clock,
      className: "bg-amber-50 text-amber-700",
    };
  }

  if (["failed", "error"].includes(normalized)) {
    return {
      label: "Failed",
      icon: AlertCircle,
      className: "bg-red-50 text-red-700",
    };
  }

  return {
    label: status || "Not processed",
    icon: FileText,
    className: "bg-gray-100 text-gray-600",
  };
};

// =====================================================
// LIBRARY PAGE
// =====================================================

export default function LibraryPage() {
  const navigate = useNavigate();

  // -----------------------------------------------------
  // STATE
  // -----------------------------------------------------

  const [documents, setDocuments] = useState<Document[]>([]);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<FilterType>("all");

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const [refreshKey, setRefreshKey] = useState(0);

  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [updatingId, setUpdatingId] = useState<number | null>(null);

  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingTitle, setEditingTitle] = useState("");

  // -----------------------------------------------------
  // LOAD DOCUMENTS
  // -----------------------------------------------------

  const loadDocuments = useCallback(async () => {
    setIsLoading(true);
    setError("");

    try {
      const response = await documentsApi.getAll({
        page,
        per_page: 12,
        favorite: filter === "favorites" ? true : undefined,
      });

      setDocuments(response.data.documents);
      setTotalPages(response.data.pagination.pages || 1);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load your documents. Please try again.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [page, filter]);

  useEffect(() => {
    void loadDocuments();
  }, [loadDocuments, refreshKey]);

  // -----------------------------------------------------
  // UPLOAD SUCCESS
  // -----------------------------------------------------

  const handleUploadSuccess = () => {
    setPage(1);
    setRefreshKey((current) => current + 1);
  };

  // -----------------------------------------------------
  // OPEN PDF READER
  // -----------------------------------------------------

  const handleOpenReader = (document: Document) => {
    const status = document.processing_status?.toLowerCase() || "";

    if (!["completed", "processed", "success"].includes(status)) {
      setError("This PDF must finish processing before it can be opened.");
      return;
    }

    navigate(
      `/reader?id=${document.id}&title=${encodeURIComponent(document.title)}`,
    );
  };

  // -----------------------------------------------------
  // FAVORITES
  // -----------------------------------------------------

  const handleFavorite = async (document: Document) => {
    setUpdatingId(document.id);
    setError("");

    try {
      await documentsApi.update(document.id, {
        is_favorite: !document.is_favorite,
      });

      setDocuments((current) =>
        current.map((item) =>
          item.id === document.id
            ? { ...item, is_favorite: !item.is_favorite }
            : item,
        ),
      );

      if (filter === "favorites" && document.is_favorite) {
        setRefreshKey((current) => current + 1);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not update favorite status.",
      );
    } finally {
      setUpdatingId(null);
    }
  };

  // -----------------------------------------------------
  // DELETE DOCUMENT
  // -----------------------------------------------------

  const handleDelete = async (document: Document) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${document.title}"? This action cannot be undone.`,
    );

    if (!confirmed) return;

    setDeletingId(document.id);
    setError("");

    try {
      await documentsApi.delete(document.id);

      setDocuments((current) =>
        current.filter((item) => item.id !== document.id),
      );

      setRefreshKey((current) => current + 1);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not delete this document.",
      );
    } finally {
      setDeletingId(null);
    }
  };

  // -----------------------------------------------------
  // RENAME DOCUMENT
  // -----------------------------------------------------

  const startEditing = (document: Document) => {
    setEditingId(document.id);
    setEditingTitle(document.title);
  };

  const saveTitle = async (document: Document) => {
    const title = editingTitle.trim();

    if (!title) {
      setError("Document title cannot be empty.");
      return;
    }

    if (title === document.title) {
      setEditingId(null);
      return;
    }

    setUpdatingId(document.id);
    setError("");

    try {
      await documentsApi.update(document.id, { title });

      setDocuments((current) =>
        current.map((item) =>
          item.id === document.id ? { ...item, title } : item,
        ),
      );

      setEditingId(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not update document title.",
      );
    } finally {
      setUpdatingId(null);
    }
  };

  // -----------------------------------------------------
  // SEARCH FILTER
  // -----------------------------------------------------

  const filteredDocuments = documents.filter((document) => {
    const query = search.toLowerCase().trim();

    return (
      !query ||
      document.title.toLowerCase().includes(query) ||
      document.original_filename.toLowerCase().includes(query)
    );
  });

  // =====================================================
  // UI
  // =====================================================

  return (
    <div className="page-container space-y-8">
      {/* PAGE HEADING */}

      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <div className="mb-2 flex items-center gap-2 text-sm text-gray-500">
            <FolderOpen size={16} />
            <span>Workspace</span>
            <span>/</span>
            <span className="text-violet-600">My Library</span>
          </div>

          <h1 className="heading-1">My Library</h1>

          <p className="body-text mt-2">
            Manage, organize and access all your documents in one place.
          </p>
        </div>

        <button
          type="button"
          onClick={() => setRefreshKey((current) => current + 1)}
          disabled={isLoading}
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 transition hover:bg-gray-50 disabled:opacity-50"
        >
          <RefreshCw size={16} className={isLoading ? "animate-spin" : ""} />
          Refresh
        </button>
      </div>

      {/* UPLOAD SECTION */}

      <section className="rounded-2xl border border-violet-100 bg-white p-5 shadow-sm sm:p-6">
        <div className="mb-5 flex items-center gap-3">
          <div className="rounded-xl bg-violet-100 p-2.5 text-violet-700">
            <FileUp size={21} />
          </div>

          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              Upload a document
            </h2>

            <p className="text-sm text-gray-500">
              Add a PDF to your personal library.
            </p>
          </div>
        </div>

        <DocumentUpload onUploadSuccess={handleUploadSuccess} />
      </section>

      {/* LIBRARY TOOLBAR */}

      <section>
        <div className="mb-5 flex flex-col justify-between gap-4 lg:flex-row lg:items-center">
          <div>
            <h2 className="heading-2">Your documents</h2>

            <p className="caption-text mt-1">
              Search and manage your uploaded PDFs.
            </p>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row">
            {/* SEARCH */}

            <div className="relative min-w-0 sm:w-72">
              <Search
                size={18}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
              />

              <input
                type="search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search documents..."
                className="w-full rounded-xl border border-gray-200 bg-white py-2.5 pl-10 pr-4 text-sm outline-none transition focus:border-violet-400 focus:ring-2 focus:ring-violet-100"
              />
            </div>

            {/* FILTERS */}

            <div className="flex rounded-xl border border-gray-200 bg-white p-1">
              <button
                type="button"
                onClick={() => {
                  setFilter("all");
                  setPage(1);
                }}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
                  filter === "all"
                    ? "bg-violet-100 text-violet-700"
                    : "text-gray-500 hover:bg-gray-50"
                }`}
              >
                All files
              </button>

              <button
                type="button"
                onClick={() => {
                  setFilter("favorites");
                  setPage(1);
                }}
                className={`inline-flex items-center gap-1.5 rounded-lg px-4 py-2 text-sm font-medium transition ${
                  filter === "favorites"
                    ? "bg-violet-100 text-violet-700"
                    : "text-gray-500 hover:bg-gray-50"
                }`}
              >
                <Star size={14} />
                Favorites
              </button>
            </div>
          </div>
        </div>

        {/* ERROR MESSAGE */}

        {error && (
          <div
            role="alert"
            className="mb-5 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700"
          >
            <AlertCircle size={18} className="mt-0.5 shrink-0" />

            <span className="flex-1">{error}</span>

            <button
              type="button"
              onClick={() => setError("")}
              aria-label="Dismiss error"
            >
              <X size={17} />
            </button>
          </div>
        )}

        {/* LOADING AND DOCUMENT GRID */}

        {isLoading ? (
          <div className="flex min-h-64 flex-col items-center justify-center gap-3 rounded-2xl border border-gray-100 bg-white">
            <LoaderCircle size={30} className="animate-spin text-violet-600" />

            <p className="text-sm text-gray-500">Loading your library...</p>
          </div>
        ) : filteredDocuments.length === 0 ? (
          /* EMPTY STATE */

          <div className="flex min-h-72 flex-col items-center justify-center rounded-2xl border border-dashed border-gray-300 bg-white px-6 text-center">
            <div className="mb-4 rounded-2xl bg-violet-50 p-4 text-violet-600">
              {search ? <Search size={30} /> : <FileText size={30} />}
            </div>

            <h3 className="text-lg font-semibold text-gray-900">
              {search
                ? "No matching documents"
                : filter === "favorites"
                  ? "No favorite documents yet"
                  : "Your library is empty"}
            </h3>

            <p className="mt-2 max-w-md text-sm text-gray-500">
              {search
                ? "Try another search term."
                : filter === "favorites"
                  ? "Mark documents with a star to find them here."
                  : "Upload your first PDF above to start building your library."}
            </p>
          </div>
        ) : (
          /* DOCUMENT GRID */

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {filteredDocuments.map((document) => {
              const status = getStatus(document.processing_status);
              const StatusIcon = status.icon;

              const isProcessed = [
                "completed",
                "processed",
                "success",
              ].includes(document.processing_status?.toLowerCase() || "");

              return (
                <article
                  key={document.id}
                  className="group rounded-2xl border border-gray-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-violet-200 hover:shadow-md"
                >
                  {/* CARD HEADER */}

                  <div className="mb-4 flex items-start justify-between">
                    <div className="rounded-xl bg-red-50 p-3 text-red-600">
                      <FileText size={25} />
                    </div>

                    <div className="flex items-center gap-1">
                      {/* FAVORITE */}

                      <button
                        type="button"
                        onClick={() => void handleFavorite(document)}
                        disabled={updatingId === document.id}
                        aria-label={
                          document.is_favorite
                            ? "Remove from favorites"
                            : "Add to favorites"
                        }
                        title="Toggle favorite"
                        className="rounded-lg p-2 text-gray-400 transition hover:bg-amber-50 hover:text-amber-500 disabled:opacity-50"
                      >
                        <Star
                          size={18}
                          fill={document.is_favorite ? "currentColor" : "none"}
                          className={
                            document.is_favorite ? "text-amber-500" : ""
                          }
                        />
                      </button>

                      {/* DELETE */}

                      <button
                        type="button"
                        onClick={() => void handleDelete(document)}
                        disabled={deletingId === document.id}
                        aria-label="Delete document"
                        title="Delete document"
                        className="rounded-lg p-2 text-gray-400 transition hover:bg-red-50 hover:text-red-600 disabled:opacity-50"
                      >
                        {deletingId === document.id ? (
                          <LoaderCircle size={18} className="animate-spin" />
                        ) : (
                          <Trash2 size={18} />
                        )}
                      </button>
                    </div>
                  </div>

                  {/* DOCUMENT TITLE */}

                  {editingId === document.id ? (
                    <div className="mb-3 flex gap-2">
                      <input
                        autoFocus
                        value={editingTitle}
                        onChange={(event) =>
                          setEditingTitle(event.target.value)
                        }
                        onKeyDown={(event) => {
                          if (event.key === "Enter") {
                            void saveTitle(document);
                          }

                          if (event.key === "Escape") {
                            setEditingId(null);
                          }
                        }}
                        className="min-w-0 flex-1 rounded-lg border border-violet-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-violet-100"
                      />

                      <button
                        type="button"
                        onClick={() => void saveTitle(document)}
                        disabled={updatingId === document.id}
                        className="rounded-lg bg-violet-600 px-3 py-2 text-xs font-semibold text-white hover:bg-violet-700 disabled:opacity-50"
                      >
                        Save
                      </button>
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={() => startEditing(document)}
                      title="Click to rename"
                      className="mb-1 block max-w-full truncate text-left text-base font-semibold text-gray-900 hover:text-violet-700"
                    >
                      {document.title}
                    </button>
                  )}

                  {/* FILE NAME */}

                  <p className="mb-4 truncate text-xs text-gray-400">
                    {document.original_filename}
                  </p>

                  {/* STATUS AND PAGE COUNT */}

                  <div className="mb-4 flex flex-wrap items-center gap-2">
                    <span
                      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${status.className}`}
                    >
                      <StatusIcon size={13} />
                      {status.label}
                    </span>

                    {document.page_count != null && (
                      <span className="rounded-full bg-gray-100 px-2.5 py-1 text-xs text-gray-600">
                        {document.page_count} pages
                      </span>
                    )}
                  </div>

                  {/* FILE INFORMATION */}

                  <div className="flex items-center justify-between border-t border-gray-100 pt-4 text-xs text-gray-500">
                    <span>{formatFileSize(document.file_size)}</span>
                    <span>{formatDate(document.created_at)}</span>
                  </div>

                  {/* OPEN READER BUTTON */}

                  <div className="mt-4">
                    <button
                      type="button"
                      onClick={() => handleOpenReader(document)}
                      disabled={!isProcessed}
                      title={
                        isProcessed
                          ? "Open this PDF in Reader"
                          : "Available after PDF processing completes"
                      }
                      className="flex w-full items-center justify-center gap-2 rounded-xl bg-violet-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      <BookOpen size={17} />
                      Open Reader
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        )}

        {/* PAGINATION */}

        {!isLoading && totalPages > 1 && (
          <div className="mt-6 flex items-center justify-between">
            <p className="text-sm text-gray-500">
              Page {page} of {totalPages}
            </p>

            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setPage((current) => Math.max(1, current - 1))}
                disabled={page <= 1}
                className="rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Previous
              </button>

              <button
                type="button"
                onClick={() =>
                  setPage((current) => Math.min(totalPages, current + 1))
                }
                disabled={page >= totalPages}
                className="rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
