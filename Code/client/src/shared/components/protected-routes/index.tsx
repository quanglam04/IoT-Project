import useAuthenHook from '@/shared/hook/useAuthenHook'
import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'

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
  const isLogin = useAuthenHook()
  const navigate = useNavigate()
  if (!isLogin) {
    navigate('/')
  }
  return <>{children}</>
}
export default ProtectedRotes
