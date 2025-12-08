import type { DataType } from '@/app/pages/charts/components/charts/useChartHook'

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
  createdAt: string
  actor: string
  event: string
  details: string
}

interface DataSensorResponse {
  temperatureArr: DataType[]
  pressureArr: DataType[]
  soilMoistureArr: DataType[]
}

interface TodaySchedule {
  date: string
  slots: [
    {
      start: string
      end: string
      durationMin: number
      decision?: boolean
    }
  ]
}

interface RecentAIDecisionResponse {
  date: string
  chanceOfRain: number
  decision: boolean
  reason: string
}

export enum ROLE {
  Admin = 'ADMIN',
  User = 'USER'
}

export type {
  LoginRequest,
  LoginResponse,
  User,
  TodaySchedule,
  GetCountDeviceResposne,
  GetLogsResponse,
  DataSensorResponse,
  RecentAIDecisionResponse
}
