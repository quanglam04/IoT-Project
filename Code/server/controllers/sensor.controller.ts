import { Request, Response } from "express";
import HTTPStatus from "../shared/constants/httpStatus";
import logger from "../utils/log";
import SensorData from "../models/SensorData";

const saveSensorData = async (req: Request, res: Response) => {
    try {
        const {temperature, humidity, light, soilMoisture, timestamp} = req.body
        const newData = new SensorData({
            temperature,
            humidity,
            light,
            soilMoisture,
            timestamp
        });

        const saveData = await newData.save();

        logger.info(`Đã lưu dữ liệu từ cảm biến: mã ${saveData._id}`)
        
        return res.status(HTTPStatus.CREATED).json({
            status: HTTPStatus.CREATED,
            message: 'Đã lưu dữ liệu thành công',
            data: saveData
        })
    } catch (error : any) {
        logger.error('Lỗi khi xử lý lưu dữ liệu sensor: ', error)

        return res.status(HTTPStatus.BAD_REQUEST).json({
            status: HTTPStatus.BAD_REQUEST,
            message: 'Lỗi khi lưu dữ liệu',
        })
    }
}

export {saveSensorData}
