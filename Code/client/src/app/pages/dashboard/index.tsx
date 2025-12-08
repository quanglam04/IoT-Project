import AIPrediction from './components/ai-prediction'
import DeviceList from './components/device-list'
import PumpStatus from './components/pump-status'
import RecentAIDecision from './components/recent-ai-decision'
import SensorData from './components/sensor-data'
import WeeklySchedule from './components/today-schedule'
import useDashBoardHook from './useDashBoardHook'

const DashBoardPage = () => {
  const { handleOnClick, open } = useDashBoardHook()
  return (
    <div className='rounded-2xl bg-gradient-to-br from-blue-50 to-blue-100 p-6'>
      <div className='grid grid-cols-1 gap-6 lg:grid-cols-3'>
        <div className='lg:col-span-1'>
          <SensorData />
        </div>
        <div>
          <div className='lg:col-span-1'>
            <PumpStatus open={open} handleOnClick={handleOnClick} />
          </div>

          <div className='mt-5 lg:col-span-1'>
            <AIPrediction />
          </div>
        </div>

        <div className='lg:col-span-1'>
          <DeviceList open={open} />
        </div>

        <div className='lg:col-span-2'>
          <RecentAIDecision />
        </div>
        <div className='lg:col-span-1'>
          <WeeklySchedule />
        </div>
      </div>
    </div>
  )
}

export default DashBoardPage
