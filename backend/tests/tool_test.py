import bcrypt

# 密文生成
salt  = bcrypt.gensalt(rounds=12)   # 随机 salt
hash  = bcrypt.hashpw("123456".encode(), salt)
print(hash.decode())

print(f"第一次测试：{bcrypt.checkpw("123456".encode(), hash)}")

print(f"第二次测试：{bcrypt.checkpw("12345678".encode(), hash)}")