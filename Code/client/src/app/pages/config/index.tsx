import useConfigHook from './useConfigHook'

const ConfigPage = () => {
  const {
    handleSaveConfig,
    rainProbabilityThreshold,
    soilMoistureThreshold,
    setRainProbabilityThreshold,
    setSoilMoistureThreshold
  } = useConfigHook()

  return (
    <div className='rounded-2xl bg-gradient-to-br from-blue-50 to-blue-100 p-6'>
      <div className='max-w-3xl rounded-3xl border-2 border-gray-800 bg-white p-8 shadow-lg'>
        <h2 className='mb-8 text-3xl font-bold'>Cấu hình hệ thống</h2>

        <div className='space-y-8'>
          {/* Grid 2 cột cho các input */}
          <div className='grid grid-cols-1 gap-6 md:grid-cols-2'>
            <div>
              <label className='mb-3 block text-lg text-gray-500'>Ngưỡng độ ẩm đất</label>
              <input
                type='number'
                value={soilMoistureThreshold}
                onChange={(e) => setSoilMoistureThreshold(e.target.value)}
                className='w-full rounded-xl border-2 border-gray-300 px-4 py-3 text-center text-lg transition-colors focus:border-blue-500 focus:outline-none'
                placeholder='40'
              />
            </div>

            <div>
              <label className='mb-3 block text-lg text-gray-500'>Ngưỡng xác suất dự báo mưa</label>
              <input
                type='number'
                step='0.1'
                value={rainProbabilityThreshold}
                onChange={(e) => setRainProbabilityThreshold(e.target.value)}
                className='w-full rounded-xl border-2 border-gray-300 px-4 py-3 text-center text-lg transition-colors focus:border-blue-500 focus:outline-none'
                placeholder='0.7'
              />
            </div>
          </div>

          <div className='flex justify-center pt-4'>
            <button
              onClick={handleSaveConfig}
              className='w-full max-w-xl rounded-xl bg-blue-600 px-32 py-4 text-lg font-semibold text-white transition-colors hover:bg-blue-700'
            >
              Lưu cấu hình
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ConfigPage
