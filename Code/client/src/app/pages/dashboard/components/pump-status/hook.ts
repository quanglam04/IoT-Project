import useNotificationHook from '@/shared/hook/useNotificationHook'
import { useState } from 'react'

const useHook = () => {
  const [open, setOpen] = useState<boolean>(false)
  const { showSuccess } = useNotificationHook()
  const handleOnClick = () => {
    if (open) showSuccess('Tắt bơm thành công')
    else showSuccess('Bật bơm thành công')
    setOpen((prev) => !prev)
    // call API gửi lên cho kiên
  }
  return { open, handleOnClick }
}
export default useHook
