import Chart from './components/charts'
import SelectTimeRange from './components/select-time-range'

const ChartPage = () => {
  return (
    <div className='rounded-2xl bg-gradient-to-br from-blue-50 to-blue-100 p-6'>
      <div className='space-y-6'>
        {/* Charts Section */}
        <Chart />

        {/* Time Range Selector */}
        <SelectTimeRange />
      </div>
    </div>
  )
}

export default ChartPage
