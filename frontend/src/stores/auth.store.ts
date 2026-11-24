
import { create } from "zustand";

import {
  authApi,
  type User,
  type LoginRequest,
  type RegisterRequest,
} from "../services/api/auth.api";

import {
  setAccessToken,
  getAccessToken,
  getApiErrorMessage,
} from "../services/api/client";

// ---------------------------------------------
// AUTHENTICATION STATE TYPE
// ---------------------------------------------

interface AuthState {
  user: User | null;
  refreshToken: string | null;

  isAuthenticated: boolean;
  isLoading: boolean;
  isInitialized: boolean;

  error: string | null;

  login: (payload: LoginRequest) => Promise<void>;

  register: (payload: RegisterRequest) => Promise<void>;

  logout: () => Promise<void>;

  fetchProfile: () => Promise<void>;

  clearError: () => void;

  clearAuth: () => void;
}

// ---------------------------------------------
// AUTHENTICATION STORE
// ---------------------------------------------

export const useAuthStore = create<AuthState>((set, get) => ({

  // -------------------------------------------
  // INITIAL STATE
  // -------------------------------------------

  user: null,
  refreshToken: null,

  isAuthenticated: false,
  isLoading: false,
  isInitialized: false,

  error: null,

  // -------------------------------------------
  // LOGIN
  // -------------------------------------------

  login: async (payload) => {
    set({
      isLoading: true,
      error: null,
    });

    try {
      const response = await authApi.login(payload);

      const {
        user,
        access_token,
        refresh_token,
      } = response.data;

      // Store access token in memory.
      setAccessToken(access_token);

      set({
        user,
        refreshToken: refresh_token,
        isAuthenticated: true,
        isLoading: false,
        isInitialized: true,
        error: null,
      });

    } catch (error) {
      set({
        isLoading: false,
        isAuthenticated: false,
        error: getApiErrorMessage(error),
      });

      throw error;
    }
  },

  // -------------------------------------------
  // REGISTER
  // -------------------------------------------

  register: async (payload) => {
    set({
      isLoading: true,
      error: null,
    });

    try {
      await authApi.register(payload);

      set({
        isLoading: false,
        error: null,
      });

    } catch (error) {
      set({
        isLoading: false,
        error: getApiErrorMessage(error),
      });

      throw error;
    }
  },

  // -------------------------------------------
  // LOGOUT
  // -------------------------------------------

  logout: async () => {
    const currentRefreshToken = get().refreshToken;

    try {
      // The backend accepts either access or refresh JWT.
      // We send the refresh token to revoke the session.
      if (currentRefreshToken) {
        await authApi.logout();
      }

    } finally {
      setAccessToken(null);

      set({
        user: null,
        refreshToken: null,
        isAuthenticated: false,
        isLoading: false,
        isInitialized: true,
        error: null,
      });
    }
  },

  // -------------------------------------------
  // FETCH PROFILE
  // -------------------------------------------

  fetchProfile: async () => {
    const token = getAccessToken();

    if (!token) {
      set({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        isInitialized: true,
      });

      return;
    }

    set({
      isLoading: true,
      error: null,
    });

    try {
      const response = await authApi.getProfile();

      set({
        user: response.data.user,
        isAuthenticated: true,
        isLoading: false,
        isInitialized: true,
        error: null,
      });

    } catch (error) {
      setAccessToken(null);

      set({
        user: null,
        refreshToken: null,
        isAuthenticated: false,
        isLoading: false,
        isInitialized: true,
        error: getApiErrorMessage(error),
      });
    }
  },

  // -------------------------------------------
  // CLEAR AUTHENTICATION
  // -------------------------------------------

  clearAuth: () => {
    setAccessToken(null);

    set({
      user: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      isInitialized: true,
      error: null,
    });
  },

  // -------------------------------------------
  // CLEAR ERROR
  // -------------------------------------------

  clearError: () => {
    set({
      error: null,
    });
  },

}));
