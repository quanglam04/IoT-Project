import clientService from '@/services/client.service'
import useLoadingHook from '@/shared/hook/useLoadingHook'
import useNotificationHook from '@/shared/hook/useNotificationHook'
import { handleDownloadCSV } from '@/shared/utils/exportCSV'

const useReportHook = () => {
  const { showSuccess, showError } = useNotificationHook()
  const { start, finish } = useLoadingHook()
  const handleExportSensorData = async () => {
    try {
      start()
      const response = await clientService.exportCSVSensor()
      let blob: Blob
      if (response.data instanceof Blob) {
        blob = response.data
      } else if (response.data.data instanceof Blob) {
        blob = response.data.data
      } else {
        blob = new Blob([response.data.data], { type: 'text/csv;charset=utf-8;' })
      }
      handleDownloadCSV(blob, 'Báo-cáo-dữ-liệu-thời-tiết')
      finish()
      showSuccess('Xuất thành công dữ liệu cảm biến')
    } catch {
      showError('Lỗi xuất data')
    }
  }

  const handleExportAIData = async () => {
    try {
      start()
      const response = await clientService.exportCSVAI()
      let blob: Blob
      if (response.data instanceof Blob) {
        blob = response.data
      } else if (response.data.data instanceof Blob) {
        blob = response.data.data
      } else {
        blob = new Blob([response.data.data], { type: 'text/csv;charset=utf-8;' })
      }
      handleDownloadCSV(blob, 'Báo-cáo-dữ-liệu-AI')
      finish()
      showSuccess('Xuất thành công dữ liệu AI xử lý')
    } catch {
      showError('Lỗi xuất data')
    }
  }
  return { handleExportAIData, handleExportSensorData }
}
export default useReportHook
