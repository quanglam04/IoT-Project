import logger from '../utils/log';
import SensorData from '../models/SensorData';
import mqttClient from '../config/mqtt.config';
import { Server } from 'socket.io';
import { io } from '..';
import Topic from '../shared/constants/topic';
import Event from '../shared/constants/event';
import HTTPStatus from '../shared/constants/httpStatus';
import { AuthRequest } from '../shared/types/util.type';
import { Response } from 'express';
import { now } from 'mongoose';
import { formatDate, roundToTwo } from '../shared/constants/helper';
import { emit } from 'process';


/**
 * Xử lý tin nhắn từ topic 'sensor/data/push'
 */
const handleSensorData = async (payload: string) => {
  try {
    const data = JSON.parse(payload);
    
    // biến để gửi thẳng lên client qua socket
    const emitData = {
      temperature: roundToTwo(data.temperature),
      humidity: roundToTwo(data.humidity),
      pressureHpa: roundToTwo(data.pressure_hpa),
      soilMoisture: roundToTwo(data.soilMoisture),
      timestamp: formatDate(data.timestamp),
      timestamps: data.timestamp
    };

    // biến model để lưu vào db
    const newData = new SensorData(emitData)

    const savedData = await newData.save();
    logger.info(`Đã lưu sensor data (MQTT): ${savedData._id}`);

    // phát sự kiện tới client, bên client lắng nghe để lấy dữ liệu
    if(io){
      io.emit(Event.SENSOR_DATA_PUSH, emitData)
      logger.info(`Đã emit "sensor/data/push" tới client`);
      logger.info(JSON.stringify(emitData));
    }

  } catch (error) {
    logger.error(`Lỗi xử lý tin nhắn 'sensor/data/push': ${error}`);
  }
};

const getSensorData = async (req: AuthRequest, res: Response) => {
  try {
    // Lấy dữ liệu 24h qua
    const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
    const now = new Date();

    const rawData = await SensorData.find({
      timestamps: { $gte: oneDayAgo, $lte: now }
    })
      .select('temperature pressureHpa soilMoisture timestamp timestamps') // Lấy thêm trường timestamps để tính toán
      .sort({ timestamps: 1 }) // Sắp xếp cũ -> mới
      .lean();

    if (rawData.length === 0) {
      return res.status(HTTPStatus.OK).json({
        status: HTTPStatus.OK,
        message: 'Không có dữ liệu trong 24 giờ gần nhất',
        data: {
          temperatureArr: [],
          pressureArr: [],
          soilMoistureArr: [],
        },
      });
    }

    // Lọc 10p 1 lần
    const filteredData: any[] = [];
    let lastTime = 0;
    const INTERVAL_MS = 10 * 60 * 1000; // 10 phút = 600,000 ms

    rawData.forEach((item) => {
      // Chuyển đổi timestamps sang dạng milliseconds để so sánh
      const currentTime = new Date(item.timestamps).getTime();

      // Nếu là phần tử đầu tiên HOẶC thời gian hiện tại cách lần lấy cuối >= 10 phút
      if (lastTime === 0 || currentTime - lastTime >= INTERVAL_MS) {
        filteredData.push(item);
        lastTime = currentTime; // Cập nhật mốc thời gian vừa lấy
      }
    });

    // Sử dụng filteredData để map dữ liệu trả về thay vì rawData
    const temperatureArr = filteredData.map(item => ({
      time: item.timestamp,                   
      value: item.temperature,
    }));

    const pressureArr = filteredData.map(item => ({
      time: item.timestamp,
      value: item.pressureHpa,
    }));

    const soilMoistureArr = filteredData.map(item => ({
      time: item.timestamp,
      value: item.soilMoisture,
    }));

    return res.status(HTTPStatus.OK).json({
      status: HTTPStatus.OK,
      message: 'Lấy dữ liệu cảm biến 24h thành công (đã lọc 10p/lần)',
      totalFiltered: filteredData.length, // Số bản ghi sau khi lọc
      data: {
        temperatureArr,
        pressureArr,
        soilMoistureArr,
      },
    });

  } catch (error: any) {
    logger.error(`Lỗi khi lấy dữ liệu cảm biến: ${error.message || error}`);
    return res.status(HTTPStatus.INTERNAL_SERVER_ERROR).json({
      status: HTTPStatus.INTERNAL_SERVER_ERROR,
      message: 'Lỗi server',
    });
  }
};

export {handleSensorData, getSensorData}