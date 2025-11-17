import clientService from '@/services/client.service'
import useNotificationHook from '@/shared/hook/useNotificationHook'
import { handleDownloadCSV } from '@/shared/utils/exportCSV'

const useReportHook = () => {
  const { showSuccess } = useNotificationHook()
  const handleExportSensorData = async () => {
    try {
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
      showSuccess('Xuất thành công dữ liệu cảm biến')
    } catch (error) {
      console.error('Export error:', error)
    }
  }

  const handleExportAIData = () => {
    console.log('Xuất báo cáo dữ liệu từ AI xử lý')
  }
  return { handleExportAIData, handleExportSensorData }
}
export default useReportHook
