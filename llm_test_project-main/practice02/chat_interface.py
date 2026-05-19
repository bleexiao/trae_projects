#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import http.client
from urllib.parse import urlparse
from dotenv import load_dotenv
import time
import sys

# 强制设置UTF-8编码
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 加载 .env
load_dotenv()

BASE_URL = os.getenv("BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME")
API_TOKEN = os.getenv("API_TOKEN")

# 清理和验证 BASE_URL
if BASE_URL:
    # 移除可能的反引号或其他特殊字符
    BASE_URL = BASE_URL.strip('`\'"')
    # 确保使用 HTTPS
    if BASE_URL.startswith('http://'):
        BASE_URL = BASE_URL.replace('http://', 'https://')
        print("警告：自动将 HTTP 转换为 HTTPS")

print(f"BASE_URL = {BASE_URL}")
print(f"MODEL_NAME = {MODEL_NAME}")
print(f"API_TOKEN = {API_TOKEN}")

if not BASE_URL or not MODEL_NAME:
    print("错误：请在 .env 文件中正确配置 BASE_URL 和 MODEL_NAME")
    exit(1)

if not BASE_URL.startswith('https://'):
    print("错误：BASE_URL 必须使用 HTTPS 协议")
    exit(1)

def get_connection():
    parsed = urlparse(BASE_URL)
    print(f"解析后的 URL: scheme={parsed.scheme}, netloc={parsed.netloc}")
    
    if parsed.scheme == "http":
        print("警告：使用 HTTP 连接，建议使用 HTTPS")
        return http.client.HTTPConnection(parsed.netloc, timeout=30)
    else:
        return http.client.HTTPSConnection(parsed.netloc, timeout=30)

def send_request(messages, stream=True):
    conn = get_connection()
    
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 1.0,
        "stream": stream
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_TOKEN}",
        "Accept": "application/json",
        "HTTP-Referer": "https://openrouter.ai",
        "X-Title": "LLM Chat Client"
    }

    # 从BASE_URL中解析路径，避免路径重复
    parsed = urlparse(BASE_URL)
    api_path = parsed.path if parsed.path else "/v1/chat/completions"
    full_url = parsed.scheme + "://" + parsed.netloc + api_path
    print(f"发送请求到: {full_url}")
    print(f"使用模型: {MODEL_NAME}")
    print(f"流式模式: {stream}")
    
    try:
        conn.request("POST", api_path, body=json.dumps(payload), headers=headers)
        response = conn.getresponse()
        print(f"响应状态码: {response.status}")
        
        if response.status != 200:
            response_body = response.read().decode('utf-8', errors='ignore')
            print(f"响应内容: {response_body}")
            # 尝试解析JSON错误信息
            try:
                error_data = json.loads(response_body)
                if 'error' in error_data:
                    print(f"API错误: {error_data['error']}")
            except:
                pass
            return None
        
        return response
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
        try:
            conn.close()
        except:
            pass
        return None

def handle_streaming_response(response):
    if not response:
        print("响应为空")
        return ""
    
    full_response = ""
    print("\nAI: ", end="", flush=True)
    
    try:
        # 先读取一小部分数据检查响应格式
        first_chunk = response.read(1024)
        if not first_chunk:
            print("\n响应内容为空")
            return ""
        
        # 检查是否是HTML响应（错误页面）
        first_text = first_chunk.decode('utf-8', errors='ignore')
        if '<html' in first_text.lower() or '<!doctype' in first_text.lower():
            print("\n收到HTML响应，可能是错误页面")
            print(f"响应内容: {first_text[:500]}")
            return ""
        
        # 处理流式响应
        buffer = first_text
        while True:
            # 处理缓冲区中的数据
            lines = buffer.split('\n')
            buffer = lines.pop() if lines else ""  # 保留最后一行（可能不完整）
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('data:'):
                    data_part = line[5:].strip()
                    if data_part == '[DONE]':
                        break
                    try:
                        data = json.loads(data_part)
                        if 'choices' in data and data['choices']:
                            delta = data['choices'][0].get('delta', {})
                            if 'content' in delta:
                                content = delta['content']
                                print(content, end="", flush=True)
                                full_response += content
                    except json.JSONDecodeError:
                        pass
            
            # 读取更多数据
            if '[DONE]' in buffer:
                break
                
            chunk = response.read(1024)
            if not chunk:
                break
            buffer += chunk.decode('utf-8', errors='ignore')
    
    except Exception as e:
        print(f"\n处理响应时发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        response.close()
    
    print()  # 换行
    return full_response

def main():
    print("=====================================")
    print("         终端聊天界面")
    print("=====================================")
    print("输入消息与AI对话，按Ctrl+C退出")
    print("=====================================\n")
    
    # 初始化聊天历史
    chat_history = []
    
    try:
        while True:
            # 获取用户输入
            user_input = input("你: ")
            
            # 添加用户消息到历史
            chat_history.append({"role": "user", "content": user_input})
            
            # 发送请求并处理流式响应
            response = send_request(chat_history)
            if response:
                ai_response = handle_streaming_response(response)
                # 添加AI回复到历史
                chat_history.append({"role": "assistant", "content": ai_response})
            
            print()  # 空行分隔
    
    except KeyboardInterrupt:
        print("\n\n聊天结束，再见！")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    main()