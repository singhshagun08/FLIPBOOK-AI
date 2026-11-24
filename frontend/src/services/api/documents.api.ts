
import apiClient from "./client";

// ============================================================
// TYPES
// ============================================================

export interface Document {
  id: number;
  user_id?: number;
  title: string;
  description?: string | null;
  original_filename: string;
  file_path?: string;
  stored_filename?: string;
  file_size: number;
  mime_type?: string;
  page_count?: number | null;
  folder_id?: number | null;
  is_favorite: boolean;
  processing_status: string;
  processing_error?: string | null;
  extracted_metadata?: Record<string, unknown> | null;
  checksum?: string;
  created_at: string;
  updated_at?: string;
}

export interface Pagination {
  page: number;
  per_page: number;
  total: number;
  pages: number;
  has_next: boolean;
  has_previous?: boolean;
  has_prev?: boolean;
}

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

export interface DocumentListResponse {
  documents: Document[];
  pagination: Pagination;
}

export interface DocumentListParams {
  page?: number;
  per_page?: number;
  folder_id?: number;
  favorite?: boolean;
}

export interface UploadDocumentPayload {
  file: File;
  title?: string;
  description?: string;
  folder_id?: number;
}

export interface UpdateDocumentPayload {
  title?: string;
  description?: string | null;
  folder_id?: number | null;
  is_favorite?: boolean;
}

export interface ProcessingStatus {
  document_id: number;
  processing_status: string;
  processing_error?: string | null;
  page_count?: number | null;
  extracted_page_count?: number;
  chunk_count?: number;
  extraction_engine?: string | null;
  text_splitter?: string | null;
}

export interface ProcessDocumentResult {
  document: Document;
  processing_status: string;
  indexing_status: string;
  page_count: number;
  chunk_count: number;
  extracted_page_count: number;
  extracted_metadata?: Record<string, unknown>;
}

export interface DocumentChunksResponse {
  document_id: number;
  chunks: Array<Record<string, unknown>>;
  pagination: Pagination;
}

// ============================================================
// UPLOAD PROGRESS CALLBACK
// ============================================================

export type UploadProgressCallback = (percentage: number) => void;

// ============================================================
// DOCUMENT API
// ============================================================

export const documentsApi = {
  // ----------------------------------------------------------
  // 1. UPLOAD DOCUMENT
  // POST /api/documents/upload
  // ----------------------------------------------------------

  upload: async (
    payload: UploadDocumentPayload,
    onUploadProgress?: UploadProgressCallback
  ): Promise<ApiResponse<Document>> => {
    const formData = new FormData();

    // Required PDF file
    formData.append("file", payload.file, payload.file.name);

    // Optional fields
    if (payload.title?.trim()) {
      formData.append("title", payload.title.trim());
    }

    if (payload.description?.trim()) {
      formData.append("description", payload.description.trim());
    }

    if (payload.folder_id !== undefined) {
      formData.append("folder_id", String(payload.folder_id));
    }

    const response = await apiClient.post<ApiResponse<Document>>(
      "/documents/upload",
      formData,
      {
        // IMPORTANT:
        // Remove the shared JSON Content-Type header.
        // The browser must generate multipart/form-data
        // with its own boundary.
        headers: {
          "Content-Type": undefined,
        },

        onUploadProgress: (event) => {
          if (event.total && onUploadProgress) {
            const percentage = Math.round(
              (event.loaded * 100) / event.total
            );

            onUploadProgress(percentage);
          }
        },
      }
    );

    return response.data;
  },

  // ----------------------------------------------------------
  // 2. GET ALL DOCUMENTS
  // GET /api/documents
  // ----------------------------------------------------------

  getAll: async (
    params: DocumentListParams = {}
  ): Promise<{ data: DocumentListResponse }> => {
    const response = await apiClient.get<ApiResponse<DocumentListResponse>>(
      "/documents",
      { params }
    );

    return {
      data: response.data.data,
    };
  },

  // ----------------------------------------------------------
  // 3. GET DOCUMENT BY ID
  // GET /api/documents/:id
  // ----------------------------------------------------------

  getById: async (
    id: number
  ): Promise<ApiResponse<Document>> => {
    const response = await apiClient.get<ApiResponse<Document>>(
      `/documents/${id}`
    );

    return response.data;
  },

  // ----------------------------------------------------------
  // 4. UPDATE DOCUMENT
  // PUT /api/documents/:id
  // ----------------------------------------------------------

  update: async (
    id: number,
    payload: UpdateDocumentPayload
  ): Promise<ApiResponse<Document>> => {
    const response = await apiClient.put<ApiResponse<Document>>(
      `/documents/${id}`,
      payload
    );

    return response.data;
  },

  // ----------------------------------------------------------
  // 5. DELETE DOCUMENT
  // DELETE /api/documents/:id
  // ----------------------------------------------------------

  delete: async (
    id: number
  ): Promise<ApiResponse<Record<string, unknown>>> => {
    const response = await apiClient.delete<
      ApiResponse<Record<string, unknown>>
    >(`/documents/${id}`);

    return response.data;
  },

  // ----------------------------------------------------------
  // 6. DOWNLOAD DOCUMENT
  // GET /api/documents/:id/download
  // ----------------------------------------------------------

  download: async (id: number): Promise<Blob> => {
    const response = await apiClient.get(
      `/documents/${id}/download`,
      {
        responseType: "blob",
      }
    );

    return response.data;
  },

  // ----------------------------------------------------------
  // 7. PROCESS DOCUMENT
  // POST /api/documents/:id/process
  // ----------------------------------------------------------

    process: async (
    id: number
    ): Promise<ApiResponse<ProcessDocumentResult>> => {
        const response = await apiClient.post<
        ApiResponse<ProcessDocumentResult>
            >(
        `/documents/${id}/process`,
         {},
        {
        timeout: 180000,
        }
         );

  return response.data;
},

  // ----------------------------------------------------------
  // 8. GET PROCESSING STATUS
  // GET /api/documents/:id/processing-status
  // ----------------------------------------------------------

  getProcessingStatus: async (
    id: number
  ): Promise<ApiResponse<ProcessingStatus>> => {
    const response = await apiClient.get<
      ApiResponse<ProcessingStatus>
    >(`/documents/${id}/processing-status`);

    return response.data;
  },

  // ----------------------------------------------------------
  // 9. GET DOCUMENT CHUNKS
  // GET /api/documents/:id/chunks
  // ----------------------------------------------------------

  getChunks: async (
    id: number,
    params: { page?: number; per_page?: number } = {}
  ): Promise<ApiResponse<DocumentChunksResponse>> => {
    const response = await apiClient.get<
      ApiResponse<DocumentChunksResponse>
    >(`/documents/${id}/chunks`, { params });

    return response.data;
  },
};

// Default export for components using:
// import documentsApi from ".../documents.api"

export default documentsApi;
