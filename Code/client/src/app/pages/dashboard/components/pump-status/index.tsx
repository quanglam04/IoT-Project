import { pumpStatus } from '../../dummy'

const PumpStatus = () => {
  return (
    <div className='space-y-4'>
      <div className='rounded-3xl border-2 border-gray-800 bg-white p-6 shadow-lg'>
        <h2 className='mb-6 text-2xl font-bold'>Pump status</h2>

        <div className='flex items-center justify-between'>
          <div>
            <div className='mb-1 text-sm text-gray-600'>Trạng thái</div>
            <div className='text-3xl font-bold'>{pumpStatus.status}</div>
          </div>

          <button className='rounded-xl bg-blue-600 px-8 py-3 text-lg font-semibold text-white transition-colors hover:bg-blue-700'>
            Bật/Tắt
          </button>
        </div>
      </div>
    </div>
  )
}

export default PumpStatus
