import type { TokenResponse } from '../types/auth';

const API_BASE_URL = 'http://localhost:8000/api';

class AuthService {
  /**
   * Send credentials to backend to authenticate user.
   */
  async login(username: string, password: string): Promise<TokenResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Authentication failed. Please verify your credentials.');
    }

    return response.json();
  }

  /**
   * Register a new user with email, username, password, and role.
   */
  async register(username: string, email: string, password: string, role: 'admin' | 'operator'): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, email, password, role }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Registration failed.');
    }

    return response.json();
  }
}

export const authService = new AuthService();
