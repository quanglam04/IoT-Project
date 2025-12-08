import { Upload, Button } from 'antd'
import { Cpu, AlertTriangle, CheckCircle2, Calendar, Zap, UploadCloud } from 'lucide-react'
import useUpdateFirmwareHook from './useUpdateFirmwareHook'

const UpdateFirmwarePage = () => {
  const { version, uploadProps, handleUpload, fileList, uploading, lastUpdateDate } = useUpdateFirmwareHook()

  return (
    <div className='rounded-2xl bg-gradient-to-br from-blue-50 to-blue-100 p-6'>
      <div className='mx-auto max-w-5xl'>
        {/* Header */}
        <div className='mb-8'>
          <div className='mb-2 flex items-center gap-3'>
            <Cpu className='h-8 w-8 text-blue-600' />
            <h1 className='text-4xl font-bold text-gray-900'>Quản lý Firmware</h1>
          </div>
          <p className='text-gray-600'>Cập nhật và quản lý phiên bản firmware cho thiết bị IoT</p>
        </div>

        <div className='grid gap-6 lg:grid-cols-3'>
          {/* Current Version Card */}
          <div className='lg:col-span-3'>
            <div className='relative overflow-hidden rounded-2xl bg-gradient-to-br from-emerald-600 to-teal-700 p-8 shadow-xl'>
              <div className='absolute top-0 right-0 h-40 w-40 translate-x-10 -translate-y-10 rounded-full bg-white/10'></div>
              <div className='absolute bottom-0 left-0 h-32 w-32 -translate-x-10 translate-y-10 rounded-full bg-white/10'></div>

              <div className='relative'>
                <div className='mb-4 flex items-center gap-2'>
                  <CheckCircle2 className='h-5 w-5 text-emerald-200' />
                  <p className='text-sm font-medium tracking-wide text-emerald-200 uppercase'>Phiên bản hiện tại</p>
                </div>

                <div className='flex items-center justify-between'>
                  <div className='flex items-baseline gap-4'>
                    <span className='text-6xl font-bold text-white'>v{version}</span>
                    <span className='rounded-full bg-white/20 px-4 py-1.5 text-sm font-semibold text-white backdrop-blur-sm'>
                      Đang hoạt động
                    </span>
                  </div>

                  <div className='flex items-center gap-2 text-emerald-100'>
                    <Calendar className='h-5 w-5' />
                    <div className='text-right'>
                      <p className='text-xs text-emerald-200'>Cập nhật lần cuối</p>
                      <p className='text-sm font-semibold'>{lastUpdateDate || 'Chưa cập nhật'}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Upload Section */}
          <div className='lg:col-span-3'>
            <div className='rounded-2xl border-2 border-gray-200 bg-white p-8 shadow-lg'>
              <div className='mb-6 flex items-center gap-3'>
                <div className='flex h-12 w-12 items-center justify-center rounded-xl bg-blue-100'>
                  <Zap className='h-6 w-6 text-blue-600' />
                </div>
                <div>
                  <h2 className='text-2xl font-bold text-gray-900'>Cập nhật Firmware</h2>
                  <p className='text-sm text-gray-600'>Tải lên file firmware mới cho thiết bị</p>
                </div>
              </div>

              {/* Upload Area */}
              <div className='mb-6'>
                <Upload
                  {...uploadProps}
                  showUploadList={true}
                  listType='text'
                  className='w-full [&_.ant-upload]:w-full [&_.ant-upload-select]:w-full'
                >
                  <div className='cursor-pointer rounded-xl border-2 border-dashed border-gray-300 bg-gradient-to-br from-blue-50 to-indigo-50 p-12 text-center transition-all hover:border-blue-500 hover:bg-gradient-to-br hover:from-blue-100 hover:to-indigo-100'>
                    <div className='mb-4 flex justify-center'>
                      <div className='flex h-16 w-16 items-center justify-center rounded-full bg-blue-100'>
                        <UploadCloud className='h-8 w-8 text-blue-600' />
                      </div>
                    </div>
                    <p className='mb-2 text-lg font-semibold text-gray-700'>Nhấp hoặc kéo file vào đây để tải lên</p>
                    <p className='text-sm text-gray-500'>Hỗ trợ định dạng: .bin, .hex, .fw (tối đa 10MB)</p>
                  </div>
                </Upload>
              </div>

              {/* Upload Button */}
              <Button
                type='primary'
                size='large'
                block
                onClick={handleUpload}
                disabled={fileList.length === 0}
                loading={uploading}
                className='h-14 rounded-xl border-none bg-gradient-to-r from-blue-600 to-indigo-600 text-lg font-semibold shadow-lg hover:from-blue-700 hover:to-indigo-700 disabled:from-gray-400 disabled:to-gray-500'
              >
                {uploading ? 'Đang cập nhật firmware...' : 'Bắt đầu cập nhật'}
              </Button>

              {/* Warning Box */}
              <div className='mt-6 rounded-xl border-2 border-amber-200 bg-amber-50 p-4'>
                <div className='flex items-start gap-3'>
                  <div className='flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-amber-500'>
                    <AlertTriangle className='h-5 w-5 text-white' />
                  </div>
                  <div>
                    <p className='mb-1 text-sm font-bold text-amber-900'>Lưu ý quan trọng</p>
                    <ul className='space-y-1 text-xs text-amber-800'>
                      <li>• Không ngắt kết nối hoặc tắt nguồn trong quá trình cập nhật</li>
                      <li>• Đảm bảo thiết bị có đủ pin hoặc kết nối nguồn điện ổn định</li>
                      <li>• Quá trình cập nhật có thể mất từ 2-5 phút</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default UpdateFirmwarePage
