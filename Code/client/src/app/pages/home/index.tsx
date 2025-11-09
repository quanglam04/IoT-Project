import PinInputModal from '@/shared/components/modal/pin-modal'
import useNotificationHook from '@/shared/hook/useNotificationHook'
import { Button, notification } from 'antd'
import useHomeHook from './useHomeHook'

const Home = () => {
  const { dataSensor } = useHomeHook()

  return (
    <>
      <div className='flex min-h-screen flex-col items-center justify-center text-2xl'>
        <div className='mb-10 text-3xl font-bold'>Data from Sensor</div>
        <div className='space-y-4 text-center'>
          <div>Temperature: {dataSensor.temperature}</div>
          <div>Humidity: {dataSensor.humidity}</div>
          <div>Light: {dataSensor.light}</div>
          <div>SoilMoisture: {dataSensor.soilMoisture}</div>
          <div>Date: {dataSensor.timestamp}</div>
        </div>
      </div>
    </>
  )
}
export default Home
