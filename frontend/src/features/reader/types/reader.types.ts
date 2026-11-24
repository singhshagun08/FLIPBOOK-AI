export interface ReaderDocument {
  id: number;
  title: string;
  file_url?: string;
  file_path?: string;
  total_pages?: number;
}

export interface ReaderState {
  currentPage: number;
  totalPages: number;
  zoom: number;
  loading: boolean;
  error: string | null;
}

export interface Bookmark {
  id: string;
  documentId: number;
  pageNumber: number;
  title: string;
  createdAt: string;
}

export interface ReadingProgress {
  documentId: number;
  currentPage: number;
  totalPages: number;
  progressPercentage: number;
  lastReadAt: string;
}