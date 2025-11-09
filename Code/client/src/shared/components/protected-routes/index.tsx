import useAuthenHook from '@/shared/hook/useAuthenHook'
import useNotificationHook from '@/shared/hook/useNotificationHook'
import type { ReactNode } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'

/**
 * @description: Mô tả về cách dùng của compoent này
 * Muốn bọc ngoài component để chắc chắn nó login rồi mới cho vào
 * Trong file route
 * path: '/',
 *   children: [
 *     {
 *       index: true,
 *       element: (
 *         <ProtectedRoutes>
 *           <Home />
 *         </ProtectedRoutes>
 *       )
 *     },
 *
 */

type Props = {
  children: ReactNode
}
const ProtectedRotes = ({ children }: Props) => {
  const { isLogin } = useAuthenHook()
  console.log(`isLogin:::`, isLogin)
  const { showError } = useNotificationHook()
  if (!isLogin) {
    showError('Vui lòng đăng nhập')
    return <Navigate to={'/login'} />
  }
  return <>{children}</>
}
export default ProtectedRotes
