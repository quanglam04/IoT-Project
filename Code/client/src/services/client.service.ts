import http from '@/shared/services/http.service'
import type { ApiResponse } from '@/shared/types/http.type'
import type {
  DataSensorResponse,
  GetCountDeviceResposne,
  GetLogsResponse,
  LoginRequest,
  LoginResponse,
  RecentAIDecisionResponse,
  TodaySchedule,
  User
} from '@/shared/types/auth.type'

class _ClientService {
  async login(payload: LoginRequest) {
    const response = await http.post<ApiResponse<LoginResponse>>('/users/login', payload)
    return response
  }

  async getListUser() {
    const response = await http.get<ApiResponse<User[]>>('/users/list')
    return response
  }

  async getCountDevice() {
    const response = await http.get<ApiResponse<GetCountDeviceResposne>>('/users/count-device')
    return response
  }

  async getLogs() {
    const response = await http.get<ApiResponse<GetLogsResponse[]>>('/users/get-logs')
    return response
  }

  async exportCSVSensor() {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const response = await http.get<ApiResponse<any>>('/users/reports/esp/export', {
      responseType: 'blob'
    })
    return response
  }

  async exportCSVAI() {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const response = await http.get<ApiResponse<any>>('/users/reports/ai/export', {
      responseType: 'blob'
    })
    return response
  }

  async uploadFile(file: File) {
    const formData = new FormData()
    formData.append('file', file)

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const response = await http.post<ApiResponse<any>>('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    return response
  }

  async getDataSensor() {
    const response = await http.get<ApiResponse<DataSensorResponse>>('/sensors/get-data')
    return response
  }

  async getTodaySchedule() {
    const response = await http.get<ApiResponse<TodaySchedule>>('/users/schedule/today')
    return response
  }

  async getHistoryAIDecision() {
    const response = await http.get<ApiResponse<RecentAIDecisionResponse[]>>('/users/ai/decision')
    return response
  }
}
const clientService = new _ClientService()

export default clientService
