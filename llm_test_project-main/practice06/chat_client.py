#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import http.client
from urllib.parse import urlparse, quote
from dotenv import load_dotenv
import io
import sys
import re

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

# ==================== 链式调用上下文管理器 ====================
class ChainedCallContext:
    """链式调用上下文管理器，用于在多个工具之间传递数据和状态"""
    
    def __init__(self, max_iterations=10):
        self.max_iterations = max_iterations
        self.current_iteration = 0
        self.call_history = []  # 记录每一步的调用和结果
        self.variables = {}     # 存储中间变量供后续步骤使用
        self.user_request = ""  # 用户原始请求
        self.final_answer = ""  # 最终回答
    
    def add_call(self, tool_name, arguments, result):
        """添加工具调用记录"""
        self.call_history.append({
            "tool_name": tool_name,
            "arguments": arguments,
            "result": result,
            "iteration": self.current_iteration
        })
    
    def set_variable(self, name, value):
        """设置中间变量"""
        self.variables[name] = value
    
    def get_variable(self, name, default=None):
        """获取中间变量"""
        return self.variables.get(name, default)
    
    def increment_iteration(self):
        """增加迭代次数"""
        self.current_iteration += 1
    
    def should_continue(self):
        """检查是否应该继续迭代"""
        return self.current_iteration < self.max_iterations
    
    def get_summary(self):
        """获取调用历史摘要"""
        summary = []
        for call in self.call_history:
            summary.append({
                "工具": call["tool_name"],
                "参数": call["arguments"],
                "结果": str(call["result"])[:200] + "..." if len(str(call["result"])) > 200 else call["result"]
            })
        return summary

# ==================== 工具函数实现 ====================

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

