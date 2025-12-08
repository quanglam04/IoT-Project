type PropPumpStatus = {
  handleOnClick: () => Promise<void>
  open: boolean
}

const PumpStatus = ({ handleOnClick, open }: PropPumpStatus) => {
  return (
    <div className='space-y-4'>
      <div className='rounded-3xl border-2 border-gray-800 bg-white p-6 shadow-lg'>
        <h2 className='mb-6 text-2xl font-bold'>Trạng thái bơm</h2>

        <div className='flex items-center justify-between'>
          <div>
            <div className='mb-1 text-sm text-gray-600'>Trạng thái</div>
            <div className='text-3xl font-bold'>{open ? 'ON' : 'OFF'}</div>
          </div>

          <button
            onClick={() => {
              handleOnClick()
            }}
            className={`cursor-pointer rounded-xl ${open ? 'bg-blue-600' : 'bg-gray-400'} px-8 py-3 text-lg font-semibold text-white transition-colors hover:bg-blue-700`}
          >
            {!open ? 'Bật' : 'Tắt'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default PumpStatus
