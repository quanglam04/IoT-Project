import { Upload, Button, Card, Typography, Tag, Space } from 'antd'
import { UploadOutlined, CheckCircleOutlined, WarningOutlined } from '@ant-design/icons'
import useUpdateFirmwareHook from './useUpdateFirmwareHook'

const { Title, Text } = Typography

const UpdateFirmwarePage: React.FC = () => {
  const { currentVersion, uploadProps, handleUpload, fileList, uploading, lastUpdateDate } = useUpdateFirmwareHook()
  return (
    <div className='rounded-2xl bg-gradient-to-br from-blue-50 to-blue-100 p-8'>
      <div className='mx-auto max-w-4xl'>
        <Card className='mb-8 rounded-2xl shadow-lg'>
          <Title level={3} className='mb-4'>
            Phiên bản hiện tại
          </Title>
          <div className='flex items-center justify-between'>
            <Space align='center' size='middle'>
              <Title
                level={1}
                className='m-0 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent'
              >
                {currentVersion}
              </Title>
              <Tag color='success' icon={<CheckCircleOutlined />} className='text-sm font-medium'>
                Đang hoạt động
              </Tag>
            </Space>
            <Text type='secondary' className='font-bold'>
              Cập nhật vào lúc: {lastUpdateDate || 'Chưa cập nhật'}
            </Text>
          </div>
        </Card>

        <Card
          title={
            <Title level={3} className='m-0'>
              Cập nhật Firmware
            </Title>
          }
          className='rounded-2xl shadow-lg'
        >
          <Space direction='vertical' size='large' className='w-full'>
            {/* Upload Area */}
            <div className='rounded-lg border-2 border-dashed border-gray-300 bg-white p-8 text-center transition-colors hover:border-blue-500'>
              <Upload {...uploadProps} showUploadList={true} listType='text'>
                <div className='cursor-pointer'>
                  <UploadOutlined className='mb-4 text-5xl text-blue-500' />
                  <p className='mb-2 text-base font-medium text-gray-700'>Nhấp hoặc kéo file vào đây để tải lên</p>
                  <p className='text-sm text-gray-400'>Hỗ trợ: .bin, .hex, .fw</p>
                </div>
              </Upload>
            </div>

            <Button
              type='primary'
              size='large'
              block
              onClick={handleUpload}
              disabled={fileList.length === 0}
              loading={uploading}
              className='h-12 rounded-lg border-none bg-gradient-to-r from-blue-600 to-purple-600 text-base font-semibold hover:from-blue-700 hover:to-purple-700'
            >
              {uploading ? 'Đang tải lên...' : 'Cập nhật Firmware'}
            </Button>

            <Card size='small' className='rounded-lg border border-amber-200 bg-amber-50'>
              <Space>
                <WarningOutlined className='text-lg text-amber-500' />
                <Text className='text-amber-800'>
                  <strong>Lưu ý:</strong> Không ngắt kết nối hoặc tắt nguồn trong quá trình cập nhật firmware.
                </Text>
              </Space>
            </Card>
          </Space>
        </Card>
      </div>
    </div>
  )
}

export default UpdateFirmwarePage
