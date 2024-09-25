**CanTpReceive.py**
file chứa class CanTpReceive để khởi tạo Receiver. Trong class chứa hàm receive_message() dùng để nhận bản tin. Các hàm với tên bắt đầu _{name}_ là các subfunction bổ trợ cho receive_message(). Chương trình nhận bản tin thực hiện theo specification của CanTP, khi có bản tin được nhận sẽ bắt đầu một chu xử lý nhận tương ứng. Chu trình nhận dữ liệu xử lý thành công sẽ in ra màn hình kết quả bản tin nhận được.

**CanTpTransmit.py**
File chứa class CanTpTransmit để khởi tạo Sender. Trong class chứa hàm  send_message() dùng để gửi bản tin. Các hàm với tên bắt đầu _{name}_ là các subfunction bổ trợ cho send_message(). Chương trình gửi bản tin được thực hiện theo specification của CanTP. Khi bắt đầu gửi bản tin, bản tin sẽ được phân tích cùng với cài đặt của người dùng để lựa chọn phương thức gửi tương ứng (Can Classic hoặc CanFD, Single Frame hoặc Multiple Frame,...).

**Receiver.py**
File được import CanTpReceive.py. Chương trình khởi tạo bộ Receiver với các thông số tương ứng và chạy chương trình nhận receive_message(). File được sử dụng để chạy với phần cứng thực tế.

**Sender.py**
File được import CanTpTransmit.py. Chương trình khởi tạo bộ Sender với các thông số tương ứng và chạy chương trình gửi send_message(). File được sử dụng để chạy với phần cứng thực tế.

**Simulation.py**
File được import CanTpReceive.py và CanTpTransmit.py. Chương trình được thiết kế cho việc chạy mô phỏng việc truyền và nhận với bus ảo. 