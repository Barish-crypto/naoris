import json
import random
import re

# Đọc nội dung từ file accounts.txt
with open('accounts.txt', 'r', encoding='utf-8') as f:
    txt_content = f.read()

# Dùng regex để trích xuất các wallet address
wallet_addresses = re.findall(r'0x[a-fA-F0-9]{40}', txt_content)

# Hàm tạo danh sách deviceHash ngẫu nhiên
def generate_device_hashes(count=2):
    return [random.randint(1000000000, 9999999999) for _ in range(count)]

# Tạo danh sách JSON đầu ra
new_data = []
for address in wallet_addresses:
    # Tùy bạn muốn bao nhiêu deviceHash mỗi ví (random hoặc cố định)
    num_hashes = random.randint(2, 5)  # Mỗi ví sẽ có từ 2 đến 5 deviceHash
    new_data.append({
        "walletAddress": address,
        "deviceHashes": generate_device_hashes(num_hashes)
    })

# Ghi ra file accounts.json
with open('accounts.json', 'w', encoding='utf-8') as f:
    json.dump(new_data, f, indent=2)

print("✅ Đã cập nhật accounts.json với nhiều deviceHash mỗi ví.")
