import clientService from '@/services/client.service'
import useLoadingHook from '@/shared/hook/useLoadingHook'
import type { GetLogsResponse } from '@/shared/types/auth.type'
import { HTTP_STATUS } from '@/shared/types/http.type'
import { useEffect, useState } from 'react'

const useLogHook = () => {
  const [logs, setLogs] = useState<GetLogsResponse[]>([])
  const { start, finish } = useLoadingHook()
  const handleGetLog = async () => {
    try {
      start()
      const response = await clientService.getLogs()
      if (response.status == HTTP_STATUS.OK) {
        const listLogs = response.data.data
        setLogs(listLogs)
      }
    } catch (e) {
      console.log(e)
    } finally {
      finish()
    }
  }

  useEffect(() => {
    handleGetLog()
  }, [])

  return { logs }
}
export default useLogHook
