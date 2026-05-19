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
        self.call_history = []
        self.variables = {}
        self.user_request = ""
        self.final_answer = ""
    
    def add_call(self, tool_name, arguments, result):
        self.call_history.append({
            "tool_name": tool_name,
            "arguments": arguments,
            "result": result,
            "iteration": self.current_iteration
        })
    
    def set_variable(self, name, value):
        self.variables[name] = value
    
    def get_variable(self, name, default=None):
        return self.variables.get(name, default)
    
    def increment_iteration(self):
        self.current_iteration += 1
    
    def should_continue(self):
        return self.current_iteration < self.max_iterations
    
    def get_summary(self):
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
    """列出某个目录下有哪些文件"""
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

def create_file(directory=None, filename=None, content=None, path=None):
    """在某个目录下新建文件，并且写入内容"""
    try:
        if path:
            directory = os.path.dirname(path)
            filename = os.path.basename(path)
            if not directory:
                directory = '.'
        elif filename and not directory:
            directory = '.'
        
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
    """读取某个目录下的某个文件并返回内容"""
    try:
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return {
            "status": "success",
            "content": content,
            "full_length": len(content)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def list_available_skills():
    """读取技能列表，提取每个技能的name和description"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    skills = []
    
    skill_dirs = [
        os.path.join(current_dir),
        os.path.join(os.path.dirname(current_dir), ".agents", "skills")
    ]
    
    for skills_dir in skill_dirs:
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
    
    return {"skills": skills}

def load_skill_content(skill_name):
    """加载技能的正文内容"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    skill_paths = [
        os.path.join(current_dir, skill_name),
        os.path.join(os.path.dirname(current_dir), ".agents", "skills", skill_name)
    ]
    
    for skill_path in skill_paths:
        skill_file = os.path.join(skill_path, "SKILL.md")
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

def load_example_file(example_name):
    """加载示例文件内容"""
    assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "init-article", "assets")
    example_path = os.path.join(assets_dir, f"{example_name}-example.md")
    
    if os.path.exists(example_path):
        try:
            with open(example_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"加载示例文件时出错: {e}")
            return ""
    return ""

# ==================== 工具定义 ====================
tools = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "列出某个目录下有哪些文件",
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
            "description": "读取某个目录下的某个文件并返回内容",
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
            "description": "在某个目录下新建文件，并且写入内容",
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
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        conn.request("POST", "/v1/chat/completions", body=body, headers=headers)
        resp = conn.getresponse()
        raw_data = resp.read()
        data = json.loads(raw_data.decode('utf-8', errors='ignore'))
        return data
    except Exception as e:
        print(f"发生错误: {e}")
        return None
    finally:
        conn.close()

# ==================== JSON解析辅助函数 ====================

def extract_json(text):
    """从文本中提取JSON内容，处理markdown代码块标记"""
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if json_match:
        return json_match.group(1).strip()
    return text.strip()

def parse_json_response(text):
    """解析 JSON 响应，处理可能的格式问题"""
    try:
        cleaned_text = extract_json(text)
        return json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        print(f"JSON 解析失败：{e}")
        print(f"原始文本：{text[:300]}")
        
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
        
        cleaned_text = re.sub(r',\s*}', '}', cleaned_text)
        cleaned_text = re.sub(r',\s*]', ']', cleaned_text)
        
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e2:
            print(f"修复后仍解析失败：{e2}")
        
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
        
        if re.search(r'"done"\s*:\s*true', cleaned_text.lower()):
            answer_match = re.search(r'"answer"\s*:\s*"([^"]+)"', cleaned_text)
            if answer_match:
                return {"done": True, "answer": answer_match.group(1)}
            return {"done": True, "answer": "任务已完成"}

        return None

# ==================== 分析提示词构建函数 ====================

def clean_ansi(text):
    """移除ANSI转义字符"""
    return re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)

def build_analysis_prompt(context):
    """构建分析提示词，包含用户请求、已执行步骤历史和决策规则"""
    
    history_summary = ""
    if context.call_history:
        history_summary = "\n已执行的工具调用：\n"
        for i, call in enumerate(context.call_history[-3:], 1):
            history_summary += f"{i}. {call['tool_name']}: {json.dumps(call['arguments'], ensure_ascii=False)}\n"
            result_str = json.dumps(call['result'], ensure_ascii=False)
            result_str = clean_ansi(result_str)
            history_summary += f"   -> {result_str[:100]}{'...' if len(result_str) > 100 else ''}\n"
    
    system_prompt = f"""你是智能助手，擅长链式工具调用和文章生成。

用户请求：{context.user_request}

{history_summary}

可用工具：{list(tool_functions.keys())}

决策规则：
1. 如果需要生成文章规则，先调用load_skill_content加载init-article技能
2. 根据技能和用户需求，生成四个规则文件（topic.md, voice.md, structure.md, check.md）
3. 使用create_file保存规则文件到article_rules目录
4. 如果有足够信息生成文章，输出{{"done":true,"answer":"文章内容"}}
5. 否则调用工具{{"done":false,"tool_call":{{"name":"工具名","arguments":{{"参数":"值"}}}}}}"""
    
    return system_prompt

