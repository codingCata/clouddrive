# CloudDrive

[中文版](./README_zh.md) | English

A lightweight personal cloud storage system.

## Pain Points & Solutions

| Pain Point | Solution |
|------------|----------|
| Complex commercial cloud drives | Minimal feature set - only file/folder management |
| Privacy concerns | Self-hosted, data stays on your server |
| Hard to integrate with AI | Built-in API + AI Skill for seamless AI integration |
| Difficult deployment | One-command Docker deployment |

## Key Features

- **Self-hosted**: Your data, your control
- **AI-Ready**: RESTful API + API Key auth for AI agents
- **Simple**: File upload/download, folder management - nothing more
- **Lightweight**: Python + SQLite, no heavy dependencies
- **Docker**: One-command deployment

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python3 app.py
```

Visit `http://localhost:5051`

### Docker Deployment

```bash
# Build and start
docker compose up -d --build

# Stop
docker compose down
```

Visit `http://localhost:5051`

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | Auto-generated | Flask secret key |
| `STORAGE_DIR` | `./storage` | File storage directory |
| `DB_PATH` | `./clouddrive.db` | Database path |

### Docker Example

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

## Project Structure

```
clouddrive/
├── app.py                    # Main application entry
├── clouddrive/              # Main package
│   ├── __init__.py         # Flask app factory
│   ├── auth.py              # Authentication
│   ├── constants.py         # Constants
│   ├── models.py            # Database models
│   ├── routes/              # API blueprints
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── files.py
│   │   ├── folders.py
│   │   ├── user.py
│   │   └── api_key.py
│   └── utils/
│       └── storage.py       # Storage utilities
├── config.py                 # Legacy config (compatibility)
├── models.py                # Legacy models (compatibility)
├── auth.py                  # Legacy auth (compatibility)
├── routes.py                # Legacy routes (compatibility)
├── Dockerfile               # Docker image
├── docker-compose.yml       # Docker compose
├── requirements.txt         # Python dependencies
├── templates/              # HTML templates
├── static/                 # CSS/JS
└── storage/                # File storage (created at runtime)
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/register` | Register new user |
| POST | `/api/login` | User login |
| POST | `/api/logout` | User logout |
| GET | `/api/user` | Get user info |
| GET | `/api/files` | List files (supports pagination) |
| GET | `/api/search` | Search files |
| POST | `/api/upload` | Upload file |
| GET | `/api/download/<filename>` | Download file |
| GET | `/api/preview/<filename>` | Preview file |
| DELETE | `/api/delete/<filename>` | Delete file |
| POST | `/api/folders` | Create folder |
| DELETE | `/api/folders/<id>` | Delete folder |
| POST | `/api/batch-delete` | Batch delete files/folders |
| POST | `/api/batch-download` | Batch download files (ZIP) |
| POST | `/api/change-password` | Change password |
| POST | `/api/api-key` | Generate API key |
| GET | `/api/api-key` | Get API key info |
| DELETE | `/api/api-key` | Delete API key |
| GET | `/api/ai-docs` | AI API documentation |

## AI Integration

Generate an API key for AI agents to access your cloud storage:

```bash
# 1. Login to get session cookie
curl -X POST http://localhost:5051/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"your_user","password":"your_password"}' -c cookies.txt

# 2. Generate API key
curl -X POST http://localhost:5051/api/api-key -b cookies.txt
# Returns: {"api_key":"your-key-here"}

# 3. Use API key for subsequent requests
curl http://localhost:5051/api/files \
  -H "X-API-Key: your-key-here"

curl http://localhost:5051/api/user \
  -H "X-API-Key: your-key-here"
```

Get full API docs:
```bash
curl http://localhost:5051/api/ai-docs
```

## Tech Stack

- Backend: Python Flask + SQLite
- Frontend: Vanilla HTML/CSS/JS
- Authentication: Session + bcrypt
- Deployment: Docker
