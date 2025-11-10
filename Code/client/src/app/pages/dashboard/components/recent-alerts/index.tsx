import { alerts } from '../../dummy'

const RecentAlert = () => {
  return (
    <div className='h-full rounded-3xl border-2 border-gray-800 bg-white p-6 shadow-lg'>
      <h2 className='mb-6 text-2xl font-bold'>Các cảnh báo gần đây</h2>

      <div className='space-y-4'>
        {alerts.map((alert, index) => (
          <div key={index} className='border-b border-gray-100 pb-4 last:border-0'>
            <div className='mb-1 font-medium'>{alert.message}</div>
            <div className='text-sm text-gray-500'>* {alert.time}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default RecentAlert
