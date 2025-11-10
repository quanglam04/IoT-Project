import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts'
import { humidityData, pressureData, temperatureData } from '../../dummy'
import { useGlobalContext } from '@/shared/context/GlobalContext'

const Chart = () => {
  const { a } = useGlobalContext()
  console.log(`a: ${a}`)
  return (
    <div className='rounded-3xl border-2 border-gray-800 bg-white p-6 shadow-lg'>
      <h2 className='mb-6 text-2xl font-bold'>Biểu đồ</h2>

      <div className='grid grid-cols-1 gap-6 lg:grid-cols-3'>
        <div className='rounded-2xl border-2 border-gray-200 p-4'>
          <h3 className='mb-3 text-center text-lg font-semibold text-gray-700'>Nhiệt độ (°C)</h3>
          <ResponsiveContainer width='100%' height={200}>
            <LineChart data={temperatureData}>
              <CartesianGrid strokeDasharray='3 3' stroke='#f0f0f0' />
              <XAxis dataKey='time' tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} domain={[15, 35]} />
              <Tooltip />
              <Line type='monotone' dataKey='value' stroke='#ef4444' strokeWidth={2} dot={{ fill: '#ef4444', r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className='rounded-2xl border-2 border-gray-200 p-4'>
          <h3 className='mb-3 text-center text-lg font-semibold text-gray-700'>Độ ẩm đất (%)</h3>
          <ResponsiveContainer width='100%' height={200}>
            <AreaChart data={humidityData}>
              <CartesianGrid strokeDasharray='3 3' stroke='#f0f0f0' />
              <XAxis dataKey='time' tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} domain={[0, 100]} />
              <Tooltip />
              <Area type='monotone' dataKey='value' stroke='#3b82f6' fill='#93c5fd' strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className='rounded-2xl border-2 border-gray-200 p-4'>
          <h3 className='mb-3 text-center text-lg font-semibold text-gray-700'>Áp suất (hPa)</h3>
          <ResponsiveContainer width='100%' height={200}>
            <BarChart data={pressureData}>
              <CartesianGrid strokeDasharray='3 3' stroke='#f0f0f0' />
              <XAxis dataKey='time' tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} domain={[1008, 1018]} />
              <Tooltip />
              <Bar dataKey='value' fill='#10b981' radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}

export default Chart
