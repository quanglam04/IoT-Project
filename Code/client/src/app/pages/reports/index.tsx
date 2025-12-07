import { BarChart3, Download, TrendingUp, Activity } from 'lucide-react'
import { kpiData } from './dummy'
import useReportHook from './useReportHook'
import { getDateFormat } from '@/shared/utils/date.util'

const ReportPage = () => {
  const { handleExportAIData, handleExportSensorData } = useReportHook()

  return (
    <div className='rounded-2xl bg-gradient-to-br from-blue-50 to-blue-100 p-6'>
      <div className='mx-auto max-w-6xl'>
        <div className='mb-8'>
          <div className='mb-2 flex items-center gap-3'>
            <BarChart3 className='h-8 w-8 text-blue-600' />
            <h1 className='text-4xl font-bold text-gray-900'>Báo cáo & Hiệu suất</h1>
          </div>
          <p className='text-gray-600'>Theo dõi và xuất báo cáo dữ liệu hệ thống</p>
        </div>

        <div className='grid gap-6 lg:grid-cols-2'>
          <div className='lg:col-span-2'>
            <div className='relative overflow-hidden rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-700 p-8 shadow-xl'>
              <div className='absolute top-0 right-0 h-40 w-40 translate-x-10 -translate-y-10 rounded-full bg-white/10'></div>
              <div className='absolute bottom-0 left-0 h-32 w-32 -translate-x-10 translate-y-10 rounded-full bg-white/10'></div>

              <div className='relative'>
                <div className='mb-4 flex items-center gap-2'>
                  <TrendingUp className='h-5 w-5 text-blue-200' />
                  <p className='text-sm font-medium tracking-wide text-blue-200 uppercase'>{kpiData.metric}</p>
                </div>

                <div className='flex items-baseline gap-3'>
                  <span className='text-7xl font-bold text-white'>{kpiData.value}</span>
                  <span className='text-3xl font-semibold text-blue-200'>{kpiData.label}</span>
                </div>

                <div className='mt-6 flex items-center gap-2 text-sm text-blue-100'>
                  <Activity className='h-4 w-4' />
                  <span>Cập nhật lần cuối: Hôm nay, {getDateFormat({ onlyDate: true })}</span>
                </div>
              </div>
            </div>
          </div>

          <div className='group rounded-2xl border-2 border-gray-200 bg-white p-6 shadow-lg transition-all hover:border-blue-500 hover:shadow-xl'>
            <div className='mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-blue-100 transition-colors group-hover:bg-blue-600'>
              <Activity className='h-7 w-7 text-blue-600 transition-colors group-hover:text-white' />
            </div>

            <h3 className='mb-2 text-xl font-bold text-gray-900'>Dữ liệu Cảm biến</h3>
            <p className='mb-6 text-sm text-gray-600'>Xuất báo cáo chi tiết từ các cảm biến IoT trong hệ thống</p>

            <button
              onClick={handleExportSensorData}
              className='flex w-full cursor-pointer items-center justify-center gap-2 rounded-xl bg-blue-600 px-6 py-3.5 font-semibold text-white transition-all hover:bg-blue-700 active:scale-95'
            >
              <Download className='h-5 w-5' />
              Xuất báo cáo
            </button>
          </div>

          <div className='group rounded-2xl border-2 border-gray-200 bg-white p-6 shadow-lg transition-all hover:border-green-500 hover:shadow-xl'>
            <div className='mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-green-100 transition-colors group-hover:bg-green-600'>
              <BarChart3 className='h-7 w-7 text-green-600 transition-colors group-hover:text-white' />
            </div>

            <h3 className='mb-2 text-xl font-bold text-gray-900'>Dữ liệu AI</h3>
            <p className='mb-6 text-sm text-gray-600'>Xuất báo cáo phân tích và quyết định từ AI xử lý</p>

            <button
              onClick={handleExportAIData}
              className='flex w-full cursor-pointer items-center justify-center gap-2 rounded-xl bg-green-600 px-6 py-3.5 font-semibold text-white transition-all hover:bg-green-700 active:scale-95'
            >
              <Download className='h-5 w-5' />
              Xuất báo cáo
            </button>
          </div>
        </div>

        <div className='mt-6 rounded-xl border border-amber-200 bg-amber-50 p-4'>
          <div className='flex items-start gap-3'>
            <div className='flex h-6 w-6 items-center justify-center rounded-full bg-amber-500 text-sm font-bold text-white'>
              i
            </div>
            <div>
              <p className='text-sm font-medium text-amber-900'>Báo cáo sẽ được xuất dưới định dạng CSV</p>
              <p className='mt-1 text-xs text-amber-700'>Dữ liệu bao gồm toàn bộ thông tin trong cơ sở dữ liệu</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ReportPage
