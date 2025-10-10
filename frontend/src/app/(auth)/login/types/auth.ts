export type AuthCredentials = {
  email: string;
  password: string;
};

export type AuthResponse = {
  token: string;
  user?: {
    id?: string;
    email?: string;
  };
};

export type AuthError = {
  message: string;
  code?: string;
};
