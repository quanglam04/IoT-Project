import AIPrediction from './components/ai-prediction'
import DeviceList from './components/device-list'
import PumpStatus from './components/pump-status'
import RecentAIDecision from './components/recent-ai-decision'
import RecentAlert from './components/recent-alerts'
import SensorData from './components/sensor-data'
import WeeklySchedule from './components/today-schedule'

const DashBoardPage = () => {
  return (
    <div className='rounded-2xl bg-gradient-to-br from-blue-50 to-blue-100 p-6'>
      {/* Grid layout - 3 cột */}
      <div className='grid grid-cols-1 gap-6 lg:grid-cols-3'>
        {/* Hàng 1 */}
        <div className='lg:col-span-1'>
          <SensorData />
        </div>
        <div>
          <div className='lg:col-span-1'>
            <PumpStatus />
          </div>

          <div className='mt-5 lg:col-span-1'>
            <AIPrediction />
          </div>
        </div>

        <div className='lg:col-span-1'>
          <DeviceList />
        </div>

        {/* Hàng 2 */}
        <div className='lg:col-span-1'>
          <RecentAIDecision />
        </div>
        <div className='lg:col-span-1'>
          <WeeklySchedule />
        </div>
        <div className='lg:col-span-1'>
          <RecentAlert />
        </div>
      </div>
    </div>
  )
}

export default DashBoardPage
