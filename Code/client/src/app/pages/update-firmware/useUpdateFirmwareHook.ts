import clientService from '@/services/client.service'
import mqttClientService from '@/services/mqtt.service'
import useLoadingHook from '@/shared/hook/useLoadingHook'
import useNotificationHook from '@/shared/hook/useNotificationHook'
import storageService from '@/shared/services/storage.service'
import { getDateFormat } from '@/shared/utils/date.util'
import { message, type UploadFile, type UploadProps } from 'antd'
import { useEffect, useState } from 'react'

const useUpdateFirmwareHook = () => {
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [lastUpdateDate, setLastUpdateDate] = useState<string>('')
  const { showError, showSuccess } = useNotificationHook()
  const { start, finish, isLoading } = useLoadingHook()
  const currentVersion = 'v1.2.3'

  const uploadProps: UploadProps = {
    onRemove: (file) => {
      const index = fileList.indexOf(file)
      const newFileList = fileList.slice()
      newFileList.splice(index, 1)
      setFileList(newFileList)
    },
    beforeUpload: (file) => {
      setFileList([file])
      return false
    },
    fileList,
    maxCount: 1,
    accept: '.bin,.hex,.fw'
  }

  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.warning('Vui lòng chọn file firmware!')
      return
    }
    start()
    try {
      const file = fileList[0] as unknown as File

      if (!file) {
        showError('Không tìm thấy file!')
        finish()
        return
      }

      const response = await clientService.uploadFile(file)
      if (response.status === 200) {
        // lắng nghe thông tin từ hivemq, nếu thành công => ok
        console.log('upload thành công')
        mqttClientService.subscribe('upload/status', (message: string) => {
          console.log('lắng nghe')
          // có thể lấy thông tin version để hiển thị, đồng thời set lại ngày
          const { status } = JSON.parse(message)
          console.log(`status: ${status}`)
          if (status === 'done') {
            console.log('status::::', status)
            const updatedAt = getDateFormat()
            setLastUpdateDate(updatedAt)
            localStorage.setItem('updatedAt', updatedAt)
            showSuccess('Upload firmware thành công')
            finish()
          }
        })
        setFileList([])
      } else {
        showError('Upload file thất bại!')
      }
    } catch {
      showError('Lỗi server')
    }
  }

  useEffect(() => {
    const updatedAt = storageService.get('updatedAt') || ''
    if (updatedAt) setLastUpdateDate(updatedAt)
  }, [])

  return { currentVersion, uploadProps, handleUpload, fileList, uploading: isLoading, lastUpdateDate }
}
export default useUpdateFirmwareHook
