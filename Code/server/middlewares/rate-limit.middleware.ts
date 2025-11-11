import rateLimit from 'express-rate-limit';

const limiter = rateLimit({
  windowMs: 1 * 60 * 1000, 
  max: 60,
  message: 'Đã gửi quá nhiều yêu cầu, vui lòng thử lại sau 1 phút',
  standardHeaders: true, 
  legacyHeaders: false,
});

export {limiter}
