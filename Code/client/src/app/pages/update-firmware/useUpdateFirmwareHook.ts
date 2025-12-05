import clientService from '@/services/client.service'
import mqttClientService from '@/services/mqtt.service'
import useLoadingHook from '@/shared/hook/useLoadingHook'
import useNotificationHook from '@/shared/hook/useNotificationHook'
import { getDateFormat } from '@/shared/utils/date.util'
import { message, type UploadFile, type UploadProps } from 'antd'
import { useState } from 'react'

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
        showSuccess('Upload file thành công!')
        // Cập nhật ngày theo format HH:mm dd/mm/yyyy
        const updatedAt = getDateFormat()
        setLastUpdateDate(updatedAt)
        // lắng nghe thông tin từ hivemq, nếu thành công => ok
        // mqttClientService.subscribe('', () => {
        //   // có thể lấy thông tin version để hiển thị, đồng thời set lại ngày
        //   setLastUpdateDate(new Date().toLocaleDateString)
        //   showSuccess('Upload firmware thành công')
        // })
        setFileList([])
      } else {
        showError('Upload file thất bại!')
      }
    } catch {
      showError('Lỗi server')
    } finally {
      finish()
    }
  }
  return { currentVersion, uploadProps, handleUpload, fileList, uploading: isLoading, lastUpdateDate }
}
export default useUpdateFirmwareHook
