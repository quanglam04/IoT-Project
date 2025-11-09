# API Design [UPDATE]

**1. Đăng nhập**
```
POST api/users/login

API này không check token ở middleware

Request Body {
	username
	password
}

Response {
	status: 200 (đây chỉ demo trường hợp thành công thôi nhé, mấy trường hợp thất bại trả về mã lỗi tương ứng)
	message: Đăng nhập thành công
	data: {
	access_token
	thông tin user (trừ mật khẩu)
	}
}
```

Cấu trúc Users trong DB sẽ là:
```
username: string
password: string
fullName: string
address: string
phoneNumber: string
role: kiểu enum với 2 giá trị là USER, ADMIN (cái này ko biết thì tra chat là ra)
```

Tạo sẵn 2 user trong db
```
username: trinhlam
password: 123456
fullName: Trịnh Quang Lâm
address: Hà Nội
phoneNumber: 0971624914
role: ADMIN

username: nhankien
password: 123456
fullName: Vũ Nhân Kiên
address: Hà Nội
phoneNumber: 0123456789
role: USER
```

FLOW: Khi login, bên backend trả về những thông tin như thế kia, bên frontend t sẽ check cái role. Nếu là admin thì sẽ cho full quyền luôn. Còn nếu user thì sẽ if else 1 số đoạn để nó không vào được.
 Thông tin payload trong jwt gồm có  `id,username,role` <br>


**2. Đếm số người dùng**
```
GET api/users/count
Có check token ở middleware trước khi xử lý nhé, và cái này chỉ có role ADMIN mới được gọi (trước khi xử lý đếm số người, check role trong payload xem nếu là ADMIN thì làm tiếp không thì thôi trả về mã lỗi dạng ko có quyền)

Request body {}

Response {
	status: 200
	message: Lấy số lượng user thành công
	data: {
	numberOfUsers
	}
}
```


**3. Đếm số thiết bị**
```
GET api/iot-device/count
Có check token ở middleware trước khi xử lý nhé, và cái này chỉ có role ADMIN mới được gọi (trước khi xử lý đếm số người, check role trong payload xem nếu là ADMIN thì làm tiếp không thì thôi trả về mã lỗi dạng ko có quyền)

Request body{}

Response {
	status: 200
	message: Lấy số lượng thiết bị iot thành công
	data: {
	numberOfIotDevice: 
	}
}