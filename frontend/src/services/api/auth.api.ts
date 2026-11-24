
import apiClient from "./client";

// ---------------------------------------------
// Types
// ---------------------------------------------

export interface User {
  id: number;
  full_name: string;
  username: string;
  email: string;
  is_active?: boolean;
  created_at?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AuthResponse extends AuthTokens {
  user: User;
}

export interface RegisterRequest {
  full_name: string;
  username: string;
  email: string;
  password: string;
}

export interface LoginRequest {
  identifier: string;
  password: string;
}

export interface UpdateProfileRequest {
  full_name?: string;
  username?: string;
  email?: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

// ---------------------------------------------
// Authentication API
// ---------------------------------------------

export const authApi = {
  // Register a new account
  register: async (
    payload: RegisterRequest
  ): Promise<ApiResponse<{ user: User }>> => {
    const response = await apiClient.post<
      ApiResponse<{ user: User }>
    >("/auth/register", payload);

    return response.data;
  },

  // Login
  login: async (
    payload: LoginRequest
  ): Promise<ApiResponse<AuthResponse>> => {
    const response = await apiClient.post<
      ApiResponse<AuthResponse>
    >("/auth/login", payload);

    return response.data;
  },

  // Refresh access and refresh tokens
  refresh: async (
    refreshToken: string
  ): Promise<ApiResponse<AuthTokens>> => {
    const response = await apiClient.post<
      ApiResponse<AuthTokens>
    >(
      "/auth/refresh",
      {},
      {
        headers: {
          Authorization: `Bearer ${refreshToken}`,
        },
      }
    );

    return response.data;
  },

  // Logout
  logout: async (): Promise<ApiResponse<Record<string, never>>> => {
    const response = await apiClient.post<
      ApiResponse<Record<string, never>>
    >("/auth/logout");

    return response.data;
  },

  // Get current user profile
  getProfile: async (): Promise<ApiResponse<{ user: User }>> => {
    const response = await apiClient.get<
      ApiResponse<{ user: User }>
    >("/auth/me");

    return response.data;
  },

  // Update profile
  updateProfile: async (
    payload: UpdateProfileRequest
  ): Promise<ApiResponse<{ user: User }>> => {
    const response = await apiClient.put<
      ApiResponse<{ user: User }>
    >("/auth/me", payload);

    return response.data;
  },

  // Change password
  changePassword: async (
    payload: ChangePasswordRequest
  ): Promise<ApiResponse<Record<string, never>>> => {
    const response = await apiClient.post<
      ApiResponse<Record<string, never>>
    >("/auth/change-password", payload);

    return response.data;
  },
};
