"""
项目 README - Python 学习项目说明文档
==========================================

本文件用于记录项目中各个 Python 代码的功能用途及实现的教学目标。

---

更新记录
========

**2026-05-19 修复更新**
- **Issue1**: 修复 practice02/chat_interface.py 中的 API 路径构建逻辑错误，使用 urlparse 直接从 BASE_URL 中解析路径部分，避免路径重复
- **Issue2**: 修复 practice03/chat_analytics.py 和 practice04/chat_analytics.py 中的 HTTP 连接池复用问题，http.client 连接不支持复用，改为每次请求创建新连接
- **Issue3**: 修复 practice04/anythingllm_query.py 中的安全隐患，将 subprocess 调用 curl 替换为 requests 库，消除命令注入风险
- **Issue4 & Issue5**: 经检查，practice03/chat_compression.py 和 practice04/chat_compression.py 中的函数调用参数匹配，无需修改

**2026-05-19 代码优化**
- **practice01/llm_client.py**: 添加配置验证函数 `validate_config()`，优化错误处理（区分 HTTP 错误、JSON 解析错误），支持从 BASE_URL 中解析 API 路径
- **practice02/tool_calling.py**: 添加 `get_api_path()` 函数，使用 urlparse 解析 API 路径避免硬编码，增加超时设置和错误处理优化
- **practice04/chat_client.py**: 添加 `get_api_path()` 函数，统一 API 路径解析方式，优化错误处理
- **新增文档**: 为 practice01、practice02、practice03 添加 README.md 文档

---

项目结构
========

├── practice01/             # 第一个教学实践
│   └── llm_client.py       # 基础 LLM API 调用
├── practice02/             # 第二个教学实践
│   ├── chat_interface.py   # 终端聊天界面（支持流式输出和历史记录）
│   └── tool_calling.py     # 工具调用系统（文件操作功能）
├── practice03/             # 第三个教学实践
│   ├── chat_compression.py # 聊天记录压缩系统
│   └── chat_analytics.py   # 聊天分析系统（关键信息提取和搜索）
├── practice04/             # 第四个教学实践
│   ├── chat_client.py      # 集成聊天客户端（支持AnythingLLM查询）
│   ├── anythingllm_query.py# AnythingLLM文档仓库查询工具
│   ├── chat_analytics.py   # 聊天分析系统
│   └── chat_compression.py # 聊天压缩系统
├── practice05/             # 第五个教学实践
│   ├── chat_client.py      # 集成聊天客户端（支持技能加载）
│   ├── test_skills.py      # 技能测试脚本
│   ├── test_notice.py      # 通知撰写测试
│   └── test_national_day.py# 国庆节通知测试
├── practice06/             # 第六个教学实践
│   ├── chat_client.py      # 集成聊天客户端（支持链式调用）
│   ├── FIXES.md            # 修复记录
│   └── weather_report.txt  # 天气报告示例输出
├── practice07/             # 第七个教学实践
│   ├── chat_client.py      # 文章生成系统
│   ├── init-article/       # 文章初始化技能
│   │   ├── SKILL.md        # 技能定义
│   │   └── assets/         # 规则示例文件
│   ├── article.txt         # 生成的文章
│   └── 工作流程.md         # 工作流程文档
├── .agents/                # 技能目录
│   └── skills/             # 技能定义
│       ├── notice/         # 通知撰写技能
│       └── init-article/   # 文章初始化技能
├── chat-log/               # 聊天日志目录
├── repo/                   # 项目报告目录
│   └── report.md           # 项目报告
├── test.py                 # 基础测试文件
├── .env.example            # 环境配置示例
├── .gitignore              # Git 忽略文件
├── requirements.txt        # 项目依赖
└── README.py               # 项目说明文档

---

教学实践详情
============

实践 1: 基础 LLM API 调用 (practice01/llm_client.py)
---------------------------------------------------
功能用途:
    - 演示如何通过原生 Python http.client 模块调用大语言模型(LLM) API
    - 展示如何从 .env 文件加载环境配置（使用 dotenv 库）
    - 演示 HTTP/HTTPS POST 请求的构建和发送
    - 实现与 LLM 的简单对话交互

实现的技术点:
    - os.getenv() - 读取系统环境变量
    - dotenv.load_dotenv() - 加载 .env 配置文件
    - http.client.HTTPConnection / HTTPSConnection - 建立 HTTP 连接
    - json.dumps() - 序列化 Python 对象为 JSON 字符串
    - urllib.parse.urlparse() - 解析 URL
    - API 调用格式（OpenAI 兼容的 /v1/chat/completions 接口）

教学目标:
    - 理解客户端如何与 LLM API 服务进行通信
    - 掌握 HTTP 请求的基本原理和构造方法
    - 学习环境变量管理敏感配置信息
    - 了解 JSON 数据格式在 API 通信中的应用

运行命令:
    python practice01/llm_client.py

---

实践 2: 终端聊天界面 (practice02/chat_interface.py)
--------------------------------------------------
功能用途:
    - 实现交互式终端聊天界面
    - 支持流式输出（实时显示 AI 回复）
    - 自动维护聊天历史记录
    - 支持按 Ctrl+C 退出程序

实现的技术点:
    - 流式响应处理（Streaming Response）
    - 聊天历史上下文管理
    - 异常处理（KeyboardInterrupt）
    - 实时输出和用户输入处理
    - 模块化函数设计

教学目标:
    - 学习如何处理流式 API 响应
    - 理解对话上下文管理的重要性
    - 掌握终端界面的用户交互设计
    - 学习异常处理和程序控制流

运行命令:
    python practice02/chat_interface.py

---

实践 2: 工具调用系统 (practice02/tool_calling.py)
--------------------------------------------------
功能用途:
    - 实现基于 LLM 的工具调用系统
    - 提供 5 个文件操作工具：列出文件、重命名文件、删除文件、创建文件、读取文件
    - 支持通过自然语言指令调用工具
    - 自动处理工具调用和结果处理

实现的技术点:
    - OpenAI 兼容的工具调用格式
    - 函数参数解析和执行
    - 文件系统操作（os 模块）
    - 工具调用流程管理
    - 多轮对话上下文处理

教学目标:
    - 理解 LLM 工具调用的工作原理
    - 学习如何设计和实现工具调用系统
    - 掌握文件系统操作的基本方法
    - 了解如何将工具能力集成到 LLM 应用中

运行命令:
    python practice02/tool_calling.py

---

实践 3: 聊天记录压缩系统 (practice03/chat_compression.py)
--------------------------------------------------------
功能用途:
    - 实现聊天记录自动压缩功能
    - 当聊天历史超过5轮或上下文长度超过3k时自动触发压缩
    - 对前70%的聊天内容进行压缩，保留最后30%的内容
    - 支持流式输出和正常的聊天交互

实现的技术点:
    - 聊天上下文长度计算
    - 自动压缩触发机制
    - 非流式响应处理（用于生成摘要）
    - 聊天历史管理和重组
    - 基于比例的内容分割

教学目标:
    - 学习如何管理和优化长对话上下文
    - 理解聊天记录压缩的重要性
    - 掌握不同响应模式的处理方法
    - 学习如何设计智能的上下文管理策略

运行命令:
    python practice03/chat_compression.py

---

实践 3: 聊天分析系统 (practice03/chat_analytics.py)
--------------------------------------------------------
功能用途:
    - 实现关键信息提取功能（每5次聊天提取一次）
    - 按照5W原则（Who、What、When、Where、Why）提取关键信息
    - 支持多模型部署（qwen3.5-9b和qwen2.5-3b的全量和轻量部署）
    - 实现聊天记录搜索功能（使用/search开头或相关关键词）
    - 增量更新日志到本地文件系统

实现的技术点:
    - 多模型配置管理
    - 关键信息提取和5W原则应用
    - 日志系统设计和文件操作
    - 聊天历史搜索功能
    - 命令模式识别（/search命令）

教学目标:
    - 学习如何设计多模型部署系统
    - 理解关键信息提取的重要性和方法
    - 掌握日志系统的设计和实现
    - 学习如何实现聊天历史搜索功能
    - 理解命令模式在对话系统中的应用

运行命令:
    python practice03/chat_analytics.py

---

实践 4: AnythingLLM 文档仓库查询 (practice04/)
--------------------------------------------------------
功能用途:
    - 集成 AnythingLLM 文档仓库查询能力
    - 当用户提到"文档仓库"、"文件仓库"、"仓库"时自动调用查询
    - 通过 subprocess 调用 curl 命令访问 AnythingLLM API
    - 支持中文编码的查询和响应

实现的技术点:
    - subprocess 模块调用外部命令
    - AnythingLLM API 集成
    - 工作区（Workspace）管理
    - 环境变量配置（ANYTHINGLLM_API_KEY、ANYTHINGLLM_WORKSPACE_SLUG）
    - 工具调用系统集成

教学目标:
    - 学习如何集成外部服务和 API
    - 理解文档检索和问答系统的工作原理
    - 掌握 subprocess 模块的使用方法
    - 了解如何将新工具集成到现有系统中

运行命令:
    python practice04/chat_client.py

---

实践 5: 技能加载与使用系统 (practice05/)
--------------------------------------------------------
功能用途:
    - 自动扫描 .agents/skills/ 目录读取可用技能列表
    - 解析 SKILL.md 文件的 YAML front matter 提取技能元数据
    - 将技能列表以 JSON 格式通过 system prompt 发送给 LLM
    - 当 LLM 需要使用技能时，动态加载技能详细内容

实现的技术点:
    - 目录扫描和文件遍历
    - YAML front matter 解析
    - 技能元数据提取（name、description）
    - 技能内容动态加载
    - 技能驱动的任务执行流程

教学目标:
    - 学习如何设计模块化的技能系统
    - 理解技能驱动架构的优势
    - 掌握 YAML front matter 的解析方法
    - 了解动态能力加载的设计模式

运行命令:
    python practice05/chat_client.py

---

实践 6: 链式工具调用系统 (practice06/)
--------------------------------------------------------
功能用途:
    - 实现链式工具调用（Chained Tool Calls）功能
    - LLM 根据中间结果自主决定下一个工具调用
    - 通过 ChainedCallContext 上下文管理器传递数据和状态
    - 支持最多 10 步迭代推理，防止无限循环

实现的技术点:
    - ChainedCallContext 上下文管理器设计
    - 链式调用执行流程控制
    - 分析提示词构建（包含用户请求和已执行步骤历史）
    - JSON 响应解析与容错处理
    - 多格式响应支持（JSON content 和 tool_calls）
    - ANSI 转义字符清理

支持的工具:
    - list_files: 列出目录下的文件
    - search_files: 搜索包含关键词的文件
    - read_file: 读取文件内容
    - create_file: 创建文件
    - load_skill_content: 加载技能内容
    - fetch_webpage: 获取网页内容
    - list_available_skills: 获取可用技能列表

教学目标:
    - 学习如何设计多步骤任务执行流程
    - 理解上下文状态管理的重要性
    - 掌握 LLM 自主决策的实现方法
    - 了解链式调用中的错误处理和容错机制

运行命令:
    python practice06/chat_client.py

---

实践 7: 文章初始化与生成系统 (practice07/)
--------------------------------------------------------
功能用途:
    - 基于 init-article 技能实现完整的文章生成系统
    - 根据用户需求自动生成四个写作约束规则文件
    - 使用生成的规则作为约束，调用 LLM 生成符合要求的文章

四个写作规则文件:
    - topic.md: 主题锚定规范 - 防止跑题、AI自说自话
    - voice.md: 语气风格规范 - 设定写作语气和风格
    - structure.md: 文档结构规范 - 定义文章结构和提纲
    - check.md: 质量检查规范 - 确保文章质量达标

实现的技术点:
    - 技能驱动的任务编排
    - 多步骤规则生成流程
    - 约束条件下的内容生成
    - 文件保存和管理
    - 交互式菜单设计

教学目标:
    - 学习如何将技能系统应用于实际场景
    - 理解约束驱动的内容生成方法
    - 掌握多步骤任务流程的设计
    - 了解如何将 AI 能力应用于写作辅助

运行命令:
    python practice07/chat_client.py

---

基础文件
========

1. test.py
----------
功能用途:
    - 最基础的 Python 程序，用于验证开发环境和运行环境是否正常
    - 作为最简单的代码模板，用于测试文件创建和执行流程

实现的技术点:
    - print() 函数的基本使用

教学目标:
    - 确认 Python 解释器配置正确
    - 验证代码文件能够正常执行
    - 作为入门级测试文件

运行命令:
    python test.py

---

配置文件
========

1. .env
-------
用途说明:
    - 存储 API 相关的敏感配置信息
    - 包含以下配置项：
      - BASE_URL：API 服务器地址
      - MODEL_NAME：模型名称
      - API_TOKEN：访问令牌

注意事项:
    - 该文件包含敏感信息，不应提交到版本控制系统
    - 项目已配置 .gitignore 忽略此文件

2. requirements.txt
-------------------
项目依赖:
    - python-dotenv：用于加载 .env 配置文件
    - requests：用于网络请求

安装依赖:
    pip install -r requirements.txt

---

项目运行说明
============
1. 确保已安装 Python 3.x 环境
2. 安装项目依赖：pip install -r requirements.txt
3. 配置 .env 文件，填入真实的 API 地址、模型名称和访问令牌
4. 运行相应的实践文件：
   - 实践 1（基础LLM调用）：python practice01/llm_client.py
   - 实践 2（聊天界面）：python practice02/chat_interface.py
   - 实践 2（工具调用）：python practice02/tool_calling.py
   - 实践 3（聊天压缩）：python practice03/chat_compression.py
   - 实践 3（聊天分析）：python practice03/chat_analytics.py
   - 实践 4（AnythingLLM集成）：python practice04/chat_client.py
   - 实践 5（技能加载）：python practice05/chat_client.py
   - 实践 6（链式调用）：python practice06/chat_client.py
   - 实践 7（文章生成）：python practice07/chat_client.py
   - 基础测试：python test.py

---

项目演进路径
============
practice01 → practice02 → practice03 → practice04 → practice05 → practice06 → practice07
   |            |            |            |            |            |            |
  基础LLM     工具调用     对话管理     外部集成     技能系统     链式调用     实际应用
  API调用     流式输出     压缩分析     文档检索     动态加载     自主决策     文章生成

每个实践阶段都在前一阶段的基础上增加新的能力，逐步构建出完整的智能体系统。

---

未来规划
========
- 引入多智能体协作框架（如 CrewAI、AutoGen）
- 增强 JSON 解析鲁棒性，引入 json_repair 库
- 集成多模态能力（视觉模型、语音模型）
- 开发基于 Gradio 或 Streamlit 的 Web 界面
- 探索模型量化和缓存机制优化性能
"""
