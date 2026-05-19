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

# 模型配置
MODEL_CONFIGS = {
    "qwen3.5-9b": {
        "full": {
            "model_name": "qwen3.5-9b",
            "base_url": os.getenv("BASE_URL_QWEN35_9B", os.getenv("BASE_URL"))
        },
        "light": {
            "model_name": "qwen3.5-9b-light",
            "base_url": os.getenv("BASE_URL_QWEN35_9B_LIGHT", os.getenv("BASE_URL"))
        }
    },
    "qwen2.5-3b": {
        "full": {
            "model_name": "qwen2.5-3b",
            "base_url": os.getenv("BASE_URL_QWEN25_3B", os.getenv("BASE_URL"))
        },
        "light": {
            "model_name": "qwen2.5-3b-light",
            "base_url": os.getenv("BASE_URL_QWEN25_3B_LIGHT", os.getenv("BASE_URL"))
        }
    }
}

API_TOKEN = os.getenv("API_TOKEN")

# 日志目录
LOG_DIR = "C:\\Users\\20918\\Desktop\\llm_test_project\\chat-log"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 日志文件路径
LOG_FILES = {
    "qwen3.5-9b": {
        "full": os.path.join(LOG_DIR, "qwen35_9b_full.log"),
        "light": os.path.join(LOG_DIR, "qwen35_9b_light.log")
    },
    "qwen2.5-3b": {
        "full": os.path.join(LOG_DIR, "qwen25_3b_full.log"),
        "light": os.path.join(LOG_DIR, "qwen25_3b_light.log")
    },
    "total": os.path.join(LOG_DIR, "total.log")
}

print("模型配置:")
for model, deployments in MODEL_CONFIGS.items():
    for deployment, config in deployments.items():
        print(f"  {model} ({deployment}): {config['model_name']} @ {config['base_url']}")

print(f"API_TOKEN = {API_TOKEN}")
print(f"日志目录: {LOG_DIR}")

def get_connection(base_url):
    """创建新的HTTP/HTTPS连接（http.client连接不支持复用）"""
    parsed = urlparse(base_url)
    
    if parsed.scheme == "http":
        return http.client.HTTPConnection(parsed.netloc, timeout=30)
    else:
        return http.client.HTTPSConnection(parsed.netloc, timeout=30)

def close_all_connections():
    """关闭所有连接（现在每次请求都创建新连接，无需手动管理）"""
    pass

def send_request(messages, model_config, stream=True):
    base_url = model_config['base_url']
    conn = None
    
    payload = {
        "model": model_config['model_name'],
        "messages": messages,
        "temperature": 1.0,
        "stream": stream
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_TOKEN}"
    }

    try:
        conn = get_connection(base_url)
        conn.request("POST", "/v1/chat/completions", body=json.dumps(payload), headers=headers)
        return conn.getresponse()
    except Exception as e:
        print(f"发生错误: {e}")
        # 连接失败，从连接池中移除
        parsed = urlparse(base_url)
        key = parsed.netloc
        with lock:
            if key in connection_pool:
                connection_pool[key] = None
        if conn:
            try:
                conn.close()
            except:
                pass
        return None

def handle_streaming_response(response):
    if not response:
        return ""
    
    full_response = ""
    print("\nAI: ", end="")
    
    try:
        while True:
            try:
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
            except (http.client.IncompleteRead, ConnectionResetError, OSError) as e:
                print(f"\n连接错误: {e}")
                break
    finally:
        try:
            response.close()
        except:
            pass
    
    print()  # 换行
    return full_response

def handle_non_streaming_response(response):
    if not response:
        return ""
    
    try:
        data = json.loads(response.read().decode())
        if 'choices' in data and data['choices']:
            return data['choices'][0]['message']['content']
    except (http.client.IncompleteRead, ConnectionResetError, OSError) as e:
        print(f"连接错误: {e}")
    except Exception as e:
        print(f"处理响应时发生错误: {e}")
    finally:
        try:
            response.close()
        except:
            pass
    
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

