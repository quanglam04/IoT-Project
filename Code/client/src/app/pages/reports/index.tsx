import { kpiData } from './dummy'
import useReportHook from './useReportHook'

const ReportPage = () => {
  const { handleExportAIData, handleExportSensorData } = useReportHook()
  return (
    <div className='flex justify-center rounded-2xl bg-gradient-to-br from-blue-50 to-blue-100 p-6'>
      <div className='max-w-3xl rounded-3xl border-2 border-gray-800 bg-white p-8 shadow-lg'>
        <h2 className='mb-8 text-3xl font-bold'>Report & KPIs</h2>

        <div className='space-y-4'>
          <h3 className='text-lg text-gray-500'>{kpiData.metric}</h3>

          <div className='text-5xl font-bold'>
            {kpiData.value} <span className='text-3xl text-gray-600'>{kpiData.label}</span>
          </div>
        </div>

        <div className='mt-8 flex gap-4'>
          <button
            onClick={handleExportSensorData}
            className='flex-1 rounded-lg bg-blue-600 px-6 py-3 font-semibold text-white transition-colors hover:bg-blue-700 active:bg-blue-800'
          >
            Xuất báo cáo dữ liệu từ cảm biến
          </button>

          <button
            onClick={handleExportAIData}
            className='flex-1 rounded-lg bg-green-600 px-6 py-3 font-semibold text-white transition-colors hover:bg-green-700 active:bg-green-800'
          >
            Xuất báo cáo dữ liệu từ AI xử lý
          </button>
        </div>
      </div>
    </div>
  )
}

export default ReportPage
