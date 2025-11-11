import { Response } from 'express'
import HTTPStatus from '../shared/constants/httpStatus'
import logger from '../utils/log'
import { AuthRequest } from '../shared/types/util.type'
import Audit, { AuditEvent } from '../models/Audit' // Import model Audit
import mqttClient from '../config/mqtt.config' // Import MQTT client
import * as jwt from 'jsonwebtoken'
import Topic from '../shared/constants/topic'
/**
 * Điều khiển bật/tắt bơm thủ công
 * API: POST /api/micro-controller/change-status
 */
export const changePumpStatus = async (req: AuthRequest, res: Response) => {
  const { currentStatus } = req.body 
  const actor = (req.user as jwt.JwtPayload).username
  const actorRole = (req.user as jwt.JwtPayload).role

  if (typeof currentStatus !== 'boolean') {
    return res.status(HTTPStatus.BAD_REQUEST).json({
      message: 'Trường "currentStatus" là bắt buộc và phải là kiểu boolean.'
    })
  }

  const newStatus = !currentStatus
  const newStatusString = newStatus ? 'ON' : 'OFF'
  
  try {
    // 1. Ghi log Audit (Yêu cầu của bạn)
    const logDetails = `Người dùng [${actor} (Role: ${actorRole})] thay đổi trạng thái bơm từ ${currentStatus ? 'ON' : 'OFF'} sang ${newStatusString}.`
    
    const newAuditLog = new Audit({
      actor: actor,
      event: AuditEvent.MANUAL_PUMP_CONTROL,
      details: logDetails
    })
    await newAuditLog.save()
    
    // Gửi lệnh cho Esp32 qua MQTT
    const topic = Topic.DEVICE_CONTROLLER_PUMP // cái này Esp32 cũng phải lắng nghe nhé
    const payload = newStatusString
    
    mqttClient.publish(topic, payload, (err) => {
      if (err) {
        logger.error(`MQTT publish lỗi: ${err}`)
      } else {
        logger.info(`Đã publish lệnh '${payload}' (điều khiển bơm) đến topic '${topic}'`)
      }
    })

    // trả về FE
    return res.status(HTTPStatus.OK).json({
      status: HTTPStatus.OK,
      message: `Đã gửi lệnh ${newStatusString} thành công.`,
      data: {
        newStatus: newStatus 
      }
    })

  } catch (error) {
    logger.error('Lỗi khi thay đổi trạng thái bơm:', error)
    return res.status(HTTPStatus.INTERNAL_SERVER_ERROR).json({
      status: HTTPStatus.INTERNAL_SERVER_ERROR,
      message: 'Lỗi server',
    })
  }
}