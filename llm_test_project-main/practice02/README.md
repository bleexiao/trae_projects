# Practice02: 终端聊天界面与工具调用系统

## 项目简介

本项目包含两个核心功能模块：

1. **终端聊天界面** (chat_interface.py) - 支持流式输出和聊天历史管理
2. **工具调用系统** (tool_calling.py) - 基于 LLM 的文件操作工具调用

## 功能特性

### 终端聊天界面

- 交互式终端聊天界面，支持实时对话
- 流式输出支持，实时显示 AI 回复
- 自动维护聊天历史记录
- 支持按 Ctrl+C 优雅退出程序
- API 路径自动解析，避免路径重复

### 工具调用系统

- 提供 5 个文件操作工具：
  - `list_files`: 列出目录下的文件
  - `rename_file`: 重命名文件
  - `delete_file`: 删除文件
  - `create_file`: 创建文件
  - `read_file`: 读取文件内容
- 支持通过自然语言指令调用工具
- 自动处理工具调用和结果处理
- 多轮对话上下文管理

## 配置说明

在 `.env` 文件中配置：
```
BASE_URL=https://your-llm-api-endpoint
MODEL_NAME=your-model-name
API_TOKEN=your-api-token
```

**注意**：BASE_URL 可以包含完整路径（如 `https://api.example.com/v1/chat/completions`），系统会自动解析路径部分。

## 运行命令

```bash
# 运行终端聊天界面
python chat_interface.py

# 运行工具调用系统
python tool_calling.py
```

## 技术优化说明

**2026-05-19 更新**
- 修复 API 路径构建逻辑：使用 `urlparse` 直接从 BASE_URL 中解析路径部分，避免路径重复问题
- 支持完整 URL 路径配置，提高灵活性

## 项目结构

```
practice02/
├── chat_interface.py      # 终端聊天界面
├── tool_calling.py        # 工具调用系统
├── project_structure.html # 项目结构可视化
├── project_structure.svg  # 项目结构图示
└── README.md              # 项目说明文档
```

## 依赖项

- Python 3.6+
- `python-dotenv` 库
- 一个支持 OpenAI 兼容 API 的 LLM 服务
