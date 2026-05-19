# Practice06: 链式工具调用系统

## 项目简介

本项目基于practice05的chat_client.py文件，实现了链式工具调用（Chained Tool Calls）功能。该系统能够让LLM根据中间结果自主决定下一个工具调用，实现多步骤的自动化任务执行。

## 核心功能

### 1. 链式调用上下文管理器 `ChainedCallContext`

用于在多个工具之间传递数据和状态：
- 记录每一步的调用和结果
- 存储中间变量供后续步骤使用
- 设置最大迭代次数，防止无限循环

### 2. 链式调用执行函数 `execute_chained_tool_call`

实现链式工具调用的完整流程：
- 初始化消息历史，包含 system prompt
- 循环最多 `max_iterations` 次：
  - 构建分析提示词（包含用户请求和已执行的步骤历史）
  - 调用LLM决定下一步操作
  - 解析LLM响应（支持JSON格式和tool_calls格式）
  - 如果任务完成，返回最终回答
  - 如果需继续调用，执行工具并记录到上下文
  - 将结果添加到消息历史，继续下一轮

### 3. 分析提示词构建函数 `build_analysis_prompt`

提示词包含：
- 用户原始请求
- 已执行的工具调用历史（工具名、参数、结果）
- 决策规则说明
- JSON输出格式要求

### 4. LLM决策格式

LLM需要按照以下JSON格式返回决策：

**完成任务时：**
```json
{"done": true, "answer": "最终回答内容"}
```

**继续调用工具时：**
```json
{"done": false, "tool_call": {"name": "工具名称", "arguments": {"参数名": "参数值"}}}
```

## 支持的工具

| 工具名称 | 描述 | 参数 |
|---------|------|------|
| `list_files` | 列出目录下的文件 | `directory` - 目录路径 |
| `search_files` | 搜索包含关键词的文件 | `directory` - 目录路径, `keyword` - 关键词 |
| `read_file` | 读取文件内容 | `directory` - 目录路径, `filename` - 文件名 |
| `create_file` | 创建文件 | `directory` - 目录路径, `filename` - 文件名, `content` - 文件内容 |
| `load_skill_content` | 加载技能内容 | `skill_name` - 技能名称 |
| `fetch_webpage` | 获取网页内容 | `url` - 网页URL |
| `list_available_skills` | 获取可用技能列表 | 无 |

## 系统提示词规则

在system prompt中明确了链式调用的规则：
- 说明工具调用的顺序依赖关系
- 指导LLM如何根据中间结果决定后续操作
- 提供链式调用的示例
- 说明上下文变量的使用方式（`$variable_name`）

## 使用方法

1. 确保 `.env` 文件中配置了正确的 `BASE_URL`、`MODEL_NAME` 和 `API_TOKEN`
2. 运行 `python chat_client.py` 启动系统
3. 选择操作：
   - 运行测试（预设的三个测试用例）
   - 直接输入请求

## 测试用例

### 测试1：文件搜索链式调用
- 输入："请查找practice05目录下的所有包含'def'关键词的文件，并总结这些文件的主要内容"
- 预期：系统会先搜索文件，然后读取每个匹配的文件，最后总结内容

### 测试2：技能查询链式调用
- 输入："我想了解notice技能的详细规则"
- 预期：系统会先获取技能列表，然后加载notice技能的详细内容

### 测试3：网页处理链式调用
- 输入："访问https://www.nsu.edu.cn/HTML/news/2024/06/article_3974.html并总结页面内容，保存到practice06/summary.txt"
- 预期：系统会先获取网页内容，然后总结，最后保存到文件

## 项目结构

```
practice06/
├── chat_client.py          # 主程序文件，包含链式调用实现
├── test_chained_calls.py   # 链式调用测试脚本
└── README.md               # 项目说明文档
```

## 依赖项

- Python 3.6+
- `python-dotenv` 库
- 一个支持工具调用的LLM API

## 注意事项

1. **JSON解析**：LLM可能返回包含markdown代码块标记（如```json）的内容，系统会先提取JSON部分再解析
2. **响应格式**：系统同时支持 `tool_calls` 格式（OpenAI标准Function Calling格式）和JSON `content` 格式
3. **错误处理**：检查LLM响应是否为None，处理JSON解析失败的情况，处理工具执行异常
4. **防止无限循环**：设置 `max_iterations` 限制最大迭代次数（默认10次）
