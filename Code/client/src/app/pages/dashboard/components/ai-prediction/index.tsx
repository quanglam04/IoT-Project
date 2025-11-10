import { pumpStatus } from '../../dummy'

const AIPrediction = () => {
  return (
    <>
      <div className='rounded-3xl border-2 border-gray-800 bg-white p-6 shadow-lg'>
        <h2 className='mb-4 text-2xl font-bold'>Dự đoán của AI (60m)</h2>

        <div>
          <div className='mb-2 text-lg'>
            Xác suất mưa: <span className='text-2xl font-bold'>{pumpStatus.aiPrediction.rainProbability}%</span>
          </div>
          <div className='text-sm text-gray-600'>Gợi ý: {pumpStatus.aiPrediction.suggestion}</div>
        </div>
      </div>
    </>
  )
}
export default AIPrediction
