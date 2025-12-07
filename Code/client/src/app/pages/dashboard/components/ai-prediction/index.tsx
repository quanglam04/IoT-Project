import useAIPredictionHook from './useAIPredictionHook'

const AIPrediction = () => {
  const { rainProbability, suggestion } = useAIPredictionHook()
  return (
    <>
      <div className='rounded-3xl border-2 border-gray-800 bg-white p-6 shadow-lg'>
        <h2 className='mb-4 text-2xl font-bold'>Dự đoán của AI (60m)</h2>

        <div>
          <div className='mb-2 text-lg'>
            Xác suất mưa: <span className='text-2xl font-bold'>{rainProbability}%</span>
          </div>
          <div className='text-sm text-gray-600'>{suggestion}</div>
        </div>
      </div>
    </>
  )
}
export default AIPrediction
