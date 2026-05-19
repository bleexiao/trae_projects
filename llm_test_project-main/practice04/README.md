# Practice04: AnythingLLM 查询功能

本项目实现了通过 AnythingLLM 查询文档仓库的功能，当用户提到"文档仓库"、"文件仓库"、"仓库"时，系统会自动调用 AnythingLLM 的 API 进行查询。

## 功能特性

1. **AnythingLLM 查询**：通过 requests 库访问 AnythingLLM 的聊天 API（安全优化，避免命令注入风险）
2. **工具调用**：集成到智能助手系统中，作为一个工具供 LLM 调用
3. **环境变量配置**：从 .env 文件读取 API 密钥和工作区信息
4. **中文编码支持**：确保中文查询和响应正常处理
5. **安全设计**：使用 requests 库替代 subprocess 调用，消除命令注入风险

## 配置说明

1. 在项目根目录创建 .env 文件，基于 .env.example 模板
2. 配置以下环境变量：
   - `BASE_URL`：LLM 模型的 API 基础 URL
   - `MODEL_NAME`：使用的模型名称
   - `API_TOKEN`：LLM 模型的 API 令牌
   - `ANYTHINGLLM_API_KEY`：AnythingLLM 的 API 密钥
   - `ANYTHINGLLM_WORKSPACE_SLUG`：AnythingLLM 的工作区 slug

## 运行步骤

1. 确保 AnythingLLM 服务正在运行（默认端口为 3001）
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 运行聊天客户端：
   ```bash
   python chat_client.py
   ```
4. 在聊天界面中，当提到"文档仓库"、"文件仓库"或"仓库"时，系统会自动调用 AnythingLLM 查询工具

## 测试示例

```
你: 文档仓库中有什么内容？
AI: 正在处理请求...

调用工具: anythingllm_query
工具返回: {
  "status": "success",
  "content": "文档仓库中包含以下内容：..."
}

AI: 文档仓库中包含以下内容：...
```

## 注意事项

1. 确保 AnythingLLM 服务已启动并可访问
2. 正确配置 API 密钥和工作区 slug
3. 如果遇到错误，请参考 http://localhost:3001/api/docs/ 的文档
4. 确保网络连接正常，curl 命令可以正常执行
