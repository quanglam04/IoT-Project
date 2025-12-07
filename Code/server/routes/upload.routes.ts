import express from 'express';
import { authenticateToken } from '../middlewares/user.middleware';
import { uploadConfig, handleUpload } from '../controllers/upload.controller';
import { userRouter } from './user.routes';

export const uploadRouter = express.Router();
uploadRouter.use(authenticateToken)
uploadRouter.post('/', uploadConfig.single('file'), handleUpload);