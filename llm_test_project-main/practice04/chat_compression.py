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

print(f"BASE_URL = {BASE_URL}")
print(f"MODEL_NAME = {MODEL_NAME}")
print(f"API_TOKEN = {API_TOKEN}")

if not BASE_URL or not MODEL_NAME:
    print("错误：请在 .env 文件中正确配置 BASE_URL 和 MODEL_NAME")
    exit(1)

def get_connection():
    parsed = urlparse(BASE_URL)
    if parsed.scheme == "http":
        return http.client.HTTPConnection(parsed.netloc)
    else:
        return http.client.HTTPSConnection(parsed.netloc)

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
        "Authorization": f"Bearer {API_TOKEN}"
    }

    try:
        conn.request("POST", "/v1/chat/completions", body=json.dumps(payload), headers=headers)
        return conn.getresponse()
    except Exception as e:
        print(f"发生错误: {e}")
        conn.close()
        return None

def handle_streaming_response(response):
    if not response:
        return ""
    
    full_response = ""
    print("\nAI: ", end="")
    
    try:
        while True:
            chunk = response.read(1024)
            if not chunk:
                break
            
            chunk_str = chunk.decode('utf-8')
            lines = chunk_str.split('\n')
            
            for line in lines:
                line = line.strip()
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
    finally:
        response.close()
    
    print()  # 换行
    return full_response

def handle_non_streaming_response(response):
    if not response:
        return ""
    
    try:
        data = json.loads(response.read().decode())
        if 'choices' in data and data['choices']:
            return data['choices'][0]['message']['content']
    except Exception as e:
        print(f"处理响应时发生错误: {e}")
    finally:
        response.close()
    
    return ""

def calculate_context_length(messages):
    """计算聊天上下文的总长度"""
    total_length = 0
    for message in messages:
        if 'content' in message:
            total_length += len(message['content'])
    return total_length

def should_compress_chat(chat_history):
    """判断是否需要压缩聊天记录"""
    # 检查聊天轮数（每2条消息为1轮）
    num_rounds = len(chat_history) // 2
    # 检查上下文长度
    context_length = calculate_context_length(chat_history)
    
    return num_rounds >= 5 or context_length >= 3000

def compress_chat_history(chat_history):
    """压缩聊天历史记录"""
    print("\n检测到聊天记录过长，正在压缩...")
    
    # 计算分割点（前70%压缩，后30%保留）
    total_messages = len(chat_history)
    split_point = int(total_messages * 0.7)
    
    # 提取需要压缩的部分和需要保留的部分
    compress_part = chat_history[:split_point]
    keep_part = chat_history[split_point:]
    
    # 生成压缩提示
    compression_prompt = """请将以下聊天记录压缩成简洁的摘要，保留关键信息和对话脉络：

"""
    
    # 构建压缩请求消息
    compression_messages = [
        {"role": "system", "content": "你是一个专业的对话摘要助手，擅长将长对话压缩为简洁的摘要。"},
        {"role": "user", "content": compression_prompt + json.dumps(compress_part, ensure_ascii=False)}
    ]
    
    # 发送压缩请求
    print("正在生成聊天摘要...")
    response = send_request(compression_messages, stream=False)
    summary = handle_non_streaming_response(response)
    
    if summary:
        # 构建新的聊天历史：系统摘要 + 保留的部分
        new_chat_history = [
            {"role": "system", "content": f"聊天历史摘要：{summary}"}
        ] + keep_part
        
        print(f"聊天记录压缩完成，原长度: {len(chat_history)}条消息，压缩后: {len(new_chat_history)}条消息")
        return new_chat_history
    else:
        print("压缩失败，保持原聊天记录")
        return chat_history

def main():
    print("=====================================")
    print("         聊天记录压缩系统")
    print("=====================================")
    print("输入消息与AI对话，按Ctrl+C退出")
    print("系统会自动压缩过长的聊天记录")
    print("=====================================\n")
    
    # 初始化聊天历史
    chat_history = []
    
    try:
        while True:
            # 检查是否需要压缩
            if should_compress_chat(chat_history):
                chat_history = compress_chat_history(chat_history)
            
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