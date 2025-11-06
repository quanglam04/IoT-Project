import mongoose from 'mongoose'
import SensorData from '../models/SensorData'

export const connectDB = async () => {
  try {
    await mongoose.connect(process.env.DB_URL as string, {
      dbName: 'iot'
    })
    console.log(process.env.DB_URL as string)
    console.log('Kết nối thành công')
  } catch (error) {
    console.log(process.env.DB_URL as string)
    console.error(error)
    process.exit(1)
  }
}

export const clearDataSensorData = async () => {
  try {
    const result = await SensorData.deleteMany({})

    console.log('============================================')
    console.log('✅ Xóa dữ liệu thành công')
    console.log(`Số lượng tài khoản đã xóa: ${result.deletedCount}`)
    console.log('============================================')

    return result.deletedCount
  } catch (error) {
    console.error('❌ Lỗi khi xóa dữ liệu users:', error)
    throw error
  }
}
