# sjc.widget

An Übersicht widget that displays the SJC gold price per tael along with the premium difference compared to the international spot gold price (excluding taxes and fees).

The widget also displays the international spot gold price and the USD/VND exchange rate at the time the data is fetched.

Data is automatically refreshed every 5 minutes. You can adjust this interval in the code, but a refresh interval shorter than 5 minutes is not recommended for two main reasons: to avoid being blocked by data provider servers and because SJC gold prices do not change very frequently.


Một widget Übersicht hiển thị giá vàng SJC 1 lượng kèm chênh lệch với giá giao ngay quốc tế (chưa bao gồm thuế phí). Widget cũng hiển thị giá giao ngay, tỉ giá USD/VND ngay thời điểm nạp dữ liệu. Dữ liệu sẽ được nạp lại mỗi 5 phút. Bạn có thể chỉnh trong mã, nhưng khuyến nghị không nên dưới 5 phút vì hai lí do chính: tránh bị các server cung cấp dữ liệu chặn và giá SJC cũng không thay đổi quá thường xuyên.

## Screenshot

![SJC Widget](screenshot.png)

## Installation (Cài đặt)

- Download and extract this repository.
- Copy `sjc.widget` to your Übersicht widgets directory.
- Refresh Übersicht.
- 
- Download repository và giải nén.
- Copy sjc.widget đến thư mục widget của Übersicht.
- Refresh Übersicht.

## Requirements (Yêu cầu trước khi cài đặt/chạy)

Before installation and running, make sure you have:

- macOS 12+
- [Übersicht](https://github.com/felixhageloh/uebersicht)
- Python 3 installed on your Mac. If you do not have Python installed, search online for instructions on installing Python on macOS. It is recommended to download and install Python from [python.org](https://www.python.org/).
- Check whether Python is already installed:

- macOS 12+
- [Übersicht](https://github.com/felixhageloh/uebersicht)
- Máy bạn phải có python3. Hãy tra Google cách cài python lên Mac nếu chưa có. Khuyến nghị download cài từ python.org.
- Kiểm tra xem máy đã có python chưa:
  
```bash
python3 --version
```

- Then install the required Python dependency:
  
- Sau đó, cài thêm thư viện sau:

```bash
python3 -m pip install --upgrade curl_cffi
```
