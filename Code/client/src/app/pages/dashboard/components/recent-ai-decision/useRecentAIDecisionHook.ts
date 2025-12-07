import clientService from '@/services/client.service'
import type { RecentAIDecisionResponse } from '@/shared/types/auth.type'
import { useEffect, useState } from 'react'

const useRecentAIDecisionHook = () => {
  const [recentAIDecision, setRecentAIDecision] = useState<RecentAIDecisionResponse[]>([])

  const fetchData = async () => {
    const response = await clientService.getHistoryAIDecision()
    if (response.status === 200) {
      const dataResponse = response.data.data
      setRecentAIDecision([...dataResponse])
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  return { recentAIDecision }
}
export default useRecentAIDecisionHook
