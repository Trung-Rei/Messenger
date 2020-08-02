# Messenger
## Ý tưởng
Sử dụng 2 socket thực hiện 2 chức năng chạy song song với nhau:
* S_SEND: Thực hiện nhiệm vụ nhận các tin nhắn và yêu cầu từ người dùng và gửi đến Server.
* S_RECV: Thực hiện nhiệm vụ nhận các tin nhắn và yêu cầu được gửi đến từ Server.

## Gửi và nhận tin nhắn
### Gửi
Định dạng thông điệp: **\<RoomName> MSG \<UserName> \<Message>**

Trong đó:
* **\<RoomName>** là tên mã phòng chat gửi tin nhắn
* **MSG** để nhận diện thông điệp là tin nhắn
* **\<UserName> \<Message>** là người gửi và tin nhắn

### Nhận
Định dạng thông điệp: **\<RoomName> MSG \<UserName> \<Message>**

Client nhận và đưa thông điệp đếp phòng chat tương ứng để hiển thị tin nhắn.

## Nhận thông báo
Định dạng thông điệp: **NOTI \<Notification>**

Trong đó:
* **NOTI** nhận diện thông điệp là thông báo
* **\<Notification>** là thông báo

Client nhận và hiển thị thông báo trong phòng chat chính.

## Tính năng phòng chat riêng tư
### Tạo phòng chat
1. Người dùng nhập **username** người cần chat và nhấn **Enter**: client gửi **username** đến Server để kiểm tra.

2. Server kiểm tra hợp lệ và tạo phòng chat gồm 2 client theo yêu cầu, sau đó gửi thông điệp tạo phòng đến cả 2 client.

3. Client nhận thông điệp tạo phòng chat và tạo cửa sổ chat riêng.

### Đóng phòng chat
1. Người dùng nhấn **X** để đóng cửa sổ chat. Client gửi thông điệp đóng cho server.
2.  Server đóng phòng chat và gửi lệnh đóng đến client còn lại.
3. Client đầu kia nhận lệnh và đóng cửa sổ phòng chat.

## Tính năng download và upload tập tin
Client và server khởi tạo 1 kết nối socket khác để truyền file.
