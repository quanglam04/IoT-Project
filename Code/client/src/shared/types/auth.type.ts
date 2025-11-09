interface LoginRequest {
  username: string
  password: string
}

interface LoginResponse {
  access_token: string
  user_info: {
    username: string
    fullName: string
    address: string
    phoneNumber: string
    role: ROLE
  }
}

export enum ROLE {
  Admin = 'ADMIN',
  User = 'USER'
}

export type { LoginRequest, LoginResponse }
