#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import requests
from dotenv import load_dotenv

# 加载 .env
load_dotenv()

# 从环境变量读取配置
ANYTHINGLLM_API_KEY = os.getenv("ANYTHINGLLM_API_KEY")
ANYTHINGLLM_WORKSPACE_SLUG = os.getenv("ANYTHINGLLM_WORKSPACE_SLUG")

if not ANYTHINGLLM_API_KEY:
    print("错误：请在 .env 文件中配置 ANYTHINGLLM_API_KEY")
    exit(1)

if not ANYTHINGLLM_WORKSPACE_SLUG:
    print("错误：请在 .env 文件中配置 ANYTHINGLLM_WORKSPACE_SLUG")
    exit(1)

def anythingllm_query(message):
    """
    使用 subprocess 模块调用 curl 命令访问 AnythingLLM 的聊天 API
    :param message: 查询消息
    :return: API 响应结果
    """
    # 构建 API URL
    api_url = f"http://localhost:3001/api/v1/workspace/{ANYTHINGLLM_WORKSPACE_SLUG}/chat"
    
    # 构建请求数据
    request_data = {
        "message": message
    }
    
    # 使用 requests 库发起请求（避免命令注入风险）
    headers = {
        "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=request_data)
        response.raise_for_status()
        
        response_data = response.json()
        if "response" in response_data:
            return response_data["response"]
        else:
            return f"错误：API 响应格式不正确，{response.text}"
    except requests.exceptions.RequestException as e:
        return f"错误：API 调用失败，{str(e)}"
    except json.JSONDecodeError:
        return f"错误：API 响应不是有效的 JSON，{response.text}"

if __name__ == "__main__":
    # 测试函数
    test_message = "你好，AnythingLLM！"
    print(f"测试查询: {test_message}")
    result = anythingllm_query(test_message)
    print(f"查询结果: {result}")
