import clientService from '@/services/client.service'
import useLoadingHook from '@/shared/hook/useLoadingHook'
import type { User } from '@/shared/types/auth.type'
import { HTTP_STATUS } from '@/shared/types/http.type'
import { useEffect, useState } from 'react'

const useUserHook = () => {
  const [listUser, setListUser] = useState<User[]>([])
  const { finish, start } = useLoadingHook()
  const fetchUser = async () => {
    try {
      start()
      const response = await clientService.getListUser()
      if (response.status === HTTP_STATUS.OK) {
        const users = response.data.data
        setListUser(users)
      }
    } catch (e) {
      console.log(e)
    } finally {
      finish()
    }
  }
  useEffect(() => {
    fetchUser()
  }, [])
  return { listUser }
}
export default useUserHook
