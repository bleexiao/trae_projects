# Practice01: 基础 LLM API 调用

## 项目简介

本项目演示如何通过原生 Python `http.client` 模块调用大语言模型(LLM) API，是学习 LLM 客户端开发的入门实践。

## 功能特性

- 通过 HTTP/HTTPS POST 请求调用 LLM API
- 从 .env 文件加载环境配置（使用 dotenv 库）
- 实现与 LLM 的简单对话交互
- 支持流式响应处理

## 配置说明

在项目根目录创建 `.env` 文件：
```
BASE_URL=https://your-llm-api-endpoint/v1
MODEL_NAME=your-model-name
API_TOKEN=your-api-token
```

## 运行命令

```bash
python llm_client.py
```

## 实现的技术点

- `os.getenv()` - 读取系统环境变量
- `dotenv.load_dotenv()` - 加载 .env 配置文件
- `http.client.HTTPConnection / HTTPSConnection` - 建立 HTTP 连接
- `json.dumps()` - 序列化 Python 对象为 JSON 字符串
- `urllib.parse.urlparse()` - 解析 URL（支持从 BASE_URL 中提取路径）
- API 调用格式（OpenAI 兼容的 `/v1/chat/completions` 接口）
- 配置验证函数 `validate_config()` - 确保配置正确
- 错误处理优化 - 区分 HTTP 错误、JSON 解析错误和其他异常

## 教学目标

- 理解客户端如何与 LLM API 服务进行通信
- 掌握 HTTP 请求的基本原理和构造方法
- 学习环境变量管理敏感配置信息
- 了解 JSON 数据格式在 API 通信中的应用

## 项目结构

```
practice01/
├── llm_client.py    # 基础 LLM API 调用实现
└── README.md        # 项目说明文档
```

## 依赖项

- Python 3.6+
- `python-dotenv` 库
- 一个支持 OpenAI 兼容 API 的 LLM 服务
