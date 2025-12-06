import logger from '../utils/log';
import Forecast from '../models/Forecast';
import Schedule from '../models/Schedule';
import fs from 'fs';
import path from 'path';
import mongoose from 'mongoose';
import { io } from '..';
import Event from '../shared/constants/event';
import HTTPStatus from '../shared/constants/httpStatus';
import { AuthRequest } from '../shared/types/util.type';
import { Response } from 'express';

// Định nghĩa thư mục lưu file JSON
// Thư mục này sẽ nằm tại: Code/server/ai_data
const AI_DATA_FOLDER = path.join(__dirname, '../ai_data');

// Đảm bảo thư mục tồn tại, nếu chưa có thì tạo mới
const ensureFolderExists = () => {
  if (!fs.existsSync(AI_DATA_FOLDER)) {
    fs.mkdirSync(AI_DATA_FOLDER, { recursive: true });
  }
};

/**
 * Xử lý dữ liệu dự báo mưa từ AI
 * Topic: ai/forecast/rain
 */
export const handleRainForecast = async (payload: string) => {
  try {
    logger.info('Nhận được dữ liệu dự báo mưa từ AI');
    
    // Parse JSON
    const data = JSON.parse(payload);
    
    // xuất ra file json
    ensureFolderExists();
    const filePath = path.join(AI_DATA_FOLDER, 'rain_forecast.json');
    
    // Ghi file (ghi đè nội dung cũ bằng nội dung mới nhất)
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2), { encoding: 'utf-8' });
    logger.info(`Đã xuất dữ liệu ra file: ${filePath}`);


    const forecastRecord = {
      date: new Date(data.timestamp),
      chanceOfRain: data.predictions.rain_60min.probability ?? null,
      recommendation: data.recommendation.reason ?? null,
      shouldIrrigate: data.recommendation.should_irrigate ?? null,
    };

    const savedForecast = await Forecast.create(forecastRecord);
    logger.info(`Đã lưu dự báo mưa mới`);


    if (io) {
      io.emit(Event.RAIN_FORECAST, forecastRecord);
      logger.info('Đã emit dự báo mưa mới tới tất cả client');
    }
  } catch (error) {
    logger.error(`Lỗi xử lý topic ai/forecast/rain: ${error}`);
  }
};

/**
 * Xử lý lịch tưới từ AI
 * Topic: ai/schedule/irrigation
 */
export const handleIrrigationSchedule = async (payload: string) => {
  try {
    logger.info('Nhận được lịch tưới từ AI');

    const data = JSON.parse(payload);

    // xuất ra file json
    ensureFolderExists();
    const filePath = path.join(AI_DATA_FOLDER, 'irrigation_schedule.json');
    
    // Ghi file (ghi đè nội dung cũ bằng nội dung mới nhất)
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2), { encoding: 'utf-8' });
    logger.info(`Đã xuất dữ liệu ra file: ${filePath}`);

    if (!data.slots || !Array.isArray(data.slots)) {
      logger.warn('Payload không có mảng slots hợp lệ, bỏ qua xử lý');
      return;
    }

    const schedulesToSave: any[] = [];
    const groupedByDate = new Map<string, any[]>();

    data.slots.forEach((slot: any) => {
      const start = new Date(slot.start_ts);
      const end = new Date(slot.end_ts);

      const dateKey = slot.date || slot.start_ts.split('T')[0];
      const timeStart = start.toLocaleString('vi-VN').split(' ')[0].substring(0, 5);
      const timeEnd = end.toLocaleString('vi-VN').split(' ')[0].substring(0, 5);

      // Dữ liệu để lưu vào DB
      schedulesToSave.push({
        start,
        end,
        durationMin: slot.duration_min,
        date: dateKey,
        note: `Tưới ${slot.duration_min} phút [${timeStart} tới ${timeEnd}]`,
      });

      // Gom nhóm theo ngày để gửi FE
      if (!groupedByDate.has(dateKey)) {
        groupedByDate.set(dateKey, []);
      }
      groupedByDate.get(dateKey)!.push({
        start: timeStart,        // "07:00"
        end: timeEnd,            // "07:20"
        durationMin: slot.duration_min,
      });
    });

    // Chuyển Map → Array để dễ xử lý ở FE
    const groupedDataForFE = Array.from(groupedByDate.entries())
      .map(([date, slots]) => ({
        date,
        slots: slots.sort((a, b) => a.start.localeCompare(b.start))
      }))
      .sort((a, b) => a.date.localeCompare(b.date));

    // Lưu vào DB
    if (schedulesToSave.length > 0) {
      await Schedule.insertMany(schedulesToSave);
      logger.info(`Đã lưu thêm ${schedulesToSave.length} lịch tưới mới vào DB`);
    }

    // Emit về Frontend
    if (io) {
      const emitData = {
        data: groupedDataForFE
      };

      io.emit(Event.IRRIGATION_SCHEDULE_UPDATE, emitData);
      logger.info(`Đã emit ${groupedDataForFE.length} ngày lịch tưới mới tới client`);
    }

  } catch (error) {
    logger.error(`Lỗi xử lý lịch tưới AI: ${error}`);
    // Không cần rollback vì không dùng transaction
  }
};

/**
 * API: Lấy lịch tưới của ngày hôm nay
 * GET /api/ai/schedule/today
 */
export const getScheduleToday = async (req: AuthRequest, res: Response) => {
  logger.info(`Lấy lịch tưới ngày hôm nay`)
  try {
    //  Xác định "Hôm nay" theo giờ Việt Nam (GMT+7)
    // Vì server có thể chạy giờ UTC, nên cần cộng 7 tiếng để ra ngày VN chính xác
    const now = new Date();
    const vnTime = new Date(now.getTime() + 7 * 60 * 60 * 1000);
    const todayStr = vnTime.toISOString().split('T')[0]; // YYYY-MM-DD (Ví dụ: "2025-12-09")

    // Tìm trong DB các slot có date trùng với hôm nay
    const schedules = await Schedule.find({ date: todayStr })
      .select('start end durationMin')
      .sort({ start: 1 })
      .lean();

    const slots = schedules.map((slot) => {
      return{
        start: new Date(slot.start).toLocaleString('vi-VN').split(' ')[0].substring(0, 5),
        end: new Date(slot.end).toLocaleString('vi-VN').split(' ')[0].substring(0, 5),
        durationMin: slot.durationMin
      };
    });

    return res.status(HTTPStatus.OK).json({
      status: HTTPStatus.OK,
      message: 'Lấy lịch tưới hôm nay thành công',
      data: {
        date: todayStr,
        slots: slots
      }
    });

  } catch (error) {
    logger.error(`Lỗi khi lấy lịch hôm nay: ${error}`);
    return res.status(HTTPStatus.INTERNAL_SERVER_ERROR).json({
      status: HTTPStatus.INTERNAL_SERVER_ERROR,
      message: 'Lỗi server',
    })
  }
};