def compress_chat_history(chat_history, model_config):
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
    response = send_request(compression_messages, model_config, stream=False)
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

def extract_key_information(chat_history, model_config):
    """提取聊天记录中的关键信息（每5次聊天提取一次）"""
    print("\n正在提取关键信息...")
    
    # 生成提取提示
    extraction_prompt = """请从以下聊天记录中提取关键信息，按照5W原则（谁Who、做了什么事What、什么时候When（可选）、在何处Where（可选）、为什么要做这个事Why）提取多条关键信息：

"""
    
    # 构建提取请求消息
    extraction_messages = [
        {"role": "system", "content": "你是一个专业的信息提取助手，擅长从对话中提取关键信息并按照5W原则组织。"},
        {"role": "user", "content": extraction_prompt + json.dumps(chat_history, ensure_ascii=False)}
    ]
    
    # 发送提取请求
    response = send_request(extraction_messages, model_config, stream=False)
    key_info = handle_non_streaming_response(response)
    
    if key_info:
        print("关键信息提取完成")
        return key_info
    else:
        print("提取失败")
        return ""

def write_log(model, deployment, content):
    """写入日志文件"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {content}\n\n"
    
    # 确保日志目录存在
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    # 写入模型特定日志
    if model in LOG_FILES and deployment in LOG_FILES[model]:
        log_file = LOG_FILES[model][deployment]
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"写入模型日志失败: {e}")
    else:
        # 如果模型或部署方式不在配置中，创建默认日志文件
        default_log_file = os.path.join(LOG_DIR, f"{model.replace('.', '_').replace('-', '_')}_{deployment}.log")
        try:
            with open(default_log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"写入默认模型日志失败: {e}")
    
    # 写入总日志
    try:
        with open(LOG_FILES['total'], 'a', encoding='utf-8') as f:
            f.write(f"[{model}-{deployment}] {log_entry}")
    except Exception as e:
        print(f"写入总日志失败: {e}")

def search_chat_history(user_query, model_config):
    """搜索聊天历史记录"""
    print("\n正在搜索聊天历史...")
    
    # 读取总日志文件
    total_log = LOG_FILES['total']
    if os.path.exists(total_log):
        with open(total_log, 'r', encoding='utf-8') as f:
            log_content = f.read()
        # 限制日志内容长度，避免超出模型上下文限制
        max_log_length = 2000
        if len(log_content) > max_log_length:
            # 保留最新的日志内容
            log_content = log_content[-max_log_length:]
            print(f"日志内容过长，已截取最后{max_log_length}字符")
    else:
        log_content = ""
    
    # 构建搜索请求消息 - 优化提示词，使其更适合小模型处理
    search_messages = [
        {"role": "system", "content": "你是一个专业的聊天记录分析助手，擅长根据用户查询从聊天历史中找到相关信息。请直接回答用户的问题，不要有任何引言或开场白。"},
        {"role": "user", "content": f"请从以下聊天历史中找到与'{user_query}'相关的信息：\n\n{log_content}\n\n请直接提供相关信息，不要有任何引言。"}
    ]
    
    # 发送搜索请求
    response = send_request(search_messages, model_config, stream=False)
    search_result = handle_non_streaming_response(response)
    
    if search_result:
        print("\n搜索结果：")
        print(search_result)
        return search_result
    else:
        print("搜索失败")
        return ""

def should_search_chat(user_input):
    """判断是否需要搜索聊天历史"""
    # 检查是否以/search开头
    if user_input.strip().startswith("/search"):
        return True
    
    # 检查是否包含搜索相关关键词
    search_keywords = ["查找聊天记录", "搜索历史", "之前的对话", "历史消息"]
    for keyword in search_keywords:
        if keyword in user_input:
            return True
    
    return False

def main():
    print("=====================================")
    print("         聊天分析系统")
    print("=====================================")
    print("输入消息与AI对话，按Ctrl+C退出")
    print("使用 /search 开头的消息可搜索聊天历史")
    print("系统会自动提取关键信息并记录到日志")
    print("=====================================\n")
    
    # 选择模型和部署方式
    print("请选择模型配置：")
    print("1. qwen3.5-9b (全量部署)")
    print("2. qwen3.5-9b (轻量部署)")
    print("3. qwen2.5-3b (全量部署)")
    print("4. qwen2.5-3b (轻量部署)")
    
    choice = input("请输入选项 (1-4): ")
    
    model_config_map = {
        "1": ("qwen3.5-9b", "full"),
        "2": ("qwen3.5-9b", "light"),
        "3": ("qwen2.5-3b", "full"),
        "4": ("qwen2.5-3b", "light")
    }
    
    if choice not in model_config_map:
        print("无效选项，使用默认配置: qwen2.5-3b (全量部署)")
        model, deployment = "qwen2.5-3b", "full"
    else:
        model, deployment = model_config_map[choice]
    
    model_config = MODEL_CONFIGS[model][deployment]
    print(f"\n使用模型: {model} ({deployment}) - {model_config['model_name']}")
    
    # 初始化聊天历史
    chat_history = []
    chat_count = 0
    
    try:
        while True:
            # 检查是否需要压缩
            if should_compress_chat(chat_history):
                chat_history = compress_chat_history(chat_history, model_config)
            
            # 每次聊天都提取关键信息
            if chat_count > 0:
                key_info = extract_key_information(chat_history, model_config)
                if key_info:
                    write_log(model, deployment, f"关键信息提取：\n{key_info}")
                    # 同时写入到指定的log.txt文件
                    log_txt_path = os.path.join(LOG_DIR, "log.txt")
                    try:
                        with open(log_txt_path, 'a', encoding='utf-8') as f:
                            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                            f.write(f"[{timestamp}] [{model}-{deployment}] 关键信息提取：\n{key_info}\n\n")
                    except Exception as e:
                        print(f"写入log.txt失败: {e}")
            
            # 获取用户输入
            try:
                user_input = input("你: ")
            except KeyboardInterrupt:
                print("\n\n聊天结束，再见！")
                return
            
            # 检查是否需要搜索聊天历史
            if should_search_chat(user_input):
                # 提取搜索查询
                if user_input.strip().startswith("/search"):
                    search_query = user_input.strip()[8:].strip()
                else:
                    search_query = user_input
                
                search_chat_history(search_query, model_config)
                print()
                continue
            
            # 添加用户消息到历史
            chat_history.append({"role": "user", "content": user_input})
            chat_count += 1
            
            # 写入用户消息到日志
            write_log(model, deployment, f"用户: {user_input}")
            
            # 发送请求并处理流式响应
            response = send_request(chat_history, model_config)
            if response:
                ai_response = handle_streaming_response(response)
                # 添加AI回复到历史
                chat_history.append({"role": "assistant", "content": ai_response})
                # 写入AI回复到日志
                write_log(model, deployment, f"AI: {ai_response}")
            
            print()  # 空行分隔
    
    except KeyboardInterrupt:
        # 在退出前提取关键信息
        if chat_count > 0:
            key_info = extract_key_information(chat_history, model_config)
            if key_info:
                write_log(model, deployment, f"关键信息提取：\n{key_info}")
                # 同时写入到指定的log.txt文件
                log_txt_path = os.path.join(LOG_DIR, "log.txt")
                try:
                    with open(log_txt_path, 'a', encoding='utf-8') as f:
                        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                        f.write(f"[{timestamp}] [{model}-{deployment}] 关键信息提取：\n{key_info}\n\n")
                except Exception as e:
                    print(f"写入log.txt失败: {e}")
        print("\n\n聊天结束，再见！")
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        # 关闭所有连接
        close_all_connections()

if __name__ == "__main__":
    main()