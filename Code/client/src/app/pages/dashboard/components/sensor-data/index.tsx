import { sensorData } from '../../dummy'

const SensorData = () => {
  return (
    <div className='h-full rounded-3xl border-2 border-gray-800 bg-white p-6 shadow-lg'>
      <div className='mb-6 flex items-start justify-between'>
        <h2 className='text-2xl font-bold'>Sensor data</h2>
        <div className='text-right text-sm'>
          <div className='text-gray-600'>Cập nhật lúc</div>
          <div className='font-medium'>{sensorData.lastUpdate}</div>
        </div>
      </div>

      <div className='grid grid-cols-2 gap-6'>
        <div className='text-center'>
          <div className='mb-2 text-sm text-gray-600'>Nhiệt độ</div>
          <div className='mb-1 text-3xl font-bold'>{sensorData.temperature} °C</div>
          <div className='text-sm text-gray-500'>Thoải mái</div>
        </div>

        <div className='text-center'>
          <div className='mb-2 text-sm text-gray-600'>Độ ẩm không khí</div>
          <div className='mb-1 text-3xl font-bold'>{sensorData.humidity} %</div>
          <div className='text-sm text-gray-500'>Cao</div>
        </div>

        <div className='text-center'>
          <div className='mb-2 text-sm text-gray-600'>Độ ẩm đất</div>
          <div className='mb-1 text-3xl font-bold'>{sensorData.soilMoisture} %</div>
          <div className='text-sm text-gray-500'>Khá khô</div>
        </div>

        <div className='text-center'>
          <div className='mb-2 text-sm text-gray-600'>Áp suất không khí</div>
          <div className='mb-1 text-3xl font-bold'>{sensorData.airPressure} mb</div>
          <div className='text-sm text-gray-500'>Bình thường</div>
        </div>
      </div>
    </div>
  )
}

export default SensorData
