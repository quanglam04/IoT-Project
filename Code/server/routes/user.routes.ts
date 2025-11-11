import express from 'express'
import { exportESP32Report, getCountDevice, getListUser, getLogs, login } from '../controllers/user.controller'
import { authenticateToken } from '../middlewares/user.middleware'

export const userRouter = express.Router()

userRouter.post('/login', login)

userRouter.use(authenticateToken)
userRouter.get('/list', getListUser)
userRouter.get('/count-device', getCountDevice)
userRouter.get('/get-logs', getLogs)
userRouter.get('/reports/esp/export', exportESP32Report)