export interface User {
  id: number;
  email: string;
  login: string;
  name: string | null;
  avatar_url: string | null;
}

export interface TokenInfo {
  access_token: string;
  token_type: string;
}
