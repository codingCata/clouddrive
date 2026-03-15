# CloudDrive - Personal Network Storage System

## 1. Project Overview

- **Project Name**: CloudDrive
- **Type**: Web Application (Cloud Storage)
- **Core Functionality**: A personal network drive system supporting file upload, download, and user-specific storage isolation
- **Target Users**: Individual users needing personal file storage with authentication

---

## 2. Technical Stack

| Layer | Technology |
|-------|------------|
| Backend | Python Flask + SQLite |
| Frontend | Vanilla HTML/CSS/JS |
| File Storage | Local filesystem (per-user directories) |
| Authentication | Session-based with password hashing |

---

## 3. UI/UX Specification

### 3.1 Design System

#### Color Palette
| Role | Color | Hex |
|------|-------|-----|
| Background | Off-white | `#f8f9fa` |
| Surface | Pure White | `#ffffff` |
| Primary | Deep Slate | `#2d3748` |
| Accent | Warm Amber | `#dd6b20` |
| Text Primary | Charcoal | `#1a202c` |
| Text Secondary | Cool Gray | `#718096` |
| Border | Light Gray | `#e2e8f0` |
| Success | Forest Green | `#38a169` |
| Danger | Crimson | `#e53e3e` |

#### Typography
- **Font Family**: `"DM Sans", system-ui, sans-serif`
- **Headings**: 600 weight
- **Body**: 400 weight
- **Sizes**: H1: 28px, H2: 20px, Body: 14px, Small: 12px

#### Spacing
- Base unit: 4px
- Common: 8px, 12px, 16px, 24px, 32px

### 3.2 Layout Structure

#### Login Page
```
┌─────────────────────────────────────────┐
│            CloudDrive                   │  ← Logo/Title (centered)
│                                         │
│         ┌───────────────────┐          │
│         │   Username        │          │  ← Input field
│         └───────────────────┘          │
│         ┌───────────────────┐          │
│         │   Password        │          │  ← Input field
│         └───────────────────┘          │
│                                         │
│         ┌───────────────────┐          │
│         │      Login        │          │  ← Primary button
│         └───────────────────┘          │
│                                         │
│    ┌─────────────────────────────┐      │
│    │  Register new account →     │      │  ← Secondary link
│    └─────────────────────────────┘      │
└─────────────────────────────────────────┘
```

#### Register Page (Modal/Expandable)
```
┌─────────────────────────────────────────┐
│         ┌───────────────────┐          │
│         │  Confirm Password  │          │  ← Additional field
│         └───────────────────┘          │
│         ┌───────────────────┐          │
│         │    Register        │          │
│         └───────────────────┘          │
└─────────────────────────────────────────┘
```

#### Dashboard (Main View)
```
┌──────────────────────────────────────────────────────┐
│  ☁ CloudDrive                    [User Avatar] ▼    │  ← Header
├──────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐  │
│  │ ▼ User Info (collapsed by default)             │  │  ← Collapsible
│  │   Username: john_doe                           │  │
│  │   Storage Used: 2.4 GB / 10 GB                │  │
│  │   [Logout]                                     │  │
│  └─────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │  📁 Documents/                                │   │  ← Folder
│  │  📄 report.pdf              2.4 MB   🗑️ 📥   │   │  ← File row
│  │  🖼️ photo.jpg                1.2 MB   🗑️ 📥   │   │
│  │  📄 notes.txt               12 KB    🗑️ 📥   │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│            ┌────────────────────┐                    │
│            │  + Upload File     │                    │  ← Upload button
│            └────────────────────┘                    │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 3.3 Components

#### Buttons
| Type | Style |
|------|-------|
| Primary | Background: `#dd6b20`, text white, border-radius 8px |
| Secondary | Background: transparent, border `#e2e8f0`, text `#2d3748` |
| Danger | Background: `#e53e3e`, text white |
| Icon Button | 32x32px, hover background `#f7fafc` |

#### Input Fields
- Border: 1px solid `#e2e8f0`
- Border-radius: 8px
- Padding: 12px 16px
- Focus: Border `#dd6b20`, subtle shadow

#### File/Folder Row
- Height: 48px
- Hover: Background `#f7fafc`
- Icon: 24px, color `#718096`
- Actions: Appear on hover

#### Collapsible Panel
- Header with chevron icon (rotate on expand)
- Smooth height transition (200ms)
- Default: collapsed

### 3.4 Animations
- Panel expand/collapse: 200ms ease
- Button hover: 150ms
- File delete: fade out 200ms
- Page transitions: fade 150ms

---

## 4. Functionality Specification

### 4.1 Authentication

| Feature | Description |
|---------|-------------|
| Register | Username (unique), password (hashed with bcrypt) |
| Login | Session-based, 24h expiration |
| Logout | Clear session, redirect to login |
| Session | Flask session with user_id |

### 4.2 File Management

| Feature | Description |
|---------|-------------|
| Upload | Single file, drag-drop or button, progress indicator |
| Download | Direct file download, original filename |
| Delete | Confirmation prompt, permanent deletion |
| List | Show all files in user's storage, sort by name/date/size |
| Folders | Single level (flat structure for simplicity) |

### 4.3 User Isolation

| Feature | Description |
|---------|-------------|
| Storage Path | `storage/{user_id}/` |
| Session | Files only accessible to authenticated owner |
| API | All endpoints verify user session |

### 4.4 User Info Panel

| Feature | Description |
|---------|-------------|
| Collapsed by default | Click to expand |
| Show | Username, storage used/total, storage percentage bar |
| Actions | Logout button |

---

## 5. API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/register` | Create new user |
| POST | `/api/login` | User login |
| POST | `/api/logout` | User logout |
| GET | `/api/files` | List user's files |
| POST | `/api/upload` | Upload file |
| GET | `/api/download/<filename>` | Download file |
| DELETE | `/api/delete/<filename>` | Delete file |
| GET | `/api/user` | Get user info |

---

## 6. Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Files Table
```sql
CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    filesize INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## 7. File Structure

```
clouddrive/
├── app.py                 # Flask application
├── requirements.txt       # Dependencies
├── storage/              # User file storage (created dynamically)
│   └── {user_id}/
├── static/
│   ├── style.css         # Styles
│   └── script.js         # Frontend logic
└── templates/
    ├── login.html        # Login page
    └── dashboard.html    # Main dashboard
```

---

## 8. Acceptance Criteria

### Authentication
- [ ] User can register with unique username
- [ ] User can login with correct credentials
- [ ] Invalid login shows error message
- [ ] Logout clears session and redirects

### File Management
- [ ] User can upload files
- [ ] Uploaded files appear in file list
- [ ] User can download their own files
- [ ] User can delete their own files
- [ ] Files are stored in isolated user directories

### UI/UX
- [ ] Login page matches design spec
- [ ] Dashboard shows file list with icons
- [ ] User info panel is collapsible
- [ ] Storage usage displayed with progress bar
- [ ] Responsive on desktop (min 768px width)

### Security
- [ ] Users cannot access other users' files
- [ ] Passwords are hashed
- [ ] Sessions are validated on all protected routes
