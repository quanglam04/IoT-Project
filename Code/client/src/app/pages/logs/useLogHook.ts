import clientService from '@/services/client.service'
import type { GetLogsResponse } from '@/shared/types/auth.type'
import { HTTP_STATUS } from '@/shared/types/http.type'
import { useEffect, useState } from 'react'

const useLogHook = () => {
  const [logs, setLogs] = useState<GetLogsResponse[]>([])
  const handleGetLog = async () => {
    try {
      const response = await clientService.getLogs()
      if (response.status == HTTP_STATUS.OK) {
        const listLogs = response.data.data
        setLogs(listLogs)
        console.log(listLogs)
      }
    } catch (e) {
      console.log(e)
    }
  }

  useEffect(() => {
    handleGetLog()
  }, [])

  return { logs }
}
export default useLogHook
