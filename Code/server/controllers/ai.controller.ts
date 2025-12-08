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
import mqttClient from '../config/mqtt.config';
import Topic from '../shared/constants/topic';
import moment from 'moment-timezone';
import DecisionAI from '../models/DecisionAI';

// Định nghĩa thư mục lưu file JSON
// Thư mục này sẽ nằm tại: Code/server/ai_data
const AI_DATA_FOLDER = path.join(__dirname, '../ai_data');
const VN_TZ = 'Asia/Ho_Chi_Minh';

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
      reason: data.recommendation.reason ?? null,
      shouldIrrigate: data.recommendation.should_irrigate ?? null,
      slot_time: data.slot_id ?? null,
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

    // Ghi file
    ensureFolderExists();
    const filePath = path.join(AI_DATA_FOLDER, 'irrigation_schedule.json');
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf-8');

    if (!data.slots || !Array.isArray(data.slots)) {
      logger.warn('Payload không có mảng slots hợp lệ');
      return;
    }

    const schedulesToSave: any[] = [];
    const decisionToSave: any[] = [];
    const groupedByDate = new Map<string, any[]>();
    const groupedByDateSensor = new Map<string, any[]>();

    data.slots.forEach((slot: any) => {
      // Ép đúng giờ Việt Nam dù chuỗi không có Z
      const start = moment.tz(slot.start_ts, 'YYYY-MM-DDTHH:mm:ss', VN_TZ);
      const end = moment.tz(slot.end_ts, 'YYYY-MM-DDTHH:mm:ss', VN_TZ);

      if (!start.isValid() || !end.isValid()) {
        logger.warn(`Thời gian không hợp lệ: ${slot.start_ts} - ${slot.end_ts}`);
        return;
      }

      const dateKey = start.format('YYYY-MM-DD');
      const timeStart = start.format('HH:mm');
      const timeEnd = end.format('HH:mm');

      if(slot.decision){
          decisionToSave.push({
            date: new Date(slot.forecast_trigger_ts),
            decision: (slot.decision === 'confirm' ? true : false),
            reason: slot.decision_reason
        });
      }

      // Lưu DB
      schedulesToSave.push({
        start: start.toDate(),
        end: end.toDate(),
        durationMin: slot.duration_min,
        date: dateKey,
        decision: slot.decision ? slot.decision == 'confirm'?true:false : true,
        note: `Tưới ${slot.duration_min} phút [${timeStart} - ${timeEnd}]`,
      });

      //  Gửi Frontend
      if (!groupedByDate.has(dateKey)) groupedByDate.set(dateKey, []);
      groupedByDate.get(dateKey)!.push({
        start: timeStart,
        end: timeEnd,
        durationMin: slot.duration_min,
        decision: slot.decision ? slot.decision == 'confirm'?true:false : null
      });

      // Gửi phần cứng,giữ nguyên định dạng 
      if (!groupedByDateSensor.has(dateKey)) groupedByDateSensor.set(dateKey, []);
      groupedByDateSensor.get(dateKey)!.push({
        start_ts: start.format('YYYY-MM-DDTHH:mm:ss'),  
        end_ts:   end.format('YYYY-MM-DDTHH:mm:ss'),   
        duration_min: slot.duration_min,
        decision: slot.decision ? slot.decision == 'confirm'?true:false : true
      });
    });

    // gom nhóm Frontend
    const groupedDataForFE = Array.from(groupedByDate.entries())
      .map(([date, slots]) => ({
        date,
        slots: slots.sort((a, b) => a.start.localeCompare(b.start))
      }))
      .sort((a, b) => a.date.localeCompare(b.date));

    // Phần cứng: đúng định dạng AI yêu cầu
    const groupedDataForHardWare = Array.from(groupedByDateSensor.entries())
      .map(([date, slots]) => ({
        date,
        slots: slots.sort((a, b) => a.start_ts.localeCompare(b.start_ts)) // sort theo chuỗi thời gian
      }))
      .sort((a, b) => a.date.localeCompare(b.date));

    // xóa lịch tưới cũ
    if (schedulesToSave.length > 0) {
      // Lấy danh sách tất cả các date có trong payload mới
      const datesToClean = [...new Set(schedulesToSave.map(s => s.date))];

      if (datesToClean.length > 0) {
        const deleteResult = await Schedule.deleteMany({
          date: { $in: datesToClean }
        });

        logger.info(`Đã xóa ${deleteResult.deletedCount} lịch tưới cũ của các ngày: ${datesToClean.join(', ')}`);
      }
    }

    // Lưu DB
    if (schedulesToSave.length > 0) {
      await Schedule.insertMany(schedulesToSave);
      logger.info(`Đã lưu ${schedulesToSave.length} lịch tưới mới`);
    }

    if (decisionToSave.length > 0) {
      await DecisionAI.insertMany(decisionToSave);
      logger.info(`Đã lưu ${decisionToSave.length} quyết định mới`);
    }

    // Gửi Frontend
    if (io) {
      io.emit(Event.IRRIGATION_SCHEDULE_UPDATE, groupedDataForFE);
    }

    // Gửi phần cứng qua MQTT
    mqttClient.publish(Topic.SCHEDULE_WEEKLY, JSON.stringify(groupedDataForHardWare), (err) => {
      if (err) {
        logger.error(`MQTT publish lỗi: ${err}`);
      } else {
        logger.info(`Đã gửi lịch tưới cho thiết bị qua topic: ${Topic.SCHEDULE_WEEKLY}`);
      }
    });

  } catch (error: any) {
    logger.error(`Lỗi xử lý lịch tưới AI: ${error.message || error}`);
  }
};

