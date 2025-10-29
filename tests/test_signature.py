import time
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.signature import generate_signature


if __name__ == "__main__":
    # 示例用法
    e_value = "requestId,eef12d6c-6dc9-47a0-aae8-b9f3454f98c5,timestamp,1761038714733,user_id,21ea9ec3-e492-4dbb-b522-fc0eaf64f0f6"
    t_value = "hi"
    # r_value = int(time.time() * 1000)
    r_value = 1761038714733
    result = generate_signature(e_value, t_value, r_value)
    print(f"生成的签名: {result['signature']}")
    print(f"时间戳: {result['timestamp']}")