def search_files(directory, keyword):
    """搜索目录下所有包含指定关键词的文件"""
    try:
        matching_files = []
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if keyword in content:
                            matching_files.append({
                                "name": filename,
                                "path": filepath,
                                "match_count": content.count(keyword)
                            })
                except:
                    continue
        return {
            "status": "success",
            "keyword": keyword,
            "matching_files": matching_files,
            "count": len(matching_files)
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

def create_file(directory=None, filename=None, content=None, path=None):
    """在某个目录下新建1个文件，并且写入内容"""
    try:
        # 支持多种参数格式
        if path:
            # 如果提供了完整路径
            directory = os.path.dirname(path)
            filename = os.path.basename(path)
            # 如果目录为空，使用当前目录
            if not directory:
                directory = '.'
        elif filename and not directory:
            # 如果只有文件名，使用当前目录
            directory = '.'
        
        # 确保目录存在
        os.makedirs(directory, exist_ok=True)
        
        filepath = os.path.join(directory, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return {
            "status": "success",
            "message": f"文件已创建: {filename}",
            "path": filepath
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
        # 限制返回内容长度，只返回前2000个字符作为摘要
        summary = content[:2000] + ("..." if len(content) > 2000 else "")
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

# 技能相关函数
def list_available_skills():
    """读取技能列表，提取每个技能的name和description"""
    project_root = os.path.dirname(os.path.abspath(__file__))
    while not os.path.exists(os.path.join(project_root, ".agents")):
        project_root = os.path.dirname(project_root)
    skills_dir = os.path.join(project_root, ".agents", "skills")
    skills = []
    
    print(f"技能目录: {skills_dir}")
    
    if os.path.exists(skills_dir):
        for skill_name in os.listdir(skills_dir):
            skill_path = os.path.join(skills_dir, skill_name)
            if os.path.isdir(skill_path):
                skill_file = os.path.join(skill_path, "SKILL.md")
                if os.path.exists(skill_file):
                    try:
                        with open(skill_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        if content.startswith('---'):
                            front_matter_end = content.find('---', 3)
                            if front_matter_end != -1:
                                front_matter = content[3:front_matter_end].strip()
                                name = ""
                                description = ""
                                for line in front_matter.split('\n'):
                                    line = line.strip()
                                    if line.startswith('name:'):
                                        name = line[5:].strip().strip('"')
                                    elif line.startswith('description:'):
                                        description = line[12:].strip().strip('"')
                                if name:
                                    skills.append({"name": name, "description": description})
                    except Exception as e:
                        print(f"读取技能文件时出错: {e}")
    
    print(f"最终技能列表: {skills}")
    return {"skills": skills}

def load_skill_content(skill_name):
    """加载技能的正文内容"""
    project_root = os.path.dirname(os.path.abspath(__file__))
    while not os.path.exists(os.path.join(project_root, ".agents")):
        project_root = os.path.dirname(project_root)
    skill_path = os.path.join(project_root, ".agents", "skills", skill_name)
    skill_file = os.path.join(skill_path, "SKILL.md")
    
    print(f"加载技能: {skill_name}")
    print(f"技能文件路径: {skill_file}")
    
    if os.path.exists(skill_file):
        try:
            with open(skill_file, 'r', encoding='utf-8') as f:
                content = f.read()
            if content.startswith('---'):
                front_matter_end = content.find('---', 3)
                if front_matter_end != -1:
                    body = content[front_matter_end + 3:].strip()
                    return body
            return content
        except Exception as e:
            print(f"加载技能内容时出错: {e}")
            return ""
    return ""

# 网页抓取函数
def fetch_webpage(url):
    """获取指定URL的网页内容"""
    try:
        # 移除URL两端可能存在的反引号和空格
        url = url.strip().strip('`')
        
        parsed = urlparse(url)
        if parsed.scheme == "http":
            conn = http.client.HTTPConnection(parsed.netloc)
        else:
            conn = http.client.HTTPSConnection(parsed.netloc)
        
        # 对路径部分进行URL编码，处理中文等特殊字符
        path = parsed.path or "/"
        # 分割路径并编码每个部分
        path_parts = path.split('/')
        encoded_path_parts = [quote(part, safe='') for part in path_parts]
        path = '/'.join(encoded_path_parts)
        
        if parsed.query:
            path += "?" + parsed.query
        
        conn.request("GET", path)
        resp = conn.getresponse()
        content = resp.read().decode('utf-8', errors='ignore')
        conn.close()
        
        # 移除ANSI转义字符（颜色代码等）
        content = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', content)
        
        # 返回前1000字符作为摘要（缩短以避免提示词过大）
        summary = content[:1000] + ("..." if len(content) > 1000 else "")
        return {
            "status": "success",
            "url": url,
            "content": summary,
            "full_length": len(content),
            "message": f"返回网页内容摘要（前{len(summary)}字符）"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

# ==================== 工具定义 ====================
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
            "name": "search_files",
            "description": "搜索目录下所有包含指定关键词的文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "要搜索的目录路径"
                    },
                    "keyword": {
                        "type": "string",
                        "description": "要搜索的关键词"
                    }
                },
                "required": ["directory", "keyword"]
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
            "name": "load_skill_content",
            "description": "加载指定技能的详细内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_name": {
                        "type": "string",
                        "description": "技能名称"
                    }
                },
                "required": ["skill_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_webpage",
            "description": "获取指定URL的网页内容",
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
    },
    {
        "type": "function",
        "function": {
            "name": "list_available_skills",
            "description": "获取所有可用技能列表",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]

# 工具函数映射
tool_functions = {
    "list_files": list_files,
    "search_files": search_files,
    "read_file": read_file,
    "create_file": create_file,
    "load_skill_content": load_skill_content,
    "fetch_webpage": fetch_webpage,
    "list_available_skills": list_available_skills
}

# ==================== LLM 请求相关函数 ====================

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
        "temperature": 0.7
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

# ==================== JSON解析辅助函数 ====================

def extract_json(text):
    """从文本中提取JSON内容，处理markdown代码块标记"""
    # 尝试匹配markdown代码块
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if json_match:
        return json_match.group(1).strip()
    
    # 如果没有代码块，直接返回文本（假设是纯JSON）
    return text.strip()
def parse_json_response(text):
    """解析 JSON 响应，处理可能的格式问题"""
    try:
        cleaned_text = extract_json(text)
        return json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        print(f"JSON 解析失败：{e}")
        print(f"原始文本：{text[:300]}")
        
        # 尝试修复常见的 JSON 格式问题
        # 1. 替换字符串值中的换行符为转义字符
        cleaned_text = text
        in_string = False
        escaped = False
        result = []
        for char in cleaned_text:
            if escaped:
                result.append(char)
                escaped = False
            elif char == '\\':
                result.append(char)
                escaped = True
            elif char == '"':
                in_string = not in_string
                result.append(char)
            elif in_string and char == '\n':
                result.append('\\n')
            elif in_string and char == '\r':
                result.append('\\r')
            else:
                result.append(char)
        cleaned_text = ''.join(result)
        
        # 2. 移除末尾的逗号
        cleaned_text = re.sub(r',\s*}', '}', cleaned_text)
        cleaned_text = re.sub(r',\s*]', ']', cleaned_text)
        
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e2:
            print(f"修复后仍解析失败：{e2}")
        
        # 3. 使用正则表达式提取工具调用信息
        tool_call_pattern = r'"tool_call"\s*:\s*{"name"\s*:\s*"([^"]+)"\s*,\s*"arguments"\s*:\s*({[^}]*})'
        match = re.search(tool_call_pattern, cleaned_text)
        if match:
            tool_name = match.group(1)
            args_str = match.group(2)
            try:
                args = json.loads(args_str)
                return {"done": False, "tool_call": {"name": tool_name, "arguments": args}}
            except:
                print(f"参数解析失败: {args_str}")
        
        # 4. 检查是否是完成状态
        if re.search(r'"done"\s*:\s*true', cleaned_text.lower()):
            # 尝试提取answer
            answer_match = re.search(r'"answer"\s*:\s*"([^"]+)"', cleaned_text)
            if answer_match:
                return {"done": True, "answer": answer_match.group(1)}
            return {"done": True, "answer": "任务已完成"}

        return None


# ==================== 分析提示词构建函数 ====================

import re

def clean_ansi(text):
    """移除ANSI转义字符"""
    return re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)

def build_analysis_prompt(context):
    """构建分析提示词，包含用户请求、已执行步骤历史和决策规则"""
    
    history_summary = ""
    if context.call_history:
        history_summary = "\n已执行的工具调用：\n"
        for i, call in enumerate(context.call_history[-3:], 1):  # 只保留最近3次调用
            history_summary += f"{i}. {call['tool_name']}: {json.dumps(call['arguments'], ensure_ascii=False)}\n"
            result_str = json.dumps(call['result'], ensure_ascii=False)
            result_str = clean_ansi(result_str)
            history_summary += f"   -> {result_str[:100]}{'...' if len(result_str) > 100 else ''}\n"
    
    # 简化工具列表描述
    tools_summary = ""
    for tool_name in tool_functions.keys():
        tools_summary += f"- {tool_name}\n"
    
    system_prompt = f"""你是智能助手，擅长链式工具调用。

用户请求：{context.user_request}

{history_summary}

可用工具：{list(tool_functions.keys())}

决策：如果有足够信息回答问题，输出{{"done":true,"answer":"总结内容"}}；否则调用工具{{"done":false,"tool_call":{{"name":"工具名","arguments":{{"参数":"值"}}}}}}"""
    
    return system_prompt

# ==================== 链式调用执行函数 ====================

def execute_chained_tool_call(user_request, max_iterations=10):
    """执行链式工具调用的完整流程"""
    # 初始化上下文
    context = ChainedCallContext(max_iterations=max_iterations)
    context.user_request = user_request
    
    print(f"\n=== 开始链式工具调用 ===")
    print(f"用户请求: {user_request}")
    print(f"最大迭代次数: {max_iterations}")
    
    # 初始化消息历史
    messages = [
        {"role": "user", "content": user_request}
    ]
    
    while context.should_continue():
        context.increment_iteration()
        print(f"\n--- 迭代 {context.current_iteration} ---")
        
        # 构建分析提示词 (每次都重新构建以包含最新的调用历史)
        analysis_prompt = build_analysis_prompt(context)
        
        # 更新系统提示词，保留之前的对话历史
        system_msg_index = -1
        for i, msg in enumerate(messages):
            if msg.get('role') == 'system':
                system_msg_index = i
                break
        
        if system_msg_index >= 0:
            messages[system_msg_index]['content'] = analysis_prompt
        else:
            messages.insert(0, {"role": "system", "content": analysis_prompt})
        
        # 调用LLM决定下一步操作
        print("正在调用LLM分析...")
        response = send_request(messages)
        
        if not response or 'choices' not in response:
            print("LLM响应为空或格式错误")
            break
        
        choice = response['choices'][0]
        message = choice['message']
        
        # 检查是否有tool_calls格式的响应
        if 'tool_calls' in message and message['tool_calls']:
            print("收到工具调用指令（tool_calls格式）")
            tool_calls = message['tool_calls']
            
            for tool_call in tool_calls:
                function_name = tool_call['function']['name']
                try:
                    arguments = json.loads(tool_call['function']['arguments'])
                except:
                    arguments = {}
                
                # 清理参数值中的反引号和多余空格
                cleaned_args = {}
                for key, value in arguments.items():
                    if isinstance(value, str):
                        cleaned_args[key] = value.strip().strip('`')
                    else:
                        cleaned_args[key] = value
                arguments = cleaned_args
                
                print(f"执行工具: {function_name}, 参数: {arguments}")
                
                # 执行工具
                if function_name in tool_functions:
                    try:
                        result = tool_functions[function_name](**arguments)
                        print(f"工具返回: {json.dumps(result, ensure_ascii=False)[:200]}")
                    except Exception as e:
                        result = {"status": "error", "message": str(e)}
                        print(f"工具执行失败: {e}")
                else:
                    result = {"status": "error", "message": f"未知工具: {function_name}"}
                
                # 记录到上下文
                context.add_call(function_name, arguments, result)
                
                # 添加工具响应到消息历史
                messages.append({
                    "role": "assistant",
                    "content": f"调用了工具：{function_name}"
                })
                messages.append({
                    "role": "user", 
                    "content": f"工具{function_name}执行结果：{json.dumps(result, ensure_ascii=False)}"
                })
                
                # 尝试从结果中提取有用的变量
                if isinstance(result, dict):
                    if 'files' in result:
                        context.set_variable('file_list', result['files'])
                    if 'content' in result:
                        context.set_variable('last_content', result['content'])
                    if 'matching_files' in result:
                        context.set_variable('matching_files', result['matching_files'])
        
        # 限制消息历史长度，避免提示词过大
        if len(messages) > 6:
            # 保留系统消息、用户请求和最近的工具调用
            messages = messages[:2] + messages[-4:]
        
        # 检查 content 字段是否包含 JSON 决策
        elif 'content' in message and message['content']:
            content = message['content']
            print(f"收到响应：{content[:200]}...")
            
            # 尝试解析 JSON 决策
            decision = parse_json_response(content)
            
            if decision:
                if decision.get('done'):
                    # 任务完成
                    answer = decision.get('answer', '')
                    print(f"\n=== 任务完成 ===")
                    print(f"最终回答: {answer}")
                    context.final_answer = answer
                    return context
                
                elif 'tool_call' in decision:
                    # 需要继续调用工具
                    tool_call = decision['tool_call']
                    function_name = tool_call.get('name', '')
                    arguments = tool_call.get('arguments', {})
                    
                    # 清理参数值中的反引号和多余空格
                    cleaned_args = {}
                    for key, value in arguments.items():
                        if isinstance(value, str):
                            cleaned_args[key] = value.strip().strip('`')
                        else:
                            cleaned_args[key] = value
                    arguments = cleaned_args
                    
                    print(f"执行工具: {function_name}, 参数: {arguments}")
                    
                    # 执行工具
                    if function_name in tool_functions:
                        try:
                            result = tool_functions[function_name](**arguments)
                            print(f"工具返回: {json.dumps(result, ensure_ascii=False)[:200]}")
                        except Exception as e:
                            result = {"status": "error", "message": str(e)}
                            print(f"工具执行失败: {e}")
                    else:
                        result = {"status": "error", "message": f"未知工具: {function_name}"}
                    
                    # 记录到上下文
                    context.add_call(function_name, arguments, result)
                    
                    # 添加工具响应到消息历史
                    messages.append({
                        "role": "assistant",
                        "content": f"调用了工具：{function_name}"
                    })
                    messages.append({
                        "role": "user",
                        "content": f"工具{function_name}执行结果：{json.dumps(result, ensure_ascii=False)}"
                    })
                    
                    # 尝试从结果中提取有用的变量
                    if isinstance(result, dict):
                        if 'files' in result:
                            context.set_variable('file_list', result['files'])
                        if 'content' in result:
                            context.set_variable('last_content', result['content'])
                        if 'matching_files' in result:
                            context.set_variable('matching_files', result['matching_files'])
                    
                    # 限制消息历史长度，避免提示词过大
                    if len(messages) > 6:
                        # 保留系统消息、用户请求和最近的工具调用
                        messages = messages[:2] + messages[-4:]
            
            else:
                # 无法解析JSON，假设是直接回答
                print(f"直接回答: {content}")
                context.final_answer = content
                return context
        
        else:
            print("无法识别响应格式")
            break
    
    # 达到最大迭代次数
    if not context.final_answer:
        context.final_answer = f"已达到最大迭代次数({max_iterations})，任务未完成。已执行的步骤：\n{json.dumps(context.get_summary(), ensure_ascii=False, indent=2)}"
    
    return context

# ==================== 测试函数 ====================

def test_chained_call():
    """测试链式工具调用功能"""
    print("=====================================")
    print("      链式工具调用测试系统")
    print("=====================================")
    print("选择测试项：")
    print("1. 文件搜索链式调用")
    print("2. 技能查询链式调用")
    print("3. 网页处理链式调用")
    print("4. 自定义测试")
    print("=====================================\n")
    
    choice = input("请输入测试编号(1-4): ")
    
    if choice == "1":
        # 测试1：文件搜索链式调用
        user_request = "请查找practice05目录下的所有包含'def'关键词的文件，并总结这些文件的主要内容"
        print(f"\n测试1: {user_request}")
        context = execute_chained_tool_call(user_request)
        print(f"\n最终结果:\n{context.final_answer}")
        
    elif choice == "2":
        # 测试2：技能查询链式调用
        user_request = "我想了解notice技能的详细规则"
        print(f"\n测试2: {user_request}")
        context = execute_chained_tool_call(user_request)
        print(f"\n最终结果:\n{context.final_answer}")
        
    elif choice == "3":
        # 测试3：网页处理链式调用
        user_request = "访问https://www.nsu.edu.cn/HTML/news/2024/06/article_3974.html并总结页面内容，保存到practice06/summary.txt"
        print(f"\n测试3: {user_request}")
        context = execute_chained_tool_call(user_request)
        print(f"\n最终结果:\n{context.final_answer}")
        
    elif choice == "4":
        # 自定义测试
        user_request = input("请输入自定义测试请求: ")
        context = execute_chained_tool_call(user_request)
        print(f"\n最终结果:\n{context.final_answer}")
        
    else:
        print("无效选择")

# ==================== 主函数 ====================

def main():
    print("=====================================")
    print("         链式工具调用系统")
    print("=====================================")
    print("基于LLM实现链式工具调用，前一个工具的输出可作为后一个工具的输入")
    print("=====================================\n")
    
    try:
        while True:
            print("\n请选择操作：")
            print("1. 运行测试")
            print("2. 直接输入请求")
            print("3. 退出")
            
            choice = input("请输入选择(1-3): ")
            
            if choice == "1":
                test_chained_call()
            elif choice == "2":
                user_request = input("请输入你的请求: ")
                context = execute_chained_tool_call(user_request)
                print(f"\nAI: {context.final_answer}")
            elif choice == "3":
                print("程序结束，再见！")
                break
            else:
                print("无效选择，请重新输入")
    
    except KeyboardInterrupt:
        print("\n\n程序结束，再见！")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    main()
