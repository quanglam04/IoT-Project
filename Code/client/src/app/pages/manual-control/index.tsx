import { useState } from 'react'

const ManualControlPage = () => {
  const [flowRate, setFlowRate] = useState(50)
  const [currentMode, setCurrentMode] = useState('AI Auto')

  return (
    <div className='flex justify-center rounded-2xl bg-gradient-to-br from-blue-50 to-blue-100 p-6'>
      <div className='max-w-4xl rounded-3xl border-2 border-gray-800 bg-white p-8 shadow-lg'>
        <h2 className='mb-8 text-3xl font-bold'>Manual Control</h2>

        <div className='grid grid-cols-1 gap-12 md:grid-cols-2'>
          <div className='space-y-8'>
            <div>
              <h3 className='mb-4 text-lg text-gray-500'>Pump</h3>
              <button className='rounded-xl bg-blue-600 px-8 py-3 text-lg font-semibold text-white transition-colors hover:bg-blue-700'>
                Start pump
              </button>
            </div>

            <div>
              <h3 className='mb-4 text-lg text-gray-500'>Flow rate</h3>
              <input
                type='range'
                min='0'
                max='100'
                value={flowRate}
                onChange={(e) => setFlowRate(Number(e.target.value))}
                className='h-3 w-full cursor-pointer appearance-none rounded-lg bg-gray-200 accent-blue-600'
                style={{
                  background: `linear-gradient(to right, #2563eb 0%, #2563eb ${flowRate}%, #e5e7eb ${flowRate}%, #e5e7eb 100%)`
                }}
              />
              <div className='mt-2 text-sm text-gray-600'>Value: {flowRate}%</div>
            </div>
          </div>

          <div>
            <h3 className='mb-6 text-2xl font-bold'>Override</h3>

            <div className='space-y-6'>
              <div>
                <div className='mb-2 text-gray-500'>
                  Current Mode: <span className='font-semibold text-gray-700'>{currentMode}</span>
                </div>
              </div>

              <button
                onClick={() => setCurrentMode('Manual')}
                className='rounded-xl bg-blue-600 px-8 py-3 text-lg font-semibold text-white transition-colors hover:bg-blue-700'
              >
                Apply manual override
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ManualControlPage
