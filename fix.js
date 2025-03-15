const fs = require('fs');

// Đọc file accounts.json
fs.readFile('accounts.json', 'utf8', (err, data) => {
  if (err) {
    console.error('Lỗi đọc file:', err);
    return;
  }

  try {
    // Chuyển đổi dữ liệu JSON thành đối tượng
    const accounts = JSON.parse(data);

    // Đổi giá trị deviceHash thành int
    accounts.forEach(account => {
      account.deviceHash = account.deviceHash.map(hash => parseInt(hash, 10));
    });

    // Ghi lại dữ liệu đã chỉnh sửa vào file
    fs.writeFile('accounts.json', JSON.stringify(accounts, null, 2), (err) => {
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

