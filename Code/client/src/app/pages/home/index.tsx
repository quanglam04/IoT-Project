import PinInputModal from '@/shared/components/modal/pin-modal'
import useNotificationHook from '@/shared/hook/useNotificationHook'
import { Button, notification } from 'antd'

const Home = () => {
  const { showError, showSuccess } = useNotificationHook()

  return (
    <div className='flex justify-center'>
      <h1 className='mt-50 mr-10 font-bold'>Base Frontend Create 15/06/2025</h1>
      {/* <HeartTrail /> */}
      <PinInputModal onSubmit={() => {}} open={false} />
      <Button
        onClick={() => {
          showSuccess('Thành công rồi đó')
        }}
      >
        Nhấp vào đâyssss
      </Button>
    </div>
  )
}
export default Home
