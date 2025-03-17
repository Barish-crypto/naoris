const fs = require('fs');

// Đọc file config.json
fs.readFile('accounts.json', 'utf8', (err, data) => {
  if (err) {
    console.error('Lỗi đọc file:', err);
    return;
  }

  try {
    // Chuyển đổi dữ liệu JSON thành đối tượng
    const config = JSON.parse(data);

    // Lọc ra walletAddress và deviceHash
    const result = config.map(item => item.walletAddress);

    // Hiển thị kết quả
    console.log(result[0]);

    // Bạn có thể ghi kết quả vào file nếu muốn
    fs.writeFile('output.txt', result[0], (err) => {
      if (err) {
        console.error('Lỗi ghi file:', err);
      } else {
        console.log('File đã được ghi!');
      }
    });

  } catch (error) {
    console.error('Lỗi xử lý JSON:', error);
  }
});

