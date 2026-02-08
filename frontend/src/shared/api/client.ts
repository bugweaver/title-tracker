const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export interface ApiError {
  detail: string;
  status: number;
}

// Flag to prevent multiple refresh attempts
let isRefreshing = false;
// Queue of requests waiting for token refresh
let refreshQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: ApiError) => void;
}> = [];

function processRefreshQueue(token: string | null, error: ApiError | null) {
  refreshQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else if (token) {
      resolve(token);
    }
  });
  refreshQueue = [];
}

class ApiClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('access_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  private async refreshToken(): Promise<string> {
    const response = await fetch(`${this.baseURL}/auth/refresh`, {
      method: 'POST',
      credentials: 'include', // Send cookies
    });

    if (!response.ok) {
      // Clear access token on refresh failure
      localStorage.removeItem('access_token');
      throw { detail: 'Session expired', status: 401 } as ApiError;
    }

    const data = await response.json();
    localStorage.setItem('access_token', data.access_token);
    return data.access_token;
  }

  private async handleTokenRefresh(): Promise<string> {
    if (isRefreshing) {
      // Wait for ongoing refresh
      return new Promise((resolve, reject) => {
        refreshQueue.push({ resolve, reject });
      });
    }

    isRefreshing = true;

    try {
      const newToken = await this.refreshToken();
      processRefreshQueue(newToken, null);
      return newToken;
    } catch (error) {
      processRefreshQueue(null, error as ApiError);
      throw error;
    } finally {
      isRefreshing = false;
    }
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retry = true
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const headers: HeadersInit = {
      ...this.getAuthHeaders(),
      ...options.headers,
    };

    const response = await fetch(url, {
      ...options,
      headers,
      credentials: 'include', // Always include cookies
    });

    if (!response.ok) {
      // Handle 401 - try to refresh token
      if (response.status === 401 && retry && !endpoint.includes('/auth/login') && !endpoint.includes('/auth/register') && !endpoint.includes('/auth/refresh')) {
        try {
          await this.handleTokenRefresh();
          // Retry the original request with new token
          return this.request<T>(endpoint, options, false);
        } catch {
          // Refresh failed, throw original error
        }
      }

      const error: ApiError = {
        detail: 'Произошла ошибка',
        status: response.status,
      };
      
      try {
        const data = await response.json();
        error.detail = data.detail || data.message || error.detail;
      } catch {
        // Response is not JSON
      }
      
      throw error;
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async getBlob(endpoint: string): Promise<Blob> {
    const url = `${this.baseURL}${endpoint}`;
    const headers: HeadersInit = {
        ...this.getAuthHeaders(),
    };

    const response = await fetch(url, {
        method: 'GET',
        headers,
        credentials: 'include',
    });

    if (!response.ok) {
        throw { detail: 'Failed to download file', status: response.status } as ApiError;
    }

    return response.blob();
  }

  async postFormUrlEncoded<T>(endpoint: string, data: Record<string, string>): Promise<T> {
    const formBody = new URLSearchParams(data).toString();
    return this.request<T>(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formBody,
    });
  }

  async postFormData<T>(endpoint: string, data: FormData): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      // Content-Type header should be omitted so browser sets it with boundary
      body: data,
    });
  }

  async put<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

export const apiClient = new ApiClient(API_BASE_URL);
