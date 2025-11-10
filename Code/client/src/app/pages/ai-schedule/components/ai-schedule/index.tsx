import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { forecastData } from '../../dummy'

const AISchedule = () => {
  return (
    <div className='rounded-3xl border-2 border-gray-800 bg-white p-6 shadow-lg'>
      <h2 className='mb-6 text-2xl font-bold'>Lịch trình & Dự báo AI</h2>

      <div>
        <h3 className='mb-2 text-lg font-semibold'>Dự báo</h3>
        <p className='mb-4 text-gray-600'>(6 giờ tới)</p>

        <div className='rounded-2xl border-2 border-gray-200 p-6'>
          <ResponsiveContainer width='100%' height={250}>
            <LineChart data={forecastData}>
              <CartesianGrid strokeDasharray='3 3' stroke='#f0f0f0' />
              <XAxis dataKey='time' tick={{ fontSize: 12 }} stroke='#6b7280' />
              <YAxis
                yAxisId='left'
                tick={{ fontSize: 12 }}
                stroke='#ef4444'
                label={{ value: 'Nhiệt độ (°C)', angle: -90, position: 'insideLeft', style: { fontSize: 12 } }}
              />
              <YAxis
                yAxisId='right'
                orientation='right'
                tick={{ fontSize: 12 }}
                stroke='#3b82f6'
                label={{ value: 'Độ ẩm (%)', angle: 90, position: 'insideRight', style: { fontSize: 12 } }}
              />
              <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }} />
              <Legend wrapperStyle={{ fontSize: '14px' }} iconType='line' />
              <Line
                yAxisId='left'
                type='monotone'
                dataKey='temp'
                stroke='#ef4444'
                strokeWidth={3}
                dot={{ fill: '#ef4444', r: 5 }}
                name='Nhiệt độ (°C)'
                activeDot={{ r: 7 }}
              />
              <Line
                yAxisId='right'
                type='monotone'
                dataKey='humidity'
                stroke='#3b82f6'
                strokeWidth={3}
                dot={{ fill: '#3b82f6', r: 5 }}
                name='Độ ẩm (%)'
                activeDot={{ r: 7 }}
              />
              <Line
                yAxisId='right'
                type='monotone'
                dataKey='pressure'
                stroke='#10b981'
                strokeWidth={2}
                strokeDasharray='5 5'
                dot={{ fill: '#10b981', r: 4 }}
                name='Áp suất (hPa)'
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>

          <div className='mt-4 grid grid-cols-1 gap-3 md:grid-cols-3'>
            <div className='rounded-lg border border-red-200 bg-red-50 p-3'>
              <p className='text-xs font-medium text-red-600'>🌡️ Nhiệt độ</p>
              <p className='mt-1 text-sm text-gray-700'>Dự báo tăng cao nhất 31°C vào +3h</p>
            </div>
            <div className='rounded-lg border border-blue-200 bg-blue-50 p-3'>
              <p className='text-xs font-medium text-blue-600'>💧 Độ ẩm</p>
              <p className='mt-1 text-sm text-gray-700'>Giảm xuống 58% rồi tăng trở lại</p>
            </div>
            <div className='rounded-lg border border-green-200 bg-green-50 p-3'>
              <p className='text-xs font-medium text-green-600'>🌪️ Áp suất</p>
              <p className='mt-1 text-sm text-gray-700'>Ổn định quanh 1011-1013 hPa</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AISchedule
