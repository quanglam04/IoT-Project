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
  const [version, setVersion] = useState<string>('')

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
        mqttClientService.subscribe('upload/status', (message: string) => {
          const { status } = JSON.parse(message)
          if (status === 'done') {
            let [a, b, c] = version.split('.').map(Number)
            // Tăng version
            c += 1

            if (c >= 10) {
              c = 1
              b += 1
            }

            if (b >= 10) {
              b = 1
              a += 1
            }

            const versionUpdated = `${a}.${b}.${c}`
            const updatedAt = getDateFormat({ onlyDate: false })
            setVersion(versionUpdated)
            setLastUpdateDate(updatedAt)
            localStorage.setItem('updatedAt', updatedAt)
            localStorage.setItem('version', versionUpdated)
            showSuccess('Upload firmware thành công')
            finish()
          }
          if (status === 'error') {
            showError('Lỗi khi cập nhật firmware')
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
    const versionStored = storageService.get('version') || '1.1.10'
    setVersion(versionStored)
  }, [])

  return { version, uploadProps, handleUpload, fileList, uploading: isLoading, lastUpdateDate }
}
export default useUpdateFirmwareHook
