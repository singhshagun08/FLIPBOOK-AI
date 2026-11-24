import { useEffect, useState } from "react";

import {
  MessageSquareText,
  Send,
  FileText,
  Plus,
  Loader2,
  AlertCircle,
  Sparkles,
  History,
  RefreshCw,
  Search,
  Trash2,
  ChevronLeft,
  ChevronRight,
  X,
  Download,
} from "lucide-react";

import { jsPDF } from "jspdf";

import documentsApi, { type Document } from "../../services/api/documents.api";

import chatApi, {
  type ChatMessage,
  type ChatSession,
  type ChatSource,
  type Pagination,
} from "../../services/api/chat.api";

import { getApiErrorMessage } from "../../services/api/client";

const PAGE_SIZE = 10;

const EMPTY_PAGINATION: Pagination = {
  page: 1,
  per_page: PAGE_SIZE,
  total: 0,
  pages: 0,
  has_next: false,
  has_previous: false,
};

export default function AssistantPage() {
  // =====================================================
  // DOCUMENT STATE
  // =====================================================

  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<number[]>([]);

  // =====================================================
  // CHAT STATE
  // =====================================================

  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  // =====================================================
  // SEARCH AND PAGINATION STATE
  // =====================================================

  const [searchInput, setSearchInput] = useState("");
  const [activeSearch, setActiveSearch] = useState("");
  const [pagination, setPagination] = useState<Pagination>(EMPTY_PAGINATION);

  // =====================================================
  // INPUT STATE
  // =====================================================

  const [question, setQuestion] = useState("");

  // =====================================================
  // LOADING STATE
  // =====================================================

  const [loadingDocuments, setLoadingDocuments] = useState(true);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [loadingSession, setLoadingSession] = useState(false);
  const [sending, setSending] = useState(false);
  const [deletingSessionId, setDeletingSessionId] = useState<number | null>(
    null,
  );

  // =====================================================
  // ERROR STATE
  // =====================================================

  const [error, setError] = useState("");

  // =====================================================
  // INITIAL LOAD
  // =====================================================

  useEffect(() => {
    void loadDocuments();
    void loadChatHistory(1, "");
  }, []);

  // =====================================================
  // LOAD DOCUMENTS
  // =====================================================

  const loadDocuments = async () => {
    try {
      setLoadingDocuments(true);

      const response = await documentsApi.getAll({
        page: 1,
        per_page: 100,
      });

      setDocuments(response.data.documents || []);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoadingDocuments(false);
    }
  };

  // =====================================================
  // LOAD CHAT HISTORY
  // =====================================================

  const loadChatHistory = async (
    page = pagination.page,
    search = activeSearch,
  ) => {
    try {
      setLoadingHistory(true);

      const response = await chatApi.getSessions(
        page,
        PAGE_SIZE,
        false,
        search,
      );

      setSessions(response.sessions || []);
      setPagination(response.pagination || EMPTY_PAGINATION);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoadingHistory(false);
    }
  };

  // =====================================================
  // PROCESSED DOCUMENTS
  // =====================================================

  const readyDocuments = documents.filter(
    (document) => document.processing_status?.toLowerCase() === "completed",
  );

  // =====================================================
  // SELECT / DESELECT DOCUMENTS
  // =====================================================

  const toggleDocument = (documentId: number) => {
    if (sending || loadingSession) return;

    setSelectedDocumentIds((current) =>
      current.includes(documentId)
        ? current.filter((id) => id !== documentId)
        : [...current, documentId],
    );

    // Changing document selection starts a new conversation.
    setSessionId(null);
    setMessages([]);
    setQuestion("");
    setError("");
  };

  // =====================================================
  // START NEW CHAT
  // =====================================================

  const startNewChat = () => {
    if (sending || loadingSession) return;

    setSessionId(null);
    setMessages([]);
    setQuestion("");
    setError("");
  };

  // =====================================================
  // RESTORE PREVIOUS CONVERSATION
  // =====================================================

  const openPreviousChat = async (id: number) => {
    if (sending || loadingSession) return;

    try {
      setLoadingSession(true);
      setError("");

      const session = await chatApi.getSession(id);

      setSessionId(session.id);
      setMessages(session.messages || []);

      // Backend session.to_dict() returns document_ids.
      // Use that field to restore selected PDFs.
      setSelectedDocumentIds(session.document_ids || []);

      setQuestion("");
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoadingSession(false);
    }
  };

  // =====================================================
  // SEND MESSAGE
  // =====================================================

  const sendMessage = async () => {
    const trimmedQuestion = question.trim();

    if (!trimmedQuestion || sending || loadingSession) {
      return;
    }

    if (selectedDocumentIds.length === 0) {
      setError("Please select at least one processed PDF.");
      return;
    }

    try {
      setSending(true);
      setError("");

      let activeSessionId = sessionId;

      // Create a conversation if one is not active.
      if (!activeSessionId) {
        const session = await chatApi.createSession({
          title: trimmedQuestion.slice(0, 80),
          document_ids: selectedDocumentIds,
        });

        activeSessionId = session.id;
        setSessionId(session.id);
      }

      setQuestion("");

      // Backend expects question and optional top_k.
      const response = await chatApi.sendMessage(activeSessionId, {
        question: trimmedQuestion,
        top_k: 5,
      });

      // Backend returns user_message and assistant_message.
      setMessages((current) => [
        ...current,
        response.user_message,
        response.assistant_message,
      ]);

      // Refresh history after sending.
      await loadChatHistory(1, activeSearch);
    } catch (err) {
      setError(getApiErrorMessage(err));
      setQuestion(trimmedQuestion);
    } finally {
      setSending(false);
    }
  };

  // =====================================================
  // SEARCH CONVERSATIONS
  // =====================================================

  const handleSearch = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const search = searchInput.trim();

    setActiveSearch(search);
    await loadChatHistory(1, search);
  };

  // =====================================================
  // CLEAR SEARCH
  // =====================================================

  const clearSearch = async () => {
    setSearchInput("");
    setActiveSearch("");
    await loadChatHistory(1, "");
  };

  // =====================================================
  // PAGINATION
  // =====================================================

  const goToPreviousPage = async () => {
    if (!pagination.has_previous || loadingHistory) return;

    await loadChatHistory(pagination.page - 1, activeSearch);
  };

  const goToNextPage = async () => {
    if (!pagination.has_next || loadingHistory) return;

    await loadChatHistory(pagination.page + 1, activeSearch);
  };

  // =====================================================
  // DELETE CONVERSATION
  // =====================================================

  const deleteConversation = async (id: number) => {
    if (sending || deletingSessionId !== null) return;

    const confirmed = window.confirm(
      "Are you sure you want to delete this conversation? This action cannot be undone.",
    );

    if (!confirmed) return;

    try {
      setDeletingSessionId(id);
      setError("");

      await chatApi.deleteSession(id);

      // Clear the current chat if it was deleted.
      if (sessionId === id) {
        setSessionId(null);
        setMessages([]);
        setQuestion("");
      }

      // Refresh current page.
      const remainingSessions = sessions.filter((session) => session.id !== id);

      if (remainingSessions.length === 0 && pagination.page > 1) {
        await loadChatHistory(pagination.page - 1, activeSearch);
      } else {
        await loadChatHistory(pagination.page, activeSearch);
      }
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setDeletingSessionId(null);
    }
  };

  // =====================================================
  // EXPORT HELPERS
  // =====================================================

  const getExportFileName = () => {
    const activeSession = sessions.find((session) => session.id === sessionId);

    const title = activeSession?.title || "flipbook-ai-conversation";

    return (
      title
        .replace(/[^a-z0-9]/gi, "_")
        .replace(/_+/g, "_")
        .slice(0, 60) || "flipbook-ai-conversation"
    );
  };

  const formatMessageDate = (date?: string) => {
    if (!date) return "Date unavailable";

    const parsedDate = new Date(date);

    if (Number.isNaN(parsedDate.getTime())) {
      return "Date unavailable";
    }

    return parsedDate.toLocaleString();
  };

  // =====================================================
  // EXPORT MARKDOWN
  // =====================================================

  const exportMarkdown = () => {
    if (messages.length === 0) return;

    const activeSession = sessions.find((session) => session.id === sessionId);

    let markdown = `# ${activeSession?.title || "AI Assistant Conversation"}\n\n`;

    markdown += `Exported: ${new Date().toLocaleString()}\n\n`;
    markdown += `---\n\n`;

    messages.forEach((message) => {
      const role = message.role === "user" ? "You" : "AI Assistant";

      markdown += `## ${role}\n\n`;
      markdown += `${message.content}\n\n`;

      markdown += `*${formatMessageDate(message.created_at)}*\n\n`;

      if (
        message.role === "assistant" &&
        message.sources &&
        message.sources.length > 0
      ) {
        markdown += `### Sources\n\n`;

        message.sources.forEach((source) => {
          const title = source.document_title || source.filename || "Document";

          const page = source.page_number ?? source.page;

          markdown += `- ${title}`;

          if (typeof page === "number") {
            markdown += `, Page ${page}`;
          }

          markdown += `\n`;
        });

        markdown += `\n`;
      }

      markdown += `---\n\n`;
    });

    const blob = new Blob([markdown], {
      type: "text/markdown;charset=utf-8",
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = `${getExportFileName()}.md`;

    document.body.appendChild(link);
    link.click();
    link.remove();

    URL.revokeObjectURL(url);
  };

  // =====================================================
  // EXPORT PDF
  // =====================================================

  const exportPDF = () => {
    if (messages.length === 0) return;

    const activeSession = sessions.find((session) => session.id === sessionId);

    const pdf = new jsPDF();

    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();

    const margin = 15;
    const contentWidth = pageWidth - margin * 2;

    let y = 20;

    const addText = (text: string, fontSize: number, isBold = false) => {
      pdf.setFont("helvetica", isBold ? "bold" : "normal");
      pdf.setFontSize(fontSize);

      const lines = pdf.splitTextToSize(text, contentWidth);
      const lineHeight = fontSize * 0.45;

      if (y + lines.length * lineHeight > pageHeight - margin) {
        pdf.addPage();
        y = 20;
      }

      pdf.text(lines, margin, y);
      y += lines.length * lineHeight + 4;
    };

    addText(activeSession?.title || "AI Assistant Conversation", 18, true);

    addText(`Exported: ${new Date().toLocaleString()}`, 9);

    y += 5;

    messages.forEach((message) => {
      const role = message.role === "user" ? "You" : "AI Assistant";

      addText(role, 12, true);
      addText(message.content, 10);

      addText(`Time: ${formatMessageDate(message.created_at)}`, 8);

      if (
        message.role === "assistant" &&
        message.sources &&
        message.sources.length > 0
      ) {
        addText("Sources:", 10, true);

        message.sources.forEach((source) => {
          const title = source.document_title || source.filename || "Document";

          const page = source.page_number ?? source.page;

          const sourceText =
            typeof page === "number"
              ? `- ${title}, Page ${page}`
              : `- ${title}`;

          addText(sourceText, 9);
        });
      }

      y += 5;

      if (y > pageHeight - margin) {
        pdf.addPage();
        y = 20;
      }
    });

    pdf.save(`${getExportFileName()}.pdf`);
  };

  // =====================================================
  // SOURCE DISPLAY
  // =====================================================

  const renderSource = (source: ChatSource, index: number) => {
    const title = source.document_title || source.filename || "Document";

    const page = source.page_number ?? source.page;

    return (
      <p
        key={`${source.document_id ?? "doc"}-${source.chunk_id ?? index}-${index}`}
        className="mb-1 text-xs text-violet-600"
      >
        {title}
        {typeof page === "number" ? `, Page ${page}` : ""}
      </p>
    );
  };

  // =====================================================
  // UI
  // =====================================================

  return (
    <div className="space-y-6">
      {/* PAGE HEADER */}

      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-violet-600">
            <Sparkles size={19} />
            <span className="text-sm font-semibold">AI WORKSPACE</span>
          </div>

          <h1 className="mt-2 text-2xl font-bold text-slate-900">
            AI Assistant
          </h1>

          <p className="mt-1 text-sm text-slate-500">
            Ask questions and discover insights from your PDFs.
          </p>
        </div>

        <button
          onClick={startNewChat}
          disabled={sending || loadingSession}
          className="flex items-center gap-2 rounded-xl bg-violet-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-violet-700 disabled:opacity-50"
        >
          <Plus size={17} />
          New Chat
        </button>
      </div>

      {/* MAIN WORKSPACE */}

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[280px_1fr]">
        {/* LEFT SIDEBAR */}

        <aside className="space-y-5">
          {/* DOCUMENT SELECTION */}

          <div className="rounded-2xl border border-slate-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-slate-900">Your documents</h2>

              <button
                onClick={loadDocuments}
                disabled={loadingDocuments}
                title="Refresh documents"
                className="text-slate-400 hover:text-violet-600"
              >
                <RefreshCw
                  size={16}
                  className={loadingDocuments ? "animate-spin" : ""}
                />
              </button>
            </div>

            <p className="mb-4 mt-1 text-xs text-slate-500">
              Select processed PDFs for your conversation.
            </p>

            {loadingDocuments ? (
              <div className="flex items-center gap-2 py-5 text-sm text-slate-500">
                <Loader2 size={17} className="animate-spin" />
                Loading documents...
              </div>
            ) : readyDocuments.length === 0 ? (
              <div className="rounded-xl bg-slate-50 p-4 text-center">
                <FileText className="mx-auto mb-2 text-slate-400" size={25} />

                <p className="text-sm font-medium text-slate-700">
                  No processed PDFs
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  Upload and process a PDF in your Library first.
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {readyDocuments.map((document) => (
                  <label
                    key={document.id}
                    className="flex cursor-pointer items-start gap-3 rounded-xl border border-slate-200 p-3 hover:border-violet-300"
                  >
                    <input
                      type="checkbox"
                      checked={selectedDocumentIds.includes(document.id)}
                      onChange={() => toggleDocument(document.id)}
                      disabled={sending || loadingSession}
                      className="mt-1 accent-violet-600"
                    />

                    <div className="min-w-0">
                      <p className="break-words text-sm font-medium text-slate-800">
                        {document.title}
                      </p>

                      <p className="mt-1 text-xs text-emerald-600">
                        Ready for AI
                      </p>
                    </div>
                  </label>
                ))}
              </div>
            )}

            <p className="mt-4 text-xs text-slate-400">
              {selectedDocumentIds.length} document(s) selected
            </p>
          </div>

          {/* CHAT HISTORY */}

          <div className="rounded-2xl border border-slate-200 bg-white p-4">
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <History size={17} className="text-violet-600" />

                <h2 className="font-semibold text-slate-900">Chat History</h2>
              </div>

              <button
                onClick={() => loadChatHistory(pagination.page, activeSearch)}
                disabled={loadingHistory}
                title="Refresh chat history"
                className="text-slate-400 hover:text-violet-600"
              >
                <RefreshCw
                  size={15}
                  className={loadingHistory ? "animate-spin" : ""}
                />
              </button>
            </div>

            {/* SEARCH */}

            <form onSubmit={handleSearch} className="mb-3">
              <div className="flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 focus-within:border-violet-400">
                <Search size={16} className="shrink-0 text-slate-400" />

                <input
                  type="text"
                  value={searchInput}
                  onChange={(event) => setSearchInput(event.target.value)}
                  placeholder="Search conversations..."
                  maxLength={100}
                  className="min-w-0 flex-1 bg-transparent text-sm outline-none"
                />

                {searchInput && (
                  <button
                    type="button"
                    onClick={clearSearch}
                    title="Clear search"
                    className="text-slate-400 hover:text-slate-700"
                  >
                    <X size={15} />
                  </button>
                )}
              </div>

              <button
                type="submit"
                disabled={loadingHistory}
                className="mt-2 w-full rounded-lg bg-violet-50 px-3 py-2 text-xs font-medium text-violet-700 hover:bg-violet-100 disabled:opacity-50"
              >
                Search conversations
              </button>
            </form>

            {/* SESSION LIST */}

            {loadingHistory ? (
              <div className="flex items-center gap-2 py-4 text-sm text-slate-500">
                <Loader2 size={16} className="animate-spin" />
                Loading conversations...
              </div>
            ) : sessions.length === 0 ? (
              <p className="py-4 text-center text-xs text-slate-400">
                {activeSearch
                  ? "No matching conversations found."
                  : "No previous conversations yet."}
              </p>
            ) : (
              <div className="max-h-[350px] space-y-2 overflow-y-auto">
                {sessions.map((session) => (
                  <div
                    key={session.id}
                    className={`flex items-start gap-2 rounded-xl border p-3 transition ${
                      sessionId === session.id
                        ? "border-violet-300 bg-violet-50"
                        : "border-slate-100 hover:border-violet-200 hover:bg-slate-50"
                    }`}
                  >
                    <button
                      onClick={() => openPreviousChat(session.id)}
                      disabled={loadingSession || sending}
                      className="min-w-0 flex-1 text-left disabled:opacity-50"
                    >
                      <p className="line-clamp-2 text-sm font-medium text-slate-800">
                        {session.title || "New conversation"}
                      </p>

                      <p className="mt-1 text-xs text-slate-400">
                        {session.message_count ?? 0} messages
                      </p>
                    </button>

                    <button
                      onClick={() => deleteConversation(session.id)}
                      disabled={
                        deletingSessionId !== null || sending || loadingSession
                      }
                      title="Delete conversation"
                      aria-label={`Delete conversation ${session.id}`}
                      className="shrink-0 rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-600 disabled:opacity-40"
                    >
                      {deletingSessionId === session.id ? (
                        <Loader2 size={16} className="animate-spin" />
                      ) : (
                        <Trash2 size={16} />
                      )}
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* PAGINATION */}

            <div className="mt-4 border-t border-slate-100 pt-3">
              <div className="mb-2 flex items-center justify-between text-xs text-slate-400">
                <span>{pagination.total} conversation(s)</span>

                <span>
                  Page {pagination.page} of {Math.max(pagination.pages, 1)}
                </span>
              </div>

              <div className="flex items-center justify-between gap-2">
                <button
                  onClick={goToPreviousPage}
                  disabled={!pagination.has_previous || loadingHistory}
                  className="flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <ChevronLeft size={15} />
                  Previous
                </button>

                <button
                  onClick={goToNextPage}
                  disabled={!pagination.has_next || loadingHistory}
                  className="flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Next
                  <ChevronRight size={15} />
                </button>
              </div>
            </div>
          </div>
        </aside>

        {/* CHAT WINDOW */}

        <section className="flex min-h-[600px] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white">
          {/* CHAT HEADER */}

          <div className="flex flex-wrap items-center gap-3 border-b border-slate-100 p-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-100 text-violet-600">
              <MessageSquareText size={20} />
            </div>

            <div className="min-w-0 flex-1">
              <h2 className="font-semibold text-slate-900">
                {sessionId ? "Previous Conversation" : "Document Chat"}
              </h2>

              <p className="text-xs text-slate-500">
                Powered by FLIPBOOK-AI RAG
              </p>
            </div>

            {/* EXPORT BUTTONS */}

            <div className="flex items-center gap-2">
              <button
                onClick={exportMarkdown}
                disabled={messages.length === 0}
                title="Export as Markdown"
                className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
              >
                <Download size={15} />
                Markdown
              </button>

              <button
                onClick={exportPDF}
                disabled={messages.length === 0}
                title="Export as PDF"
                className="flex items-center gap-1.5 rounded-lg bg-violet-600 px-3 py-2 text-xs font-medium text-white hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-40"
              >
                <FileText size={15} />
                PDF
              </button>
            </div>
          </div>

          {/* MESSAGES */}

          <div className="flex flex-1 flex-col gap-4 overflow-y-auto bg-slate-50/70 p-5">
            {loadingSession && (
              <div className="m-auto flex items-center gap-2 text-sm text-slate-500">
                <Loader2 size={18} className="animate-spin" />
                Restoring conversation...
              </div>
            )}

            {!loadingSession && messages.length === 0 && (
              <div className="m-auto max-w-md py-10 text-center">
                <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-violet-100 text-violet-600">
                  <Sparkles size={27} />
                </div>

                <h3 className="text-lg font-semibold text-slate-900">
                  Ask your documents anything
                </h3>

                <p className="mt-2 text-sm text-slate-500">
                  Select one or more processed PDFs, then ask a question. The AI
                  will search your documents and generate an answer.
                </p>
              </div>
            )}

            {messages.map((message, index) => (
              <div
                key={message.id ?? `${message.role}-${index}`}
                className={`max-w-[85%] rounded-2xl p-4 ${
                  message.role === "user"
                    ? "ml-auto bg-violet-600 text-white"
                    : "mr-auto border border-slate-200 bg-white text-slate-800"
                }`}
              >
                <p className="whitespace-pre-wrap text-sm leading-relaxed">
                  {message.content}
                </p>

                {message.role === "assistant" &&
                  message.sources &&
                  message.sources.length > 0 && (
                    <div className="mt-4 border-t border-slate-200 pt-3">
                      <p className="mb-2 text-xs font-semibold text-slate-500">
                        SOURCES
                      </p>

                      {message.sources.map((source, sourceIndex) =>
                        renderSource(source, sourceIndex),
                      )}
                    </div>
                  )}
              </div>
            ))}

            {sending && (
              <div className="mr-auto flex items-center gap-2 rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-500">
                <Loader2 size={17} className="animate-spin" />
                AI is reading your documents...
              </div>
            )}
          </div>

          {/* ERROR MESSAGE */}

          {error && (
            <div className="mx-4 mt-3 flex items-start gap-2 rounded-xl bg-red-50 p-3 text-sm text-red-600">
              <AlertCircle size={17} className="mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* MESSAGE INPUT */}

          <div className="border-t border-slate-100 bg-white p-4">
            <form
              onSubmit={(event) => {
                event.preventDefault();
                void sendMessage();
              }}
              className="flex items-end gap-3"
            >
              <textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    void sendMessage();
                  }
                }}
                placeholder="Ask a question about your selected PDFs..."
                rows={2}
                disabled={sending || loadingSession}
                className="min-h-[52px] flex-1 resize-none rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-100"
              />

              <button
                type="submit"
                disabled={
                  sending ||
                  loadingSession ||
                  !question.trim() ||
                  selectedDocumentIds.length === 0
                }
                className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-violet-600 text-white hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-40"
                aria-label="Send message"
              >
                {sending ? (
                  <Loader2 size={19} className="animate-spin" />
                ) : (
                  <Send size={19} />
                )}
              </button>
            </form>

            <p className="mt-2 text-center text-xs text-slate-400">
              AI responses are based on the selected documents.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
