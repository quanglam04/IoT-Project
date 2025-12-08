import { Request, Response } from 'express'
import User, { UserRole } from "../models/User"
import HTTPStatus from "../shared/constants/httpStatus"
import logger from "../utils/log"
import * as jwt from 'jsonwebtoken'
import { AuthRequest } from '../shared/types/util.type'
import Audit, { AuditEvent } from '../models/Audit'
import { Parser } from 'json2csv'
import SensorData from '../models/SensorData'
import Schedule from '../models/Schedule'
import { io } from '..'


const login = async (req: Request, res: Response) => {
  const { username, password } = req.body
  logger.info(`User [${username}] đăng nhập vào hệ thống`)
  if (!username || !password) {
    return res.status(HTTPStatus.BAD_REQUEST).json({
      status: HTTPStatus.BAD_REQUEST,
      message: 'Vui lòng cung cấp đầy đủ tên đăng nhập và mật khẩu.'
    })
  }
  try {
    const user = await User.findOne({ username: username })
    if (!user) {
      return res.status(HTTPStatus.UNAUTHORIZED).json({
        status: HTTPStatus.UNAUTHORIZED,
        message: 'Tên đăng nhập hoặc mật khẩu không đúng.'
      })
    }
    const isPasswordValid = password === user.password
    if (!isPasswordValid) {
      return res.status(HTTPStatus.UNAUTHORIZED).json({
        status: HTTPStatus.UNAUTHORIZED,
        message: 'Tên đăng nhập hoặc mật khẩu không đúng.'
      })
    }

    // đầu tiên định cho chung mà đọc api design bảo chỉ 3 cái này nên tách ra nhé
    const Payload = { 
      id: user.id,
      username: user.username,
      role: user.role
    }
    const access_token = jwt.sign(Payload, process.env.JWT_SECRET as string, {
      expiresIn: '1d'
    })

    const userResponseData = {
      id: user.id,
      username: user.username,
      email: user.email,
      fullName: user.fullName,
      address: user.address,
      phoneNumber: user.phoneNumber,
      role: user.role
    }
    return res.status(HTTPStatus.OK).json({
      status: HTTPStatus.OK,
      message: 'Đăng nhập thành công',
      data: {
        access_token: access_token,
        user_info: userResponseData
      }
    })
  } catch (error) {
    console.error('Lỗi đăng nhập:', error)
    return res.status(HTTPStatus.INTERNAL_SERVER_ERROR).json({
      status: HTTPStatus.INTERNAL_SERVER_ERROR,
      message: 'Đã xảy ra lỗi hệ thống.'
    })
  }
}

const getListUser = async (req: AuthRequest, res: Response) => {
  logger.info('Lấy danh sách người dùng')
  try {
    const currentUserRole = (req.user as jwt.JwtPayload).role
    if(currentUserRole === UserRole.ADMIN){
      const listUser = await User.find().select('email fullName address phoneNumber role')
      if (listUser.length) {
        return res.status(HTTPStatus.OK).json({
          status: HTTPStatus.OK,
          message: 'Lấy danh sách người dùng thành công',
          data: listUser
        })
      } else {
        return res.status(HTTPStatus.NO_CONTENT).json({
          status: HTTPStatus.NO_CONTENT,
          message: 'Danh sách người dùng hiện đang trống',
          data: listUser
        })
      }
    }
    else{
      return res.status(HTTPStatus.FORBIDDEN).json({
          status: HTTPStatus.FORBIDDEN,
          message: 'Bạn không có quyền hạn này',
        })
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } catch (e: any) {
    logger.error('Lỗi không thể lấy danh sách người dùng: ', e)
    return res.status(HTTPStatus.INTERNAL_SERVER_ERROR).json({
      status: HTTPStatus.INTERNAL_SERVER_ERROR,
      message: 'Lỗi server',
      data: null
    })
  }
}


const formatDate = (date: Date): string => {
  if (!date) return '';

  // Phần Ngày (Date)
  const day = date.getDate().toString().padStart(2, '0');
  const month = (date.getMonth() + 1).toString().padStart(2, '0'); // getMonth() bắt đầu từ 0
  const year = date.getFullYear();

  // Phần Giờ (Time)
  const hours = date.getHours().toString().padStart(2, '0');
  const minutes = date.getMinutes().toString().padStart(2, '0');
  const seconds = date.getSeconds().toString().padStart(2, '0');

  // Kết hợp
  return `${day}/${month}/${year} ${hours}:${minutes}:${seconds}`;
};

const getLogs = async (req: AuthRequest, res: Response) => {
  logger.info('Lấy Logs hệ thống')
  try {
    const username = (req.user as jwt.JwtPayload).username
    const userRole = (req.user as jwt.JwtPayload).role

    if(userRole !== 'ADMIN'){
      logger.error('Bạn không có quyền hạn này')
      return res.status(HTTPStatus.FORBIDDEN).json({
        status: HTTPStatus.FORBIDDEN,
        message: 'Bạn không có quyền hạn này',
      })
    }
    

    const logs = (await Audit.find().sort({createdAt: -1})).map(log => {
      // Chuyển Mongoose document thành plain object
      const logObject = log.toObject();
      
      return {
        ...logObject,
        // Ghi đè trường 'createdAt' bằng chuỗi đã định dạng
        createdAt: formatDate(logObject.createdAt),
      };
    });

    return res.status(HTTPStatus.OK).json({
      status: HTTPStatus.OK,
      message: `[${username}] Lấy toàn bộ Log thành công`,
      data: logs
    })
  } catch (error : any) {
    logger.error('Lỗi không thể lấy nhật ký: ', error)
    return res.status(HTTPStatus.INTERNAL_SERVER_ERROR).json({
      status: HTTPStatus.INTERNAL_SERVER_ERROR,
      message: 'Lỗi server',
    })
  }
}

const exportESP32Report = async (req: AuthRequest, res: Response) => {
  logger.info('Xuất báo cáo dữ liệu của ESP32')
  try {
    const username = (req.user as jwt.JwtPayload).username
    const userRole = (req.user as jwt.JwtPayload).role

    if(userRole !== 'ADMIN'){
      logger.error('Bạn không có quyền hạn này')
      return res.status(HTTPStatus.FORBIDDEN).json({
        status: HTTPStatus.FORBIDDEN,
        message: 'Bạn không có quyền hạn này',
      })
    }

    const newAuditLog = new Audit({
      actor: username,
      event: AuditEvent.GET_ESP32_REPORT,
      details: `Admin [${username}] đã xuất dữ liệu từ các cảm biến`
    })
    await newAuditLog.save()

    // Lấy dữ liệu từ DB (dùng .lean() để tăng tốc độ)
    const allDataSensor = await SensorData.find().sort({ timestamp: 1}).lean();

    if (!allDataSensor || allDataSensor.length === 0) {
      return res.status(HTTPStatus.NOT_FOUND).json({
        message: 'Không có dữ liệu cảm biến để xuất.'
      });
    }

    const formatData = allDataSensor.map(log => ({
      date_time: log.timestamp,
      temperature: log.temperature,
      humidity: log.humidity,
      pressure_hpa: log.pressureHpa,
      soil_moisture: log.soilMoisture
    }));

    // cấu hình file csv
    const fields = ['date_time', 'temperature', 'humidity', 'pressure_hpa', 'soil_moisture'];
    const json2csvParser = new Parser({ fields });
    const csv = json2csvParser.parse(formatData);

    // Thiết lập Headers để trình duyệt tải file về
    res.setHeader('Content-Type', 'text/csv; charset=utf-8');

    // Đặt tên file là 'bao_cao_cam_bien_esp32.csv'
    res.setHeader('Content-Disposition', 'attachment; filename="bao_cao_cam_bien_esp32.csv"');

    // Gửi file csv
    return res.status(HTTPStatus.OK).send(Buffer.from(csv, 'utf-8'));

  } catch (error : any) {
    logger.error('Lỗi không thể xuất báo cáo cảm biến: ', error);
    return res.status(HTTPStatus.INTERNAL_SERVER_ERROR).json({
      status: HTTPStatus.INTERNAL_SERVER_ERROR,
      message: 'Lỗi server',
      data: null
    });
  }
  
}

const exportAiReport = async (req: AuthRequest, res: Response) => {
  logger.info('Xuất báo cáo lịch tưới của AI');

  try {
    const username = (req.user as jwt.JwtPayload).username;
    const userRole = (req.user as jwt.JwtPayload).role;

    // Kiểm tra quyền ADMIN
    if (userRole !== 'ADMIN') {
      logger.error('Bạn không có quyền hạn này');
      return res.status(HTTPStatus.FORBIDDEN).json({
        status: HTTPStatus.FORBIDDEN,
        message: 'Bạn không có quyền hạn này',
      });
    }

    // Ghi log audit
    const newAuditLog = new Audit({
      actor: username,
      event: AuditEvent.GET_AI_REPORT,
      details: `Admin [${username}] đã xuất báo cáo lịch tưới của AI`,
    });
    await newAuditLog.save();

    // Lấy toàn bộ lịch tưới từ AI (sắp xếp theo ngày và giờ bắt đầu)
    const schedules = await Schedule.find()
      .sort({ date: 1, start: 1 })
      .lean()
      .exec();

    if (!schedules || schedules.length === 0) {
      return res.status(HTTPStatus.NOT_FOUND).json({
        message: 'Không có dữ liệu lịch tưới của AI để xuất.',
      });
    }

    const formatData = schedules.map((item) => ({
      date: item.date,                  
      start: new Date(item.start).toLocaleString('vi-VN').split(' ')[0].substring(0, 5),
      end: new Date(item.end).toLocaleString('vi-VN').split(' ')[0].substring(0, 5),   
      duration_min: item.durationMin,     
      note: item.note,                   
    }));

    const fields = ['date', 'start', 'end', 'duration_min', 'note'];
    const opts = { fields, header: true };
    const json2csvParser = new Parser(opts);
    const csv = json2csvParser.parse(formatData);

    // Thiết lập header để tải file CSV về
    res.setHeader('Content-Type', 'text/csv; charset=utf-8');
    res.setHeader(
      'Content-Disposition',
      'attachment; filename="bao_cao_lich_tuoi_ai.csv"'
    );

    // Trả về file CSV
    return res.status(HTTPStatus.OK).send(Buffer.from('\uFEFF' + csv, 'utf-8'));

  } catch (error: any) {
    logger.error('Lỗi khi xuất báo cáo lịch tưới AI: ', error);
    return res.status(HTTPStatus.INTERNAL_SERVER_ERROR).json({
      status: HTTPStatus.INTERNAL_SERVER_ERROR,
      message: 'Lỗi server khi xuất báo cáo',
      data: null,
    });
  }
};

export { login, getListUser, getLogs, exportESP32Report, exportAiReport}