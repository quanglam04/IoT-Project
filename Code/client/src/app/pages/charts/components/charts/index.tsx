const Chart = () => {
  return (
    <div className='rounded-3xl border-2 border-gray-800 bg-white p-6 shadow-lg'>
      <h2 className='mb-6 text-2xl font-bold'>Charts</h2>

      <div className='grid grid-cols-1 gap-6 lg:grid-cols-3'>
        <div className='flex h-64 items-center justify-center rounded-2xl border-2 border-gray-200 p-6'>
          <div className='text-center text-gray-400'>[Temperature chart]</div>
        </div>

        <div className='flex h-64 items-center justify-center rounded-2xl border-2 border-gray-200 p-6'>
          <div className='text-center text-gray-400'>[Soil moisture chart]</div>
        </div>

        <div className='flex h-64 items-center justify-center rounded-2xl border-2 border-gray-200 p-6'>
          <div className='text-center text-gray-400'>[Air pressure chart]</div>
        </div>
      </div>
    </div>
  )
}

export default Chart
