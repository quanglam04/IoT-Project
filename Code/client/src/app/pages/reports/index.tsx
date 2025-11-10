import { kpiData } from './dummy'

const ReportPage = () => {
  return (
    <div className='rounded-2xl bg-gradient-to-br from-blue-50 to-blue-100 p-6'>
      <div className='max-w-3xl rounded-3xl border-2 border-gray-800 bg-white p-8 shadow-lg'>
        <h2 className='mb-8 text-3xl font-bold'>Báo cáo và Chỉ số Hiệu suất</h2>

        <div className='space-y-4'>
          <h3 className='text-lg text-gray-500'>{kpiData.metric}</h3>

          <div className='text-5xl font-bold'>
            {kpiData.value} <span className='text-3xl text-gray-600'>{kpiData.label}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ReportPage
