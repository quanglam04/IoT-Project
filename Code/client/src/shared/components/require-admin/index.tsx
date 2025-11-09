import useAuthenHook from '@/shared/hook/useAuthenHook'
import { Button, Result } from 'antd'
import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'

type Props = {
  children: ReactNode
}

const RequireAdmin = ({ children }: Props) => {
  const navigate = useNavigate()
  const { isAdmin } = useAuthenHook()
  if (isAdmin) return <>{children}</>
  return (
    <Result
      status='403'
      title='403'
      subTitle='Xin lỗi, bạn không có quyền truy cập vào trang này.'
      extra={
        <Button type='primary' onClick={() => navigate('/')}>
          Quay lại trang chủ
        </Button>
      }
    />
  )
}
export default RequireAdmin
