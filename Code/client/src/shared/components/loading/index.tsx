import useLoadingHook from '@/shared/hook/useLoadingHook'
import { Spin } from 'antd'

const GlobalLoading = () => {
  const { isLoading } = useLoadingHook()

  if (!isLoading) return null

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.35)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999
      }}
    >
      <Spin size='large' />
    </div>
  )
}

export default GlobalLoading
