import 'dotenv/config';
import express from 'express';
import { connectDB } from './config/db.config';
import './models/SensorData';
import './models/Forecast';
import './models/Schedule';
import http from 'http';
import cors from 'cors';
import { startMqttSubscriptions } from './routes/mqtt.router';
import { createSocketServer } from './config/socket.config';
import { setupSocket } from './sockets';

const app = express();
const PORT = process.env.PORT || 5000;
app.use(
  cors({
    origin: process.env.ALLOW_ORIGIN
  })
);

app.use(express.json());

const httpServer = http.createServer(app)
export const io = createSocketServer(httpServer)

//set up server socket
setupSocket(io)

const startServer = async () => {
  await connectDB();
  
  startMqttSubscriptions();

  httpServer.listen(PORT, () => console.log(`Server & Socket đang chạy trên cổng ${PORT}`));
};

startServer();