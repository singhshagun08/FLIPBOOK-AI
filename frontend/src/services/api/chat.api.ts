
import apiClient from "./client";

// =====================================================
// CHAT SOURCE
// =====================================================

export interface ChatSource {
  document_id?: number;
  document_title?: string;
  filename?: string;
  page?: number;
  page_number?: number;
  chunk_id?: string | number;
  content?: string;
  relevance_score?: number;
}

// =====================================================
// CHAT MESSAGE
// =====================================================

export interface ChatMessage {
  id: number;
  chat_session_id?: number;
  session_id?: number;
  role: "user" | "assistant" | "system";
  content: string;
  sources?: ChatSource[];
  model_name?: string;
  model?: string;
  response_time_ms?: number;
  extra_data?: {
    grounded?: boolean;
    retrieved_count?: number;
    top_k?: number;
    document_ids?: number[];
  };
  created_at?: string;
}

// =====================================================
// CHAT SESSION
// =====================================================

export interface ChatSession {
  id: number;
  user_id: number;
  title: string;
  description?: string | null;
  is_archived?: boolean;
  document_ids?: number[];
  message_count?: number;
  documents?: Array<{
    id: number;
    title: string;
    original_filename?: string;
  }>;
  messages?: ChatMessage[];
  created_at?: string;
  updated_at?: string;
}

// =====================================================
// PAGINATION
// =====================================================

export interface Pagination {
  page: number;
  per_page: number;
  total: number;
  pages: number;
  has_next: boolean;
  has_previous: boolean;
}

// =====================================================
// REQUEST PAYLOADS
// =====================================================

export interface CreateChatSessionPayload {
  title?: string;
  description?: string | null;
  document_ids?: number[];
}

export interface UpdateChatSessionPayload {
  title?: string;
  description?: string | null;
  is_archived?: boolean;
  document_ids?: number[];
}

export interface SendChatMessagePayload {
  question: string;
  top_k?: number;
}

// =====================================================
// SEND MESSAGE RESPONSE
// Matches backend send_chat_message() response.
// =====================================================

export interface SendChatMessageResponse {
  session_id: number;
  user_message: ChatMessage;
  assistant_message: ChatMessage;
  grounded: boolean;
  retrieved_count: number;
  sources: ChatSource[];
}

// =====================================================
// STANDARD API RESPONSE
// =====================================================

export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data: T;
}

// =====================================================
// CHAT API METHODS
// =====================================================

export const chatApi = {
  // -------------------------------------------------
  // CREATE CHAT SESSION
  // POST /api/chat/sessions
  // -------------------------------------------------

  createSession: async (
    payload: CreateChatSessionPayload
  ): Promise<ChatSession> => {
    const response = await apiClient.post<
      ApiResponse<ChatSession>
    >("/chat/sessions", payload);

    return response.data.data;
  },

  // -------------------------------------------------
  // GET CHAT SESSIONS
  // GET /api/chat/sessions
  // Supports pagination, archive filter and search.
  // -------------------------------------------------

  getSessions: async (
    page = 1,
    perPage = 20,
    archived?: boolean,
    search = ""
  ): Promise<{
    sessions: ChatSession[];
    pagination: Pagination;
  }> => {
    const response = await apiClient.get<
      ApiResponse<{
        sessions: ChatSession[];
        pagination: Pagination;
      }>
    >("/chat/sessions", {
      params: {
        page,
        per_page: perPage,
        ...(archived !== undefined && {
          archived: archived.toString(),
        }),
        ...(search.trim() && {
          search: search.trim(),
        }),
      },
    });

    return response.data.data;
  },

  // -------------------------------------------------
  // GET ONE CHAT SESSION
  // GET /api/chat/sessions/:sessionId
  // -------------------------------------------------

  getSession: async (
    sessionId: number
  ): Promise<ChatSession> => {
    const response = await apiClient.get<
      ApiResponse<ChatSession>
    >(`/chat/sessions/${sessionId}`);

    return response.data.data;
  },

  // -------------------------------------------------
  // UPDATE CHAT SESSION
  // PUT /api/chat/sessions/:sessionId
  // -------------------------------------------------

  updateSession: async (
    sessionId: number,
    payload: UpdateChatSessionPayload
  ): Promise<ChatSession> => {
    const response = await apiClient.put<
      ApiResponse<ChatSession>
    >(`/chat/sessions/${sessionId}`, payload);

    return response.data.data;
  },

  // -------------------------------------------------
  // DELETE CHAT SESSION
  // DELETE /api/chat/sessions/:sessionId
  // -------------------------------------------------

  deleteSession: async (
    sessionId: number
  ): Promise<void> => {
    await apiClient.delete(
      `/chat/sessions/${sessionId}`
    );
  },

  // -------------------------------------------------
  // SEND MESSAGE TO AI
  // POST /api/chat/sessions/:sessionId/messages
  //
  // Backend expects:
  // { question: "...", top_k?: 5 }
  //
  // Backend returns:
  // { user_message, assistant_message, ... }
  // -------------------------------------------------

  sendMessage: async (
    sessionId: number,
    payload: SendChatMessagePayload
  ): Promise<SendChatMessageResponse> => {
    const response = await apiClient.post<
      ApiResponse<SendChatMessageResponse>
    >(
      `/chat/sessions/${sessionId}/messages`,
      payload
    );

    return response.data.data;
  },
};

// =====================================================
// DEFAULT EXPORT
// =====================================================

export default chatApi;
