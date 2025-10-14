# OpenAI 代理服务

![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![Python: 3.9-3.12](https://img.shields.io/badge/python-3.9--3.12-green.svg)
![FastAPI](https://img.shields.io/badge/framework-FastAPI-009688.svg)

基于 FastAPI 的高性能 OpenAI API 兼容代理服务，采用多提供商架构设计，支持 Z.AI（GLM-4.5/4.6 系列）、K2Think、LongCat 等多种 AI 模型。

## ✨ 核心特性

- 🔌 **OpenAI API 兼容** - 无缝对接现有 OpenAI 客户端
- 🏗️ **多提供商架构** - 统一接口支持 Z.AI、K2Think、LongCat
- 🧬 **数据库管理** - SQLite + Web 后台统一管理 Token
- 🚀 **流式响应** - 高性能 SSE 实时流式输出
- 🧠 **思考模式** - 支持 Thinking 模型的推理过程展示
- 🐳 **容器化部署** - Docker/Docker Compose 一键部署
- 🔄 **Token 池** - 智能轮询、容错恢复、健康检查
- 📊 **管理后台** - 实时监控、配置管理

## 🚀 快速开始

### 方法 1: 自动化脚本（推荐） ⚡

**一键完成所有设置、启动并测试服务器：**

```bash
# 1. 克隆项目
git clone https://github.com/Zeeeepa/z.ai2api_python.git
cd z.ai2api_python

# 2. 设置环境变量
export ZAI_EMAIL=your-email@example.com
export ZAI_PASSWORD=your-password

# 3. 运行自动化脚本
bash scripts/all.sh
```

这将自动完成：
- ✅ 安装所有依赖（Python + Playwright）
- ✅ 通过 Playwright 自动登录并获取认证令牌
- ✅ 在 8080 端口启动服务器
- ✅ 发送测试请求验证 API 功能
- ✅ 显示实时日志

**单独运行脚本：**

```bash
# 仅环境设置和令牌获取
bash scripts/setup.sh

# 仅启动服务器
bash scripts/start.sh

# 仅测试 API
bash scripts/send_openai_request.sh
```

📖 详细文档请参阅 [scripts/README.md](scripts/README.md)

---

### 方法 2: 手动安装

**环境要求：**
- Python 3.9-3.12
- pip 或 uv (推荐)

**步骤：**

```bash
# 1. 克隆项目
git clone https://github.com/Zeeeepa/z.ai2api_python.git
cd z.ai2api_python

# 2. 安装依赖（使用 uv 推荐）
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync

# 或使用 pip
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置 AUTH_TOKEN 等配置

# 4. 启动服务
uv run python main.py  # 或 python main.py
```

**首次运行会自动初始化数据库**，访问以下地址：
- API 文档：http://localhost:8080/docs
- 管理后台：http://localhost:8080/admin
- Token 管理：http://localhost:8080/admin/tokens

> ⚠️ **重要**：请妥善保管 `AUTH_TOKEN`，不要泄露给他人

### Docker 部署

#### 使用预构建镜像（推荐）

```bash
# 拉取镜像
docker pull zyphrzero/z-ai2api-python:latest

# 快速启动
docker run -d \
  --name z-ai2api \
  -p 8080:8080 \
  -e AUTH_TOKEN="sk-your-api-key" \
  -v $(pwd)/tokens.db:/app/tokens.db \
  zyphrzero/z-ai2api-python:latest
```

#### 使用 Docker Compose

创建 `docker-compose.yml`：

```yaml
version: '3.8'
services:
  z-ai2api:
    image: zyphrzero/z-ai2api-python:latest
    container_name: z-ai2api
    ports:
      - "8080:8080"
    environment:
      - AUTH_TOKEN=sk-your-api-key
      - ANONYMOUS_MODE=true
      - DEBUG_LOGGING=false
      - TOOL_SUPPORT=true
    volumes:
      - ./tokens.db:/app/tokens.db
    restart: unless-stopped
```

启动服务：

```bash
docker-compose up -d
```

> 💡 **数据持久化**：务必挂载 `tokens.db` 数据库文件以保存 Token 配置

## 📖 支持的模型

### Z.AI 提供商（GLM 系列）

| 模型 | 上游 ID | 特性 |
|------|---------|------|
| `GLM-4.5` | 0727-360B-API | 标准模型，通用对话 |
| `GLM-4.5-Thinking` | 0727-360B-API | 思考模型，显示推理过程 |
| `GLM-4.5-Search` | 0727-360B-API | 搜索模型，实时联网 |
| `GLM-4.5-Air` | 0727-106B-API | 轻量模型，快速响应 |
| `GLM-4.6` | GLM-4-6-API-V1 | 新版标准模型 |
| `GLM-4.6-Thinking` | GLM-4-6-API-V1 | 新版思考模型 |
| `GLM-4.6-Search` | GLM-4-6-API-V1 | 新版搜索模型 |

### K2Think 提供商

| 模型 | 特性 |
|------|------|
| `MBZUAI-IFM/K2-Think` | 高质量推理模型 |

### LongCat 提供商

| 模型 | 特性 |
|------|------|
| `LongCat-Flash` | 快速响应 |
| `LongCat` | 标准模型 |
| `LongCat-Search` | 搜索增强 |

## ⚙️ 配置说明

### 核心环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `AUTH_TOKEN` | `sk-your-api-key` | 客户端访问密钥（必填） |
| `LISTEN_PORT` | `8080` | 服务监听端口 |
| `DEBUG_LOGGING` | `false` | 调试日志（支持热重载） |
| `ANONYMOUS_MODE` | `true` | Z.AI 匿名模式 |
| `TOOL_SUPPORT` | `true` | Function Call 开关 |
| `SKIP_AUTH_TOKEN` | `false` | 跳过认证（仅开发） |

### Token 配置

| 变量名 | 说明 |
|--------|------|
| `LONGCAT_TOKEN` | LongCat 认证 Token（可选） |
| `TOKEN_FAILURE_THRESHOLD` | Token 失败阈值（默认 3） |
| `TOKEN_RECOVERY_TIMEOUT` | Token 恢复超时（默认 1800 秒） |

> 💡 详细配置请参考 [.env.example](.env.example)

## 🔄 Token 管理

### 数据库方式（推荐）

项目使用 SQLite 数据库统一管理 Token，首次运行会自动初始化：

```bash
# 首次运行自动创建 tokens.db
python main.py

# 访问 Web 管理后台
http://localhost:8080/admin
```

### 管理后台功能

- ✅ Token 增删改查
- ✅ 批量导入/导出
- ✅ 启用/禁用 Token
- ✅ Token有效性检测
- ✅ 多提供商支持（Z.AI/K2Think/LongCat）

### Token 池机制

- **负载均衡**：轮询使用多个 Token 分散请求
- **自动容错**：Token 失败时自动切换
- **自动恢复**：失败 Token 超时后重试
- **智能去重**：自动检测重复 Token
- **回退机制**：认证失败自动降级匿名模式

## ❓ 常见问题

### Q: 如何获取 AUTH_TOKEN？
A: `AUTH_TOKEN` 是自定义的 API 密钥，用于客户端访问本服务，需在 `.env` 文件中配置，确保客户端与服务端一致。

### Q: 匿名模式是什么？
A: 匿名模式使用临时 Token 访问 Z.AI，避免对话历史共享，保护隐私。设置 `ANONYMOUS_MODE=true` 启用。

### Q: 如何管理 Token？
A: 访问 Web 管理后台 http://localhost:8080/admin/tokens 即可增删改查 Token，支持批量导入导出。


## 🔑 获取 Token

### Z.AI Token

1. 访问 [Z.AI 官网](https://chat.z.ai) 并登录
2. 按 F12 打开开发者工具
3. 进入 Application → Local Storage → Cookies
4. 复制 `token` 值

> ⚠️ 多模态功能需要非匿名 Token

### LongCat Token

1. 访问 [LongCat 官网](https://longcat.chat/) 并登录美团账号
2. 按 F12 打开开发者工具
3. 进入 "Application" -> "Local Storage" -> "Cookie"列表中找到名为`passport_token_key`的值
4. 复制 `passport_token_key` 值

## 🛠️ 技术栈

| 组件 | 技术 | 版本 | 说明 |
|------|------|------|------|
| Web 框架 | [FastAPI](https://fastapi.tiangolo.com/) | 0.116.1 | 高性能异步框架 |
| ASGI 服务器 | [Granian](https://github.com/emmett-framework/granian) | 2.5.2 | Rust 高性能服务器 |
| HTTP 客户端 | [HTTPX](https://www.python-httpx.org/) | 0.28.1 | 异步 HTTP 客户端 |
| 数据验证 | [Pydantic](https://pydantic.dev/) | 2.11.7 | 类型安全验证 |
| 数据库 | SQLite (aiosqlite) | 0.20.0 | Token 存储 |
| 模板引擎 | Jinja2 | 3.1.4 | Web 后台模板 |
| 日志系统 | [Loguru](https://loguru.readthedocs.io/) | 0.7.3 | 结构化日志 |

## 🏗️ 系统架构

```
┌─────────────┐      ┌────────────────────────────────┐      ┌──────────────┐
│   OpenAI    │      │      FastAPI Server            │      │   Z.AI API   │
│   Client    │─────▶│                                │─────▶│   (GLM-4.x)  │
└─────────────┘      │  ┌──────────────────────────┐  │      └──────────────┘
                     │  │   Provider Router        │  │
                     │  │  ┌────────┬────────────┐ │  │      ┌──────────────┐
                     │  │  │ Z.AI   │ K2Think    │ │  │      │  K2Think API │
                     │  │  │Provider│ Provider   │ │  │─────▶│              │
                     │  │  └────────┴────────────┘ │  │      └──────────────┘
                     │  │  ┌────────────┐          │  │
                     │  │  │ LongCat    │          │  │      ┌──────────────┐
                     │  │  │ Provider   │          │  │      │ LongCat API  │
                     │  │  └────────────┘          │  │─────▶│              │
                     │  └──────────────────────────┘  │      └──────────────┘
                     │                                │
                     │  ┌──────────────────────────┐  │
                     │  │   Web Admin Dashboard    │  │
                     │  │   (Token/Stats/Monitor)  │  │
                     │  └──────────────────────────┘  │
                     └────────────────────────────────┘
                               ↕
                          ┌─────────┐
                          │SQLite DB│
                          │(tokens) │
                          └─────────┘
```

## 📚 相关文档

- [CLAUDE.md](CLAUDE.md) - 项目架构和 AI 使用指引
- [TOKEN_MIGRATION.md](docs/TOKEN_MIGRATION.md) - Token 数据库迁移指南
- [ADMIN_README.md](docs/ADMIN_README.md) - Web 管理后台使用手册
- [DEBUG_LOGGING_FIX.md](docs/DEBUG_LOGGING_FIX.md) - 调试日志热重载修复

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！请确保代码符合 PEP 8 规范。

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=ZyphrZero/z.ai2api_python&type=Date)](https://star-history.com/#ZyphrZero/z.ai2api_python&Date)

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## ⚠️ 免责声明

- 本项目与 Z.AI、K2Think、LongCat 等 AI 提供商官方无关
- 使用前请确保遵守各提供商的服务条款
- 请勿用于商业用途或违反使用条款的场景
- 项目仅供学习和研究使用
- 用户需自行承担使用风险

---

<div align="center">
Made with ❤️ by the community
</div>
