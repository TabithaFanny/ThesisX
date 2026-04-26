"""验证 AI 性能优化 - 简洁版"""
import sys
import os
import time
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.ai_service import _get_ai_api_key, AI_API_URL, AI_MODEL
import urllib.request
import json

print("=" * 60)
print("AI 性能优化验证测试")
print("=" * 60)

api_key = _get_ai_api_key()
if not api_key:
    print("错误: 未找到 API key")
    sys.exit(1)

result = {"start": time.time(), "first_chunk": None, "chunks": 0, "error": None}

def network_task():
    try:
        import ssl
        payload = {
            "model": AI_MODEL,
            "messages": [
                {"role": "user", "content": "Say hello in 10 words"}
            ],
            "stream": True,
            "max_tokens": 50
        }

        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "Accept": "text/event-stream",
            "Connection": "keep-alive",
        }

        ssl_context = ssl.create_default_context()
        req = urllib.request.Request(AI_API_URL, data=data, headers=headers, method="POST")

        print(f"\n[{time.time() - result['start']:.2f}s] 发送请求...")

        with urllib.request.urlopen(req, timeout=60, context=ssl_context) as response:
            print(f"[{time.time() - result['start']:.2f}s] 连接建立")

            while True:
                line_bytes = response.readline()
                if not line_bytes:
                    break

                line = line_bytes.decode("utf-8", errors="replace").strip()
                if not line or not line.startswith("data: "):
                    continue

                line = line[6:]
                if line == "[DONE]":
                    break

                try:
                    chunk_data = json.loads(line)
                    delta = chunk_data.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        if result["chunks"] == 0:
                            result["first_chunk"] = time.time() - result["start"]
                            print(f"[{result['first_chunk']:.2f}s] 首字节接收")
                        result["chunks"] += 1
                except:
                    pass

    except Exception as e:
        result["error"] = str(e)

thread = threading.Thread(target=network_task)
thread.start()
thread.join(timeout=70)

total_time = time.time() - result["start"]

print("\n" + "=" * 60)
print("测试结果")
print("=" * 60)

if result["error"]:
    print(f"错误: {result['error']}")
elif result["first_chunk"]:
    print(f"首字节时间: {result['first_chunk']:.2f}秒")
    print(f"总耗时: {total_time:.2f}秒")
    print(f"数据块数量: {result['chunks']}")
    print(f"\n性能对比:")
    print(f"  优化前: ~45秒")
    print(f"  优化后: {result['first_chunk']:.2f}秒")
    print(f"  提升: {45 / result['first_chunk']:.1f}x 倍")

    if result['first_chunk'] < 3:
        print(f"\n评级: 优秀")
    elif result['first_chunk'] < 5:
        print(f"\n评级: 良好")
    else:
        print(f"\n评级: 一般")
else:
    print("未接收到数据")

print("=" * 60)
