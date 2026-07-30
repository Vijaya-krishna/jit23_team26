export interface User {
  id: number;
  username: string;
  email: string;
  role: 'admin' | 'operator';
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  role: 'admin' | 'operator';
  username: string;
}
