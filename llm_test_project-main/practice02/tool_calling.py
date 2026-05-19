#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import http.client
from urllib.parse import urlparse
from dotenv import load_dotenv
import io
import sys
import requests

# 强制设置UTF-8编码
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

# 工具函数实现
def list_files(directory):
    """列出某个目录下有哪些文件（包括文件的基本属性、大小等信息）"""
    try:
        files_info = []
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                file_size = os.path.getsize(filepath)
                file_mtime = os.path.getmtime(filepath)
                files_info.append({
                    "name": filename,
                    "size": file_size,
                    "path": filepath,
                    "last_modified": file_mtime
                })
        return {
            "status": "success",
            "files": files_info
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def rename_file(directory, old_name, new_name):
    """修改某个目录下某个文件的名字"""
    try:
        old_path = os.path.join(directory, old_name)
        new_path = os.path.join(directory, new_name)
        os.rename(old_path, new_path)
        return {
            "status": "success",
            "message": f"文件已重命名: {old_name} -> {new_name}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def delete_file(directory, filename):
    """删除某个目录下的某个文件"""
    try:
        filepath = os.path.join(directory, filename)
        os.remove(filepath)
        return {
            "status": "success",
            "message": f"文件已删除: {filename}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def create_file(directory, filename, content):
    """在某个目录下新建1个文件，并且写入内容"""
    try:
        filepath = os.path.join(directory, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return {
            "status": "success",
            "message": f"文件已创建: {filename}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def read_file(directory, filename):
    """读取某个目录下的某个文件并返回内容摘要"""
    try:
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        # 限制返回内容长度，只返回前1000个字符作为摘要
        summary = content[:1000] + ("..." if len(content) > 1000 else "")
        return {
            "status": "success",
            "content": summary,
            "full_length": len(content),
            "message": f"返回文件内容摘要（前{len(summary)}字符）"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def curl_request(url):
    """通过curl访问网页并返回网页内容"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()  # 检查HTTP错误
        # 限制返回内容长度，只返回前2000个字符
        content = response.text
        return {
            "status": "success",
            "content": content,
            "full_length": len(response.text),
            "status_code": response.status_code,
            "url": url,
            "message": f"返回完整网页内容，长度：{len(content)}字符"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

# 工具定义
tools = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "列出某个目录下有哪些文件（包括文件的基本属性、大小等信息）",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "要列出文件的目录路径"
                    }
                },
                "required": ["directory"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "rename_file",
            "description": "修改某个目录下某个文件的名字",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "文件所在的目录路径"
                    },
                    "old_name": {
                        "type": "string",
                        "description": "原文件名"
                    },
                    "new_name": {
                        "type": "string",
                        "description": "新文件名"
                    }
                },
                "required": ["directory", "old_name", "new_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "删除某个目录下的某个文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "文件所在的目录路径"
                    },
                    "filename": {
                        "type": "string",
                        "description": "要删除的文件名"
                    }
                },
                "required": ["directory", "filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "在某个目录下新建1个文件，并且写入内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "要创建文件的目录路径"
                    },
                    "filename": {
                        "type": "string",
                        "description": "要创建的文件名"
                    },
                    "content": {
                        "type": "string",
                        "description": "要写入文件的内容"
                    }
                },
                "required": ["directory", "filename", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取某个目录下的某个文件并返回内容摘要",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "文件所在的目录路径"
                    },
                    "filename": {
                        "type": "string",
                        "description": "要读取的文件名"
                    }
                },
                "required": ["directory", "filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "curl_request",
            "description": "通过curl访问网页并返回网页内容摘要",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "要访问的网页URL"
                    }
                },
                "required": ["url"]
            }
        }
    }
]

def get_connection():
    """创建新的HTTP/HTTPS连接"""
    parsed = urlparse(BASE_URL)
    if parsed.scheme == "http":
        return http.client.HTTPConnection(parsed.netloc, timeout=30)
    else:
        return http.client.HTTPSConnection(parsed.netloc, timeout=30)

def get_api_path():
    """从BASE_URL中解析API路径，避免路径重复"""
    parsed = urlparse(BASE_URL)
    return parsed.path if parsed.path else "/v1/chat/completions"

def send_request(messages, tools=None, tool_choice="auto"):
    conn = get_connection()
    api_path = get_api_path()
    
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 1.0
    }
    
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = tool_choice

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_TOKEN}"
    }

    try:
        conn.request("POST", api_path, body=json.dumps(payload, ensure_ascii=False), headers=headers)
        resp = conn.getresponse()
        data = json.loads(resp.read().decode('utf-8'))
        return data
    except http.client.HTTPException as e:
        print(f"HTTP 错误: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON 解析错误: {e}")
        return None
    except Exception as e:
        print(f"发生错误: {e}")
        return None
    finally:
        conn.close()

def handle_tool_calls(response):
    if not response or 'choices' not in response:
        return None, None
    
    choice = response['choices'][0]
    if 'tool_calls' in choice['message']:
        tool_calls = choice['message']['tool_calls']
        return choice['message'], tool_calls
    return choice['message'], None

def execute_tool_call(tool_call):
    function_name = tool_call['function']['name']
    arguments = json.loads(tool_call['function']['arguments'])
    
    if function_name == "list_files":
        return list_files(arguments['directory'])
    elif function_name == "rename_file":
        return rename_file(arguments['directory'], arguments['old_name'], arguments['new_name'])
    elif function_name == "delete_file":
        return delete_file(arguments['directory'], arguments['filename'])
    elif function_name == "create_file":
        return create_file(arguments['directory'], arguments['filename'], arguments['content'])
    elif function_name == "read_file":
        return read_file(arguments['directory'], arguments['filename'])
    elif function_name == "curl_request":
        return curl_request(arguments['url'])
    else:
        return {"status": "error", "message": f"未知工具: {function_name}"}

def main():
    print("=====================================")
    print("         工具调用系统")
    print("=====================================")
    print("输入请求，系统将通过LLM调用相应工具")
    print("=====================================\n")
    
    # 系统提示词
    system_prompt = """你是一个智能助手，拥有以下工具调用能力：

工具列表：
1. list_files(directory) - 列出某个目录下有哪些文件（包括文件的基本属性、大小等信息）
2. rename_file(directory, old_name, new_name) - 修改某个目录下某个文件的名字
3. delete_file(directory, filename) - 删除某个目录下的某个文件
4. create_file(directory, filename, content) - 在某个目录下新建1个文件，并且写入内容
5. read_file(directory, filename) - 读取某个目录下的某个文件并返回内容摘要
6. curl_request(url) - 通过curl访问网页并返回网页内容摘要

当用户请求需要使用这些工具时，请调用相应的工具并根据工具返回的结果为用户提供回答。对于read_file和curl_request返回的内容摘要，请基于摘要为用户提供总结性的回答，而不是直接照搬原文。"""
    
    # 初始化消息
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    try:
        while True:
            # 获取用户输入
            user_input = input("你: ")
            
            # 添加用户消息
            messages.append({"role": "user", "content": user_input})
            
            # 发送请求
            print("\n正在处理请求...")
            response = send_request(messages, tools)
            
            if response:
                # 处理响应
                message, tool_calls = handle_tool_calls(response)
                
                if tool_calls:
                    # 处理工具调用
                    for tool_call in tool_calls:
                        print(f"\n调用工具: {tool_call['function']['name']}")
                        tool_result = execute_tool_call(tool_call)
                        print(f"工具返回: {json.dumps(tool_result, ensure_ascii=False, indent=2)}")
                        
                        # 添加工具响应到消息
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call['id'],
                            "name": tool_call['function']['name'],
                            "content": json.dumps(tool_result, ensure_ascii=False)
                        })
                    
                    # 再次发送请求获取最终回答
                    final_response = send_request(messages, tools)
                    if final_response and 'choices' in final_response:
                        final_message = final_response['choices'][0]['message']
                        print("\nAI: " + final_message['content'])
                        messages.append(final_message)
                else:
                    # 直接回答
                    print("\nAI: " + message['content'])
                    messages.append(message)
            
            print()  # 空行分隔
    
    except KeyboardInterrupt:
        print("\n\n程序结束，再见！")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    main()