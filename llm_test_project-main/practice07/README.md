# Practice07: 文章初始化与生成系统

## 项目简介

本项目基于init-article技能，实现了一个完整的文章生成系统。系统能够：
1. 根据用户需求自动生成四个写作约束规则文件
2. 使用这些规则生成符合要求的文章内容

## 核心功能

### 1. 写作规则生成
根据用户输入的文章主题或需求，自动生成四个约束规则文件：

| 文件 | 功能定位 |
|------|----------|
| `topic.md` | 主题锚定规范 - 防止跑题、AI自说自话 |
| `voice.md` | 语气风格规范 - 设定写作语气和风格 |
| `structure.md` | 文档结构规范 - 定义文章结构和提纲 |
| `check.md` | 质量检查规范 - 确保文章质量达标 |

### 2. 文章生成
使用生成的规则文件作为约束，调用LLM生成符合要求的文章内容。

## 使用方法

1. 确保 `.env` 文件中配置了正确的 `BASE_URL`、`MODEL_NAME` 和 `API_TOKEN`
2. 运行 `python chat_client.py` 启动系统
3. 选择操作：
   - 选项1：仅生成写作规则
   - 选项2：生成规则并撰写完整文章
   - 选项3：退出

## 项目结构

```
practice07/
├── chat_client.py          # 主程序文件
├── SKILL.md                # init-article技能定义
├── assets/                 # 规则示例文件
│   ├── topic-example.md    # 主题锚定规范示例
│   ├── voice-example.md    # 语气风格规范示例
│   ├── structure-example.md# 文档结构规范示例
│   └── check-example.md    # 质量检查规范示例
└── README.md               # 项目说明文档
```

## 输出文件

运行后会在 `article_rules/` 目录下生成：
- `topic.md` - 主题规范
- `voice.md` - 语气风格规范
- `structure.md` - 结构规范
- `check.md` - 质量检查规范
- `article.md` - 最终生成的文章（仅选项2）

## 依赖项

- Python 3.6+
- `python-dotenv` 库
- 一个支持工具调用的LLM API

## 配置说明

在 `.env` 文件中配置：
```
BASE_URL=https://your-llm-api-endpoint
MODEL_NAME=your-model-name
API_TOKEN=your-api-token
```

## 使用示例

### 示例1：生成技术报告规则
```
请输入文章主题或需求: 撰写一篇关于微服务架构的技术报告

生成的规则文件将包含：
- topic.md: 定义微服务架构报告的核心命题和边界
- voice.md: 设定技术报告的专业语气
- structure.md: 定义技术报告的章节结构
- check.md: 定义技术报告的质量检查标准
```

### 示例2：生成读书心得规则
```
请输入文章主题或需求: 写一篇《深入理解计算机系统》的读书心得

生成的规则文件将针对读书心得类型进行定制，包含：
- 书籍定位和核心论点梳理要求
- 个人化、思辨性的语气风格
- 读书心得特有的章节结构
- 原创性和思考深度的检查标准
```
