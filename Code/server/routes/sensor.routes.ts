import express from 'express';
import { getSensorData } from '../controllers/sensor.controller';
import { authenticateToken } from '../middlewares/user.middleware';

export const sensorRouter = express.Router();
sensorRouter.use(authenticateToken)
sensorRouter.get('/get-data', getSensorData);
