import mongoose from 'mongoose'
const { Schema } = mongoose

export enum UserRole {
  USER = 'USER',
  ADMIN = 'ADMIN'
}

const UserSchema = new Schema(
  {
    username: {
      type: String,
      required: true,
      unique: true,
      trim: true,
      minlength: 3
    },
    password: {
      type: String,
      required: true
    },
    email: {
      type: String,
      required: true,
      trim: true,
      unique: true,
      validate: {
        validator: function(v: string) {
          // Trả về true nếu email kết thúc bằng @gmail.com
          return v.endsWith('@gmail.com');
        },
        message: (props: { value: string }) => `${props.value} không phải là một địa chỉ Gmail hợp lệ! Vui lòng chỉ sử dụng Gmail.`
      }
    },
    fullName: {
        type: String,
        required: true
    },
    address: {
        type: String,
        required: true
    },
    phoneNumber: {
        type: String,
        required: true
    },
    role: {
      type: String,
      enum: Object.values(UserRole),
      default: UserRole.USER
    }
  },
)

const User = mongoose.model('User', UserSchema)
export default User
