import os
import json
import http.client
from urllib.parse import urlparse
from dotenv import load_dotenv

# 加载 .env
load_dotenv()

BASE_URL = os.getenv("BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME")
API_TOKEN = os.getenv("API_TOKEN")

print(f"BASE_URL = {BASE_URL}")
print(f"MODEL_NAME = {MODEL_NAME}")
print(f"API_TOKEN = {'*' * len(API_TOKEN) if API_TOKEN else None}")

def validate_config():
    """验证配置是否正确"""
    if not BASE_URL:
        print("错误：请在 .env 文件中配置 BASE_URL")
        return False
    if not MODEL_NAME:
        print("错误：请在 .env 文件中配置 MODEL_NAME")
        return False
    
    parsed = urlparse(BASE_URL)
    if not parsed.scheme or not parsed.netloc:
        print(f"错误：BASE_URL 格式不正确: {BASE_URL}")
        return False
    
    if parsed.scheme not in ("http", "https"):
        print(f"错误：BASE_URL 必须使用 HTTP 或 HTTPS 协议")
        return False
    
    return True

def get_api_path():
    """从BASE_URL中解析API路径，避免路径重复"""
    parsed = urlparse(BASE_URL)
    return parsed.path if parsed.path else "/v1/chat/completions"

def main():
    if not validate_config():
        exit(1)
    
    parsed = urlparse(BASE_URL)
    conn = None
    
    try:
        # 创建连接
        if parsed.scheme == "http":
            conn = http.client.HTTPConnection(parsed.netloc, timeout=30)
        else:
            conn = http.client.HTTPSConnection(parsed.netloc, timeout=30)

        # 构建请求
        api_path = get_api_path()
        payload = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": "user:你好，我叫肖中林。\nai:您好，肖中林先生！很高兴能为您服务。请问有什么我可以帮您解答或处理的吗？或者，如果您想聊聊最近的兴趣爱好、工作或者其他话题，也欢迎与我说说。\n请问我叫什么名字？"}],
            "temperature": 1.5
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_TOKEN}"
        }

        print(f"正在发送请求到: {parsed.scheme}://{parsed.netloc}{api_path}")
        conn.request("POST", api_path, body=json.dumps(payload, ensure_ascii=False), headers=headers)
        resp = conn.getresponse()
        print(f"响应状态码: {resp.status}")

        # 处理响应
        data = json.loads(resp.read().decode('utf-8'))
        
        if 'choices' in data and data['choices']:
            print("模型回答：")
            print(data['choices'][0]['message']['content'])
        else:
            print(f"响应格式异常: {json.dumps(data, ensure_ascii=False, indent=2)}")

    except http.client.HTTPException as e:
        print(f"HTTP 错误: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON 解析错误: {e}")
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        if conn:
            conn.close()
            print("连接已关闭")

if __name__ == "__main__":
    main()