# ==================== 链式调用执行函数 ====================

def execute_chained_tool_call(user_request, max_iterations=10):
    """执行链式工具调用的完整流程"""
    context = ChainedCallContext(max_iterations=max_iterations)
    context.user_request = user_request
    
    print(f"\n=== 开始链式工具调用 ===")
    print(f"用户请求: {user_request}")
    print(f"最大迭代次数: {max_iterations}")
    
    messages = [
        {"role": "user", "content": user_request}
    ]
    
    while context.should_continue():
        context.increment_iteration()
        print(f"\n--- 迭代 {context.current_iteration} ---")
        
        analysis_prompt = build_analysis_prompt(context)
        
        system_msg_index = -1
        for i, msg in enumerate(messages):
            if msg.get('role') == 'system':
                system_msg_index = i
                break
        
        if system_msg_index >= 0:
            messages[system_msg_index]['content'] = analysis_prompt
        else:
            messages.insert(0, {"role": "system", "content": analysis_prompt})
        
        print("正在调用LLM分析...")
        response = send_request(messages, tools=tools)
        
        if not response or 'choices' not in response:
            print("LLM响应为空或格式错误")
            break
        
        choice = response['choices'][0]
        message = choice['message']
        
        if 'tool_calls' in message and message['tool_calls']:
            print("收到工具调用指令（tool_calls格式）")
            tool_calls = message['tool_calls']
            
            for tool_call in tool_calls:
                function_name = tool_call['function']['name']
                try:
                    arguments = json.loads(tool_call['function']['arguments'])
                except:
                    arguments = {}
                
                cleaned_args = {}
                for key, value in arguments.items():
                    if isinstance(value, str):
                        cleaned_args[key] = value.strip().strip('`')
                    else:
                        cleaned_args[key] = value
                arguments = cleaned_args
                
                print(f"执行工具: {function_name}, 参数: {arguments}")
                
                if function_name in tool_functions:
                    try:
                        result = tool_functions[function_name](**arguments)
                        print(f"工具返回: {json.dumps(result, ensure_ascii=False)[:200]}")
                    except Exception as e:
                        result = {"status": "error", "message": str(e)}
                        print(f"工具执行失败: {e}")
                else:
                    result = {"status": "error", "message": f"未知工具: {function_name}"}
                
                context.add_call(function_name, arguments, result)
                
                messages.append({
                    "role": "assistant",
                    "content": f"调用了工具：{function_name}"
                })
                messages.append({
                    "role": "user", 
                    "content": f"工具{function_name}执行结果：{json.dumps(result, ensure_ascii=False)}"
                })
                
                if isinstance(result, dict):
                    if 'files' in result:
                        context.set_variable('file_list', result['files'])
                    if 'content' in result:
                        context.set_variable('last_content', result['content'])
                    if 'matching_files' in result:
                        context.set_variable('matching_files', result['matching_files'])
        
        if len(messages) > 6:
            messages = messages[:2] + messages[-4:]
        
        elif 'content' in message and message['content']:
            content = message['content']
            print(f"收到响应：{content[:200]}...")
            
            decision = parse_json_response(content)
            
            if decision:
                if decision.get('done'):
                    answer = decision.get('answer', '')
                    print(f"\n=== 任务完成 ===")
                    print(f"最终回答: {answer}")
                    context.final_answer = answer
                    return context
                
                elif 'tool_call' in decision:
                    tool_call = decision['tool_call']
                    function_name = tool_call.get('name', '')
                    arguments = tool_call.get('arguments', {})
                    
                    cleaned_args = {}
                    for key, value in arguments.items():
                        if isinstance(value, str):
                            cleaned_args[key] = value.strip().strip('`')
                        else:
                            cleaned_args[key] = value
                    arguments = cleaned_args
                    
                    print(f"执行工具: {function_name}, 参数: {arguments}")
                    
                    if function_name in tool_functions:
                        try:
                            result = tool_functions[function_name](**arguments)
                            print(f"工具返回: {json.dumps(result, ensure_ascii=False)[:200]}")
                        except Exception as e:
                            result = {"status": "error", "message": str(e)}
                            print(f"工具执行失败: {e}")
                    else:
                        result = {"status": "error", "message": f"未知工具: {function_name}"}
                    
                    context.add_call(function_name, arguments, result)
                    
                    messages.append({
                        "role": "assistant",
                        "content": f"调用了工具：{function_name}"
                    })
                    messages.append({
                        "role": "user",
                        "content": f"工具{function_name}执行结果：{json.dumps(result, ensure_ascii=False)}"
                    })
                    
                    if isinstance(result, dict):
                        if 'files' in result:
                            context.set_variable('file_list', result['files'])
                        if 'content' in result:
                            context.set_variable('last_content', result['content'])
                        if 'matching_files' in result:
                            context.set_variable('matching_files', result['matching_files'])
                    
                    if len(messages) > 6:
                        messages = messages[:2] + messages[-4:]
            
            else:
                print(f"直接回答: {content}")
                context.final_answer = content
                return context
        
        else:
            print("无法识别响应格式")
            break
    
    if not context.final_answer:
        context.final_answer = f"已达到最大迭代次数({max_iterations})，任务未完成。已执行的步骤：\n{json.dumps(context.get_summary(), ensure_ascii=False, indent=2)}"
    
    return context

