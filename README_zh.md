# CloudDrive

[English](./README.md) | 中文版

轻量级个人云存储系统。

## 痛点与解决方案

| 痛点 | 解决方案 |
|------|---------|
| 复杂的商业网盘 | 最小功能集 - 仅文件/文件夹管理 |
| 隐私担忧 | 自托管，数据保留在您的服务器上 |
| AI 集成困难 | 内置 API + AI Skill，无缝 AI 集成 |
| 部署困难 | 一键 Docker 部署 |

## 核心功能

- **自托管**: 您的数据，您做主
- **AI  Ready**: RESTful API + API Key 认证，支持 AI 代理
- **简洁**: 文件上传/下载、文件夹管理 - 仅此而已
- **轻量**: Python + SQLite，无重量级依赖
- **Docker**: 一键部署

## 快速开始

### 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 运行应用
python3 app.py
```

访问 `http://localhost:5051`

### Docker 部署

```bash
# 构建并启动
docker compose up -d --build

# 停止
docker compose down
```

访问 `http://localhost:5051`

## 配置

### 环境变量

| 变量 | 默认值 | 描述 |
|------|--------|------|
| `SECRET_KEY` | 自动生成 | Flask 密钥 |
| `STORAGE_DIR` | `./storage` | 文件存储目录 |
| `DB_PATH` | `./clouddrive.db` | 数据库路径 |

### Docker 示例

```yaml
# docker-compose.yml
services:
  clouddrive:
    build: .
    ports:
      - "5051:5051"
    environment:
      - STORAGE_DIR=/data/storage
      - DB_PATH=/data/clouddrive.db
    volumes:
      - /your/custom/path:/data
    restart: unless-stopped
```

## 项目结构

```
clouddrive/
├── app.py                    # 主应用入口
├── clouddrive/              # 主包
│   ├── __init__.py         # Flask 应用工厂
│   ├── auth.py              # 认证
│   ├── constants.py         # 常量
│   ├── models.py            # 数据库模型
│   ├── routes/              # API 蓝图
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── files.py
│   │   ├── folders.py
│   │   ├── user.py
│   │   └── api_key.py
│   └── utils/
│       └── storage.py       # 存储工具
├── config.py                 # 旧版配置（兼容）
├── models.py                # 旧版模型（兼容）
├── auth.py                  # 旧版认证（兼容）
├── routes.py                # 旧版路由（兼容）
├── Dockerfile               # Docker 镜像
├── docker-compose.yml       # Docker Compose
├── requirements.txt         # Python 依赖
├── templates/              # HTML 模板
├── static/                 # CSS/JS
└── storage/                # 文件存储（运行时创建）
```

## API 端点

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/register` | 注册新用户 |
| POST | `/api/login` | 用户登录 |
| POST | `/api/logout` | 用户登出 |
| GET | `/api/user` | 获取用户信息 |
| GET | `/api/files` | 列出文件（支持分页） |
| GET | `/api/search` | 搜索文件 |
| POST | `/api/upload` | 上传文件 |
| GET | `/api/download/<filename>` | 下载文件 |
| GET | `/api/preview/<filename>` | 预览文件 |
| DELETE | `/api/delete/<filename>` | 删除文件 |
| POST | `/api/folders` | 创建文件夹 |
| DELETE | `/api/folders/<id>` | 删除文件夹 |
| POST | `/api/batch-delete` | 批量删除文件/文件夹 |
| POST | `/api/batch-download` | 批量下载文件（ZIP） |
| POST | `/api/change-password` | 修改密码 |
| POST | `/api/api-key` | 生成 API 密钥 |
| GET | `/api/api-key` | 获取 API 密钥信息 |
| DELETE | `/api/api-key` | 删除 API 密钥 |
| GET | `/api/ai-docs` | AI API 文档 |

## AI 集成

为 AI 代理生成 API 密钥以访问您的云存储：

```bash
# 1. 登录获取会话 cookie
curl -X POST http://localhost:5051/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"your_user","password":"your_password"}' -c cookies.txt

# 2. 生成 API 密钥
curl -X POST http://localhost:5051/api/api-key -b cookies.txt
# 返回: {"api_key":"your-key-here"}

# 3. 使用 API 密钥进行后续请求
curl http://localhost:5051/api/files \
  -H "X-API-Key: your-key-here"

curl http://localhost:5051/api/user \
  -H "X-API-Key: your-key-here"
```

获取完整 API 文档：
```bash
curl http://localhost:5051/api/ai-docs
```

## 技术栈

- 后端: Python Flask + SQLite
- 前端: 原生 HTML/CSS/JS
- 认证: Session + bcrypt
- 部署: Docker
