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
