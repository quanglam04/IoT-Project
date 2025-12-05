import { useState } from 'react'

const ManualControlPage = () => {
  const [flowRate, setFlowRate] = useState(50)
  const [currentMode, setCurrentMode] = useState('AI Auto')

  return (
    <div className='flex justify-center rounded-2xl bg-gradient-to-br from-blue-50 to-blue-100 p-6'>
      <div className='max-w-4xl rounded-3xl border-2 border-gray-800 bg-white p-8 shadow-lg'>
        <h2 className='mb-8 text-3xl font-bold'>Điều khiển thủ công</h2>

        <div className='grid grid-cols-1 gap-12 md:grid-cols-2'>
          <div className='space-y-8'>
            <div>
              <h3 className='mb-4 text-lg text-gray-500'>Máy bơm</h3>
              <button className='rounded-xl bg-blue-600 px-8 py-3 text-lg font-semibold text-white transition-colors hover:bg-blue-700'>
                Khởi động bơm
              </button>
            </div>
          </div>

          <div>
            <h3 className='mb-6 text-2xl font-bold'>Ghi đè</h3>

            <div className='space-y-6'>
              <div>
                <div className='mb-2 text-gray-500'>
                  Chế độ hiện tại: <span className='font-semibold text-gray-700'>{currentMode}</span>
                </div>
              </div>

              <button
                onClick={() => setCurrentMode('Manual')}
                className='rounded-xl bg-blue-600 px-8 py-3 text-lg font-semibold text-white transition-colors hover:bg-blue-700'
              >
                Áp dụng ghi đè thủ công
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ManualControlPage
