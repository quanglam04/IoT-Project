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

interface User {
  id: string
  email: string
  fullName: string
  address: string
  phoneNumber: string
  role: ROLE
}

interface GetCountDeviceResposne {
  numberOfDevices: number
}

interface GetLogsResponse {
  timestamp: string
  actor: string
  event: string
  description: string
}

export enum ROLE {
  Admin = 'ADMIN',
  User = 'USER'
}

export type { LoginRequest, LoginResponse, User, GetCountDeviceResposne, GetLogsResponse }
