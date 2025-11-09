const AISchedule = () => {
  return (
    <div className='rounded-3xl border-2 border-gray-800 bg-white p-6 shadow-lg'>
      <h2 className='mb-6 text-2xl font-bold'>AI Schedule & Forecast</h2>

      <div>
        <h3 className='mb-2 text-lg font-semibold'>Forecast</h3>
        <p className='mb-4 text-gray-600'>(next 6 hours)</p>

        <div className='flex h-64 items-center justify-center rounded-2xl border-2 border-gray-200 p-6'>
          <div className='text-center text-gray-400 italic'>[Line chart]</div>
        </div>
      </div>
    </div>
  )
}

export default AISchedule
