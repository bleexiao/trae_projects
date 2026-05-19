#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import http.client
from urllib.parse import urlparse
from dotenv import load_dotenv
import io
import sys

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

# 技能相关函数
def list_available_skills():
    """读取技能列表，提取每个技能的name和description"""
    # 获取项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    while not os.path.exists(os.path.join(project_root, ".agents")):
        project_root = os.path.dirname(project_root)
    skills_dir = os.path.join(project_root, ".agents", "skills")
    skills = []
    
    print(f"技能目录: {skills_dir}")
    print(f"目录是否存在: {os.path.exists(skills_dir)}")
    
    if os.path.exists(skills_dir):
        print(f"目录内容: {os.listdir(skills_dir)}")
        for skill_name in os.listdir(skills_dir):
            skill_path = os.path.join(skills_dir, skill_name)
            print(f"检查: {skill_path}, 是目录: {os.path.isdir(skill_path)}")
            if os.path.isdir(skill_path):
                skill_file = os.path.join(skill_path, "SKILL.md")
                print(f"技能文件: {skill_file}, 存在: {os.path.exists(skill_file)}")
                if os.path.exists(skill_file):
                    try:
                        with open(skill_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        print(f"文件内容前100字符: {content[:100]}...")
                        # 提取YAML front matter
                        if content.startswith('---'):
                            front_matter_end = content.find('---', 3)
                            if front_matter_end != -1:
                                front_matter = content[3:front_matter_end].strip()
                                print(f"Front matter: {front_matter}")
                                # 解析name和description
                                name = ""
                                description = ""
                                for line in front_matter.split('\n'):
                                    line = line.strip()
                                    if line.startswith('name:'):
                                        name = line[5:].strip().strip('"')
                                    elif line.startswith('description:'):
                                        description = line[12:].strip().strip('"')
                                print(f"提取的技能: name={name}, description={description}")
                                if name:
                                    skills.append({"name": name, "description": description})
                    except Exception as e:
                        print(f"读取技能文件时出错: {e}")
    
    print(f"最终技能列表: {skills}")
    return {"skills": skills}

def load_skill_content(skill_name):
    """加载技能的正文内容"""
    # 获取项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    while not os.path.exists(os.path.join(project_root, ".agents")):
        project_root = os.path.dirname(project_root)
    skill_path = os.path.join(project_root, ".agents", "skills", skill_name)
    skill_file = os.path.join(skill_path, "SKILL.md")
    
    print(f"加载技能: {skill_name}")
    print(f"技能文件路径: {skill_file}")
    print(f"文件是否存在: {os.path.exists(skill_file)}")
    
    if os.path.exists(skill_file):
        try:
            with open(skill_file, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"文件内容前100字符: {content[:100]}...")
            # 提取正文内容（YAML front matter之后的部分）
            if content.startswith('---'):
                front_matter_end = content.find('---', 3)
                if front_matter_end != -1:
                    body = content[front_matter_end + 3:].strip()
                    print(f"提取的正文前100字符: {body[:100]}...")
                    return body
            return content
        except Exception as e:
            print(f"加载技能内容时出错: {e}")
            return ""
    return ""

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

# 工具定义
tools = [
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
    }
]

def get_connection():
    parsed = urlparse(BASE_URL)
    if parsed.scheme == "http":
        return http.client.HTTPConnection(parsed.netloc)
    else:
        return http.client.HTTPSConnection(parsed.netloc)

def send_request(messages, tools=None, tool_choice="auto"):
    conn = get_connection()
    
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
        conn.request("POST", "/v1/chat/completions", body=json.dumps(payload), headers=headers)
        resp = conn.getresponse()
        data = json.loads(resp.read().decode())
        return data
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
    
    if function_name == "create_file":
        return create_file(arguments['directory'], arguments['filename'], arguments['content'])
    else:
        return {"status": "error", "message": f"未知工具: {function_name}"}

def main():
    print("=====================================")
    print("         智能助手系统")
    print("=====================================")
    print("输入请求，系统将通过LLM调用相应工具")
    print("当需要使用技能时，系统会自动加载技能内容")
    print("=====================================\n")
    
    # 读取技能列表
    skills_info = list_available_skills()
    skills_json = json.dumps(skills_info, ensure_ascii=False, indent=2)
    
    # 系统提示词
    system_prompt = """你是一个智能助手，必须严格按照指令执行任务，不得有任何偏差。

工具列表：
1. create_file(directory, filename, content) - 在某个目录下新建1个文件，并且写入内容

当用户输入"中秋节放假通知"时，你必须：
1. 生成一个中秋节放假通知，严格按照以下要求：
   - 开头必须是"xx部关于2024年中秋节放假安排的通知"
   - 不能使用其他部门名称，必须使用"xx部"
   - 内容包括放假时间、注意事项等
   - 保持正式的语气和格式
2. 调用create_file工具将通知内容保存到文件中
3. 文件名必须是"中秋节放假通知.txt"
4. 目录参数使用"."（当前目录）

请立即执行，不要有任何犹豫或修改。"""
    
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