# ==================== 文章生成核心函数 ====================

def load_skill_content_local(skill_dir="init-article"):
    """加载本地SKILL.md文件内容"""
    skill_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), skill_dir, "SKILL.md")
    
    if not os.path.exists(skill_path):
        return None, f"错误：找不到SKILL.md文件 ({skill_path})"
    
    try:
        with open(skill_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content, "SKILL.md加载成功！"
    except Exception as e:
        return None, f"读取SKILL.md失败: {e}"

def build_article_prompt(skill_content, user_request):
    """构建文章生成提示词"""
    return f"""请仔细阅读以下SKILL.md文件，理解其中的工作流程。

【SKILL.md内容】
{skill_content}

【用户需求】
{user_request}

请按照SKILL.md中描述的工作流程：
1. 理解四个规则文件的定位（topic.md写什么、voice.md怎么写、structure.md写成什么样、check.md写完后查什么）
2. 根据用户需求，在内部构建这四个规则
3. 严格按照这四个规则撰写文章

要求：
- 直接输出文章内容（txt格式）
- 不要输出规则文件内容
- 不要输出任何说明文字
- 只输出用户需要的文章正文"""

def generate_article(user_request):
    """根据用户需求生成文章"""
    print("\n=== 步骤1: 读取SKILL.md ===")
    skill_content, msg = load_skill_content_local()
    
    if not skill_content:
        print(msg)
        return False
    
    print(msg)
    
    print("\n=== 步骤2: 大模型按照SKILL.md流程生成文章 ===")
    print("流程：大模型阅读SKILL.md → 理解四个规则 → 直接生成txt文章")
    
    article_prompt = build_article_prompt(skill_content, user_request)
    
    messages = [
        {"role": "system", "content": "你是专业的文案撰写师，擅长根据SKILL.md的工作流程撰写高质量文档。"},
        {"role": "user", "content": article_prompt}
    ]
    
    print("正在调用LLM生成文章...")
    response = send_request(messages)
    
    if not response or 'choices' not in response:
        print("错误：LLM响应失败")
        return False
    
    article = response['choices'][0]['message']['content']
    
    if not article or len(article.strip()) == 0:
        print("错误：生成的文章为空")
        return False
    
    print("\n=== 步骤3: 保存文章 ===")
    
    article_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "读书心得.txt")
    
    try:
        with open(article_path, 'w', encoding='utf-8') as f:
            f.write(article)
        
        print(f"✓ 文章已保存到: {article_path}")
        print(f"✓ 文章长度: {len(article)} 字符")
        print(f"\n【文章摘要（前500字）】")
        print(f"{article[:500]}...")
        return True
        
    except Exception as e:
        print(f"错误：保存文章失败 - {e}")
        return False

# ==================== 主函数 ====================

def main():
    """主程序入口"""
    print("=" * 50)
    print("         文章初始化与生成系统")
    print("=" * 50)
    print("基于init-article技能，一键生成读书心得")
    print("=" * 50)
    
    try:
        while True:
            print("\n" + "-" * 50)
            print("请选择操作：")
            print("1. 一键生成读书心得")
            print("2. 退出")
            print("-" * 50)
            
            choice = input("请输入选择(1-2): ").strip()
            
            if choice == "1":
                user_request = input("\n请输入文章主题或需求: ").strip()
                
                if not user_request:
                    print("错误：需求不能为空")
                    continue
                
                success = generate_article(user_request)
                
                if success:
                    print("\n✓ 文章生成完成！")
                else:
                    print("\n✗ 文章生成失败，请重试")
            
            elif choice == "2":
                print("\n程序结束，再见！")
                break
            
            else:
                print("无效选择，请输入 1 或 2")
    
    except KeyboardInterrupt:
        print("\n\n程序被中断，再见！")
    except Exception as e:
        print(f"\n发生未捕获错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
