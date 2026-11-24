
import apiClient from "./client";

import type {
  LearningApiResponse,
  GenerateQuizPayload,
  GenerateQuizResult,
  Quiz,
  QuizQuestion,
  QuizListParams,
  QuizListResult,
  SubmitQuizPayload,
  SubmitQuizResult,
  QuizAttemptListResult,
  GenerateFlashcardsPayload,
  GenerateFlashcardsResult,
  FlashcardListParams,
  FlashcardListResult,
  ReviewFlashcardPayload,
  Flashcard,
} from "../../features/learning/types/learning.types";

export const learningApi = {
  // =========================================
  // GENERATE AI QUIZ
  // =========================================

  generateQuiz: async (
    payload: GenerateQuizPayload
  ): Promise<LearningApiResponse<GenerateQuizResult>> => {
    const response = await apiClient.post<
      LearningApiResponse<GenerateQuizResult>
    >("/learning/quizzes/generate", payload, {
      timeout: 600000,
    });

    return response.data;
  },

  // =========================================
  // GET ALL QUIZZES
  // =========================================

  getQuizzes: async (
    params: QuizListParams = {}
  ): Promise<LearningApiResponse<QuizListResult>> => {
    const response = await apiClient.get<
      LearningApiResponse<QuizListResult>
    >("/learning/quizzes", { params });

    return response.data;
  },

  // =========================================
  // GET SINGLE QUIZ WITH QUESTIONS
  // =========================================

  getQuiz: async (
    quizId: number
  ): Promise<LearningApiResponse<{ quiz: Quiz }>> => {
    const response = await apiClient.get<
      LearningApiResponse<{
        quiz: Quiz;
        questions?: QuizQuestion[];
      }>
    >(`/learning/quizzes/${quizId}`, {
      timeout: 60000,
    });

    const apiData = response.data.data;

    if (!apiData?.quiz) {
      throw new Error("Quiz information was not returned by the server.");
    }

    const questions =
      apiData.questions ?? apiData.quiz.questions ?? [];

    const quizWithQuestions: Quiz = {
      ...apiData.quiz,
      questions,
    };

    return {
      ...response.data,
      data: {
        quiz: quizWithQuestions,
      },
    };
  },

  // =========================================
  // SUBMIT QUIZ
  // =========================================

  submitQuiz: async (
    quizId: number,
    payload: SubmitQuizPayload
  ): Promise<LearningApiResponse<SubmitQuizResult>> => {
    const response = await apiClient.post<
      LearningApiResponse<SubmitQuizResult>
    >(
      `/learning/quizzes/${quizId}/submit`,
      payload,
      {
        timeout: 60000,
      }
    );

    return response.data;
  },

  // =========================================
  // GET QUIZ ATTEMPTS
  // =========================================

  getAttempts: async (
    params: QuizListParams = {}
  ): Promise<LearningApiResponse<QuizAttemptListResult>> => {
    const response = await apiClient.get<
      LearningApiResponse<QuizAttemptListResult>
    >("/learning/attempts", { params });

    return response.data;
  },

  // =========================================
  // GENERATE AI FLASHCARDS
  // =========================================

  generateFlashcards: async (
    payload: GenerateFlashcardsPayload
  ): Promise<LearningApiResponse<GenerateFlashcardsResult>> => {
    const response = await apiClient.post<
      LearningApiResponse<GenerateFlashcardsResult>
    >(
      "/learning/flashcards/generate",
      payload,
      {
        timeout: 600000,
      }
    );

    return response.data;
  },

  // =========================================
  // GET SAVED FLASHCARDS
  // =========================================

  getFlashcards: async (
    params: FlashcardListParams = {}
  ): Promise<LearningApiResponse<FlashcardListResult>> => {
    const response = await apiClient.get<
      LearningApiResponse<FlashcardListResult>
    >(
      "/learning/flashcards",
      { params }
    );

    return response.data;
  },

  // =========================================
  // REVIEW FLASHCARD
  // =========================================

  reviewFlashcard: async (
    flashcardId: number,
    payload: ReviewFlashcardPayload
  ): Promise<LearningApiResponse<{ flashcard: Flashcard }>> => {
    const response = await apiClient.patch<
      LearningApiResponse<{ flashcard: Flashcard }>
    >(
      `/learning/flashcards/${flashcardId}/review`,
      payload
    );

    return response.data;
  },

  // =========================================
  // DELETE FLASHCARD
  // DELETE /api/learning/flashcards/:id
  // =========================================

  deleteFlashcard: async (
    flashcardId: number
  ): Promise<
    LearningApiResponse<{
      flashcard_id: number;
      deleted: boolean;
    }>
  > => {
    const response = await apiClient.delete<
      LearningApiResponse<{
        flashcard_id: number;
        deleted: boolean;
      }>
    >(`/learning/flashcards/${flashcardId}`);

    return response.data;
  },
};

export default learningApi;
