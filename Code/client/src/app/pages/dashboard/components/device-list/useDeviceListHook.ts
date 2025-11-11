import clientService from '@/services/client.service'
import { HTTP_STATUS } from '@/shared/types/http.type'
import { useEffect, useState } from 'react'

const useDeviceListHook = () => {
  const [count, setCount] = useState<number>(1)

  const fetchNumberOfDevice = async () => {
    const response = await clientService.getCountDevice()
    if (response.status === HTTP_STATUS.OK) {
      const data = response.data.data.numberOfDevices
      setCount(data)
    }
  }

  useEffect(() => {
    fetchNumberOfDevice()
  }, [])
  return { count }
}
export default useDeviceListHook
