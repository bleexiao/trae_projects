# Practice03: 聊天记录压缩与分析系统

## 项目简介

本项目包含两个核心功能模块：

1. **聊天记录压缩系统** (chat_compression.py)
2. **聊天分析系统** (chat_analytics.py)

## 功能特性

### 聊天记录压缩系统

- 自动检测聊天历史长度，当超过5轮或上下文长度超过3000字符时自动触发压缩
- 对前70%的聊天内容进行智能摘要，保留最后30%的实时对话
- 支持流式输出和正常的聊天交互

### 聊天分析系统

- 关键信息提取功能（每5次聊天提取一次）
- 按照5W原则（Who、What、When、Where、Why）提取关键信息
- 支持多模型部署配置（qwen3.5-9b和qwen2.5-3b的全量和轻量部署）
- 聊天记录搜索功能（使用/search开头或相关关键词）
- 增量更新日志到本地文件系统

## 配置说明

在 `.env` 文件中配置：
```
BASE_URL=https://your-llm-api-endpoint
MODEL_NAME=your-model-name
API_TOKEN=your-api-token
```

对于多模型部署，还可以配置：
```
BASE_URL_QWEN35_9B=https://your-qwen35-9b-endpoint
BASE_URL_QWEN35_9B_LIGHT=https://your-qwen35-9b-light-endpoint
BASE_URL_QWEN25_3B=https://your-qwen25-3b-endpoint
BASE_URL_QWEN25_3B_LIGHT=https://your-qwen25-3b-light-endpoint
```

## 运行命令

```bash
# 运行聊天压缩系统
python chat_compression.py

# 运行聊天分析系统
python chat_analytics.py
```

## 技术优化说明

**2026-05-19 更新**
- 修复 HTTP 连接复用问题：`http.client.HTTPConnection/HTTPSConnection` 对象不支持复用，改为每次请求创建新连接
- 移除了无效的连接池管理逻辑，简化代码结构

## 项目结构

```
practice03/
├── chat_compression.py    # 聊天记录压缩系统
├── chat_analytics.py      # 聊天分析系统
└── README.md              # 项目说明文档
```

## 依赖项

- Python 3.6+
- `python-dotenv` 库
- 一个支持 OpenAI 兼容 API 的 LLM 服务
