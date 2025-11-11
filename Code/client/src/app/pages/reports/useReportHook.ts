const useReportHook = () => {
  const handleExportSensorData = () => {
    console.log('Xuất báo cáo dữ liệu từ cảm biến')
  }

  const handleExportAIData = () => {
    console.log('Xuất báo cáo dữ liệu từ AI xử lý')
  }
  return { handleExportAIData, handleExportSensorData }
}
export default useReportHook