/**
 * API: Lấy lịch tưới của ngày hôm nay
 * GET /api/ai/schedule/today
 */

export const getScheduleToday = async (req: AuthRequest, res: Response) => {
  logger.info(`Lấy lịch tưới hôm nay`);

  try {
    const nowVN = moment.tz(VN_TZ);
    const todayStr = nowVN.format('YYYY-MM-DD');

    const schedules = await Schedule.find({ date: todayStr })
      .select('start end durationMin decision')
      .sort({ start: 1 })
      .lean();

    if (!schedules || schedules.length === 0) {
      return res.status(HTTPStatus.OK).json({
        status: HTTPStatus.OK,
        message: 'Hôm nay không có lịch tưới',
        data: { date: todayStr, slots: [] }
      });
    }

    const currentTime = moment.tz(VN_TZ);

    // Tìm slot gần nhất (dù đã qua hay chưa tới)
    let nearestSlot: any = null;
    let nearestDiff = Infinity;

    // Danh sách các slot được phép có decision
    const slotsWithDecision = new Set<string>();

    schedules.forEach((slot) => {
      const startMoment = moment.tz(slot.start, VN_TZ);
      const endMoment = moment.tz(slot.end, VN_TZ);

      // 1. Nếu slot đã bắt đầu (đã qua hoặc đang diễn ra) → chắc chắn có decision
      if (currentTime.isSameOrAfter(startMoment)) {
        slotsWithDecision.add(slot._id.toString());
      }

      // 2. Tính khoảng cách đến giờ bắt đầu để tìm slot gần nhất
      const diff = Math.abs(currentTime.diff(startMoment, 'minutes'));
      if (diff < nearestDiff) {
        nearestDiff = diff;
        nearestSlot = { ...slot, startMoment, endMoment };
      }
    });

    // 3. Slot gần nhất (dù chưa tới) → cũng được thêm decision
    if (nearestSlot) {
      slotsWithDecision.add(nearestSlot._id.toString());
    }

    // Format kết quả
    const slots = schedules.map((slot) => {
      const startMoment = moment.tz(slot.start, VN_TZ);
      const endMoment = moment.tz(slot.end, VN_TZ);

      const result: any = {
        start: startMoment.format('HH:mm'),
        end: endMoment.format('HH:mm'),
        durationMin: slot.durationMin,
      };

      // Chỉ thêm decision nếu nằm trong danh sách được phép
      if (slotsWithDecision.has(slot._id.toString())) {
        result.decision = slot.decision ?? true;
      }

      return result;
    });

    logger.info(`Lịch tưới hôm nay (${todayStr})`);

    return res.status(HTTPStatus.OK).json({
      status: HTTPStatus.OK,
      message: 'Lấy lịch tưới hôm nay thành công',
      data: {
        date: todayStr,
        slots: slots,
      }
    });

  } catch (error: any) {
    logger.error(`Lỗi khi lấy lịch hôm nay: ${error.message || error}`);
    return res.status(HTTPStatus.INTERNAL_SERVER_ERROR).json({
      status: HTTPStatus.INTERNAL_SERVER_ERROR,
      message: 'Lỗi server',
    });
  }
};

export const getAiDecision = async (req: AuthRequest, res: Response) => {
  logger.info(`Lấy 10 quyết định của AI`)
  try {
    const forecasts = await DecisionAI.find() //Decision AI
      .sort({ date: -1 })
      .limit(10)
      .lean(); 
    
    if (!forecasts || forecasts.length === 0) {
      return res.status(HTTPStatus.OK).json({
        status: HTTPStatus.OK,
        message: 'Không có quyết định nào của AI gần đây',
        data: []
      });
    }

    const formattedDecisions = forecasts.map((item) => {
      return {
        date:  moment.utc(item.date).format('DD/MM/YYYY HH:mm'),
        reason: item.reason ?? null,
        decision: item.decision
      };
    });

    return res.status(HTTPStatus.OK).json({
      status: HTTPStatus.OK,
      message: 'Lấy thành công 10 quyết định mới nhất',
      data: formattedDecisions
    })

  } catch (error: any) {
    logger.error(`Lỗi khi lấy quyết định AI: ${error}`);
    return res.status(HTTPStatus.INTERNAL_SERVER_ERROR).json({
      status: HTTPStatus.INTERNAL_SERVER_ERROR,
      message: 'Không thể lấy dữ liệu quyết định AI',
    });
  }
}