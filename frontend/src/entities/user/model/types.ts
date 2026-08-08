export interface User {
  id: number;
  email: string;
  login: string;
  name: string | null;
  avatar_url: string | null;
  bio: string | null;
  is_private: boolean;
}

export interface TokenInfo {
  access_token: string;
  token_type: string;
}
