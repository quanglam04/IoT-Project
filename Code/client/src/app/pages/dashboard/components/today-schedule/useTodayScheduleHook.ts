import clientService from '@/services/client.service'
import type { TodaySchedule } from '@/shared/types/auth.type'
import { useEffect, useState } from 'react'

const useTodayScheduleHook = () => {
  const [todaySchedule, setTodaySchedule] = useState<TodaySchedule>({
    date: '',
    slots: [
      {
        start: '',
        end: '',
        durationMin: 0
      }
    ]
  })
  const fetchTodaySchedule = async () => {
    const response = await clientService.getTodaySchedule()
    if (response.status === 200) {
      setTodaySchedule(response.data.data)
    }
  }
  useEffect(() => {
    fetchTodaySchedule()
  }, [])
  return { todaySchedule }
}
export default useTodayScheduleHook
