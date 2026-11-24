
import type { Pagination } from "../../../services/api/documents.api";

// ============================================================
// COMMON API RESPONSE
// ============================================================

export interface LearningApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

// ============================================================
// COMMON DIFFICULTY
// ============================================================

export type QuizDifficulty = "easy" | "medium" | "hard";

// ============================================================
// QUIZ TYPES
// ============================================================

export interface QuizOption {
  [key: string]: string;
}

export interface QuizQuestion {
  id: number;
  quiz_id: number;
  question_number: number;
  question_text: string;
  question_type: string;
  options: QuizOption;
  explanation?: string | null;
  marks: number;
}

export interface Quiz {
  id: number;
  user_id: number;
  document_id: number | null;
  title: string;
  description?: string | null;
  difficulty: QuizDifficulty;
  total_questions: number;
  time_limit_minutes?: number | null;
  passing_score: number;
  is_published: boolean;
  created_at: string;
  updated_at?: string;
  questions?: QuizQuestion[];
}

// ============================================================
// QUIZ GENERATION
// ============================================================

export interface GenerateQuizPayload {
  document_ids: number[];
  number_of_questions: number;
  difficulty: QuizDifficulty;
  title?: string;
  time_limit_minutes?: number | null;
  passing_score?: number;
}

export interface QuizSource {
  document_id: number;
  document_title: string;
  page_number?: number | null;
  chunk_id?: number | null;
}

export interface GenerateQuizResult {
  quiz: Quiz;
  model: string;
  sources: QuizSource[];
  retrieved_count: number;
}

// ============================================================
// QUIZ LIST
// ============================================================

export interface QuizListParams {
  page?: number;
  per_page?: number;
}

export interface QuizListResult {
  quizzes: Quiz[];
  pagination: Pagination;
}

// ============================================================
// QUIZ SUBMISSION
// ============================================================

export interface SubmitQuizPayload {
  answers: Record<string, string>;
  time_taken_seconds: number;
}

export interface QuestionResult {
  question_id: number;
  submitted_answer: string | null;
  correct_answer: string;
  is_correct: boolean;
  marks_obtained: number;
  total_marks: number;
  explanation: string;
}

export interface QuizAttempt {
  id: number;
  user_id: number;
  quiz_id: number;
  score: number;
  total_marks: number;
  percentage: number;
  answers: Record<string, string>;
  is_passed: boolean;
  time_taken_seconds: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface QuizSubmissionSummary {
  correct_answers: number;
  total_questions: number;
  score: number;
  total_marks: number;
  percentage: number;
  is_passed: boolean;
  passing_score: number;
}

export interface SubmitQuizResult {
  attempt: QuizAttempt;
  results: QuestionResult[];
  summary: QuizSubmissionSummary;
}

// ============================================================
// QUIZ ATTEMPT HISTORY
// ============================================================

export interface QuizAttemptHistoryItem extends QuizAttempt {
  quiz?: Quiz;
}

export interface QuizAttemptListResult {
  attempts: QuizAttemptHistoryItem[];
  pagination?: Pagination;
}

// ============================================================
// FLASHCARD TYPES
// ============================================================

export interface Flashcard {
  id: number;
  user_id: number;
  document_id: number | null;
  question: string;
  answer: string;
  explanation: string | null;
  difficulty: QuizDifficulty;
  tags: string[];
  is_mastered: boolean;
  review_count: number;
  next_review_at: string | null;
  last_reviewed_at: string | null;
  created_at: string;
  updated_at?: string;
}

// ============================================================
// FLASHCARD GENERATION
// ============================================================

export interface GenerateFlashcardsPayload {
  document_ids: number[];
  number_of_cards: number;
  difficulty: QuizDifficulty;
}

export interface GenerateFlashcardsResult {
  flashcards: Flashcard[];
  model: string;
  total_cards: number;
  sources: QuizSource[];
  retrieved_count: number;
}

// ============================================================
// FLASHCARD LIST
// ============================================================

export interface FlashcardListParams {
  document_id?: number;
  difficulty?: QuizDifficulty;
  mastered?: boolean;
}

export interface FlashcardListResult {
  flashcards: Flashcard[];
  total: number;
}

// ============================================================
// FLASHCARD REVIEW
// ============================================================

export interface ReviewFlashcardPayload {
  mastered: boolean;
}
