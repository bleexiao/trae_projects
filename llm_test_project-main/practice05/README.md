# Practice05: 技能加载与使用系统

## 项目简介

本项目基于practice04的chat_client.py文件，实现了一个技能加载与使用系统。该系统能够：

1. 自动读取技能列表，提取每个技能的名称和描述
2. 将技能列表以JSON格式通过system prompt发送给LLM
3. 当LLM需要使用某个技能时，加载该技能的详细内容

## 核心功能

### 1. 技能列表读取

`list_available_skills()` 函数会：
- 扫描 `.agents/skills` 目录下的所有子目录
- 读取每个子目录中的 `SKILL.md` 文件
- 提取YAML front matter中的 `name` 和 `description` 字段
- 返回格式化的技能列表

### 2. 技能内容加载

`load_skill_content(skill_name)` 函数会：
- 根据技能名称找到对应的技能目录
- 读取 `SKILL.md` 文件的正文内容（YAML front matter之后的部分）
- 返回技能的详细内容

### 3. 技能使用流程

1. 系统启动时自动读取所有可用技能
2. 将技能列表以JSON格式发送给LLM
3. 当用户请求涉及到特定技能时，LLM会调用 `load_skill_content` 工具
4. 系统加载技能内容并发送给LLM
5. LLM根据技能内容生成相应的响应

## 测试技能

本项目包含一个 `notice` 技能，用于撰写、修改和润色通知。该技能要求：

- 通知不能以"通知"二字开头
- 必须冠以"xx部"的前缀，例如"采购部通知"、"宣传部通知"等
- 如果用户没有告知所在部门，就使用"xx部"代替

## 使用方法

1. 确保 `.env` 文件中配置了正确的 `BASE_URL`、`MODEL_NAME` 和 `API_TOKEN`
2. 运行 `python chat_client.py` 启动系统
3. 输入需要撰写通知的请求，例如：
   - "撰写关于五一节放假的通知"
   - "我是销售部的，撰写关于五一节放假的通知"

## 测试结果

### 测试1：不指定部门
- 输入："撰写关于五一节放假的通知"
- 预期输出：通知应以"xx部通知"开头

### 测试2：指定销售部
- 输入："我是销售部的，撰写关于五一节放假的通知"
- 预期输出：通知应以"销售部通知"开头

## 项目结构

```
practice05/
├── chat_client.py          # 主程序文件
├── test_skills.py          # 技能测试脚本
└── README.md               # 项目说明文档
```

## 依赖项

- Python 3.6+
- `dotenv` 库
- 一个支持工具调用的LLM API

## 注意事项

- 技能文件必须放在 `.agents/skills` 目录下的子目录中
- 每个技能目录中必须包含 `SKILL.md` 文件
- `SKILL.md` 文件必须包含YAML front matter，其中包含 `name` 和 `description` 字段
- 技能的详细内容应放在YAML front matter之后