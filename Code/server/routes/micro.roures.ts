import express from 'express'
import { authenticateToken } from '../middlewares/user.middleware'
import { changePumpStatus } from '../controllers/micro.controller'

/**
 * @route   POST /api/micro-controller/change-status
 * @desc    Bật/tắt bơm thủ công
 * @access  Private (Cần Token)
 */

export const microRouter = express.Router()

microRouter.use(authenticateToken)

microRouter.post('/change-status',changePumpStatus)