import { Request, Response } from 'express';
import * as jwt from 'jsonwebtoken'
import multer from 'multer';
import path from 'path';
import fs from 'fs';
import HTTPStatus from '../shared/constants/httpStatus';
import logger from '../utils/log';
import { AuthRequest } from '../shared/types/util.type';
import Audit, { AuditEvent } from '../models/Audit';
import mqttClient from '../config/mqtt.config';
import Topic from '../shared/constants/topic';

const UPLOAD_FOLDER = 'uploads/';

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    // 1. Kiểm tra và tạo thư mục nếu chưa có
    if (!fs.existsSync(UPLOAD_FOLDER)) {
      fs.mkdirSync(UPLOAD_FOLDER, { recursive: true });
    }
    cb(null, UPLOAD_FOLDER);
  },
  filename: (req, file, cb) => {
    try {
      // Lấy danh sách file hiện có trong thư mục để đếm
      // Nếu thư mục chưa có file thì length = 0
      let fileCount = 0;
      if (fs.existsSync(UPLOAD_FOLDER)) {
        const files = fs.readdirSync(UPLOAD_FOLDER);
        fileCount = files.length;
      }

      const version = fileCount + 1;

      // Tách tên file và đuôi file
      // Ví dụ: file gốc là "bao-cao.pdf"
      // nameWithoutExt = "bao-cao"
      // ext = ".pdf"
      const nameWithoutExt = path.parse(file.originalname).name;
      const ext = path.extname(file.originalname);

      // Tạo tên mới: "file-version3.pdf"
      const newFileName = `${nameWithoutExt}_v${version}${ext}`;
      
      cb(null, newFileName);

    } catch (error) {
      // Fallback: Nếu lỗi khi đọc thư mục, quay về dùng timestamp để không bị crash
      const fallbackName = Date.now() + '-' + file.originalname;
      cb(null, fallbackName);
    }
  }
});

export const uploadConfig = multer({ storage: storage });

/**
 * 
 * @param req 
 * @param res 
 * @returns fileUrl 
 */

export const handleUpload = async (req: AuthRequest, res: Response) => {
  try {
    const actor = (req.user as jwt.JwtPayload).username
    const actorRole = (req.user as jwt.JwtPayload).role

    if(actorRole !== 'ADMIN'){
      logger.error('Bạn không có quyền hạn này')
      return res.status(HTTPStatus.FORBIDDEN).json({
        status: HTTPStatus.FORBIDDEN,
        message: 'Bạn không có quyền hạn này',
      })
    }

    if (!req.file) {
      return res.status(HTTPStatus.BAD_REQUEST).json({ 
        status: HTTPStatus.BAD_REQUEST,
        message: 'Không có file nào được gửi lên' });
    }


    const filename = req.file.filename;

    // const myHost = '100.87.123.77';
    // const myPort = '8080';
    // const fileUrl = `http://${myHost}:${myPort}/uploads/${filename}`
    const fileUrl = `https://0mxrrtbd-8080.asse.devtunnels.ms/uploads/${filename}`

    logger.info(`Đã lưu file [${filename}] vào thư mục /uploads`);


    const logDetails = `Người dùng [${actor} (Role: ${actorRole})] đã cập nhật bản firmware [${filename}] cho cảm biến.`
    
    const newAuditLog = new Audit({
      actor: actor,
      event: AuditEvent.UPDATE_FIRMWARE,
      details: logDetails
    })
    await newAuditLog.save()

    const topic = Topic.UPLOAD_FILE_FIRMWARE // topic '/upload/firmware'
    const payload = JSON.stringify({
      url: fileUrl
    });
    
    mqttClient.publish(topic, payload, (err) => {
      if (err) {
        logger.error(`MQTT publish lỗi: ${err}`)
      } else {
        logger.info(`Đã gửi Firmware URL tới topic '${topic}'. Payload: ${payload}'`)
      }
    })

    return res.status(HTTPStatus.OK).json({
      status: HTTPStatus.OK,
      message: 'Upload file firmware thành công',
      url: fileUrl,
      fileName: filename
    });
  } catch (error) {
    logger.error('Lỗi upload:', error);
    return res.status(HTTPStatus.INTERNAL_SERVER_ERROR).json({
      status: HTTPStatus.INTERNAL_SERVER_ERROR,
      message: 'Lỗi server' 
    });
  }
};