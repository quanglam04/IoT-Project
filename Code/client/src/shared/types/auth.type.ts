interface LoginRequest {
  username: string
  password: string
}

interface LoginResponse {
  access_token: string
  refresh_token: string
  login_at: string
}

export type { LoginRequest, LoginResponse }
