import { devices } from '../../dummy'

const DeviceList = () => {
  return (
    <div className='h-full rounded-3xl border-2 border-gray-800 bg-white p-6 shadow-lg'>
      <h2 className='mb-6 text-2xl font-bold'>Device list</h2>

      <div className='space-y-3'>
        {devices.map((device, index) => (
          <div key={index} className='flex items-center justify-between py-2'>
            <span className='text-lg'>{device.name}</span>
            <span className={`text-sm font-medium ${device.status === 'online' ? 'text-green-600' : 'text-gray-500'}`}>
              * {device.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default DeviceList
