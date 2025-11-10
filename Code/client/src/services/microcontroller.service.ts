import http from '@/shared/services/http.service'
import type { ApiResponse } from '@/shared/types/http.type'

class MicroControllerService {
  async ChangeStatusPump(currentStatus: boolean) {
    const response = await http.post<ApiResponse<string>>('/micro-controller/change-status/pump', {
      currentStatus: currentStatus
    })
    return response
  }
}

export default MicroControllerService
