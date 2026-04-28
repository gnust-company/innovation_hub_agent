# Innovation Hub Agent — E2E Test Report

## Test 1: General knowledge

**Question:** Innovation Hub là gì?

### Agent Trace

**[USER]** Innovation Hub là gì?

**[AI — Tool Calls]**
- `read_file({'path': '00_Index/MOC_Overview.md'})`

**[AI — Answer]**
 Tôi sẽ tìm thông tin tổng quan về Innovation Hub trong wiki. 

**[Tool Result]**
```
---
type: moc
category: Index
related: ["MOC_For_Developers", "MOC_For_End_Users"]
tags: [index, overview]
updated: 2026-04-28
---

# MOC Overview

Innovation Hub là nền tảng nội bộ quản lý đổi mới sáng tạo, số hóa quy trình "Đăng → Thảo luận → Thực thi".

## Tech Stack
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS + TipTap rich text
- **Backend**: Python 3.11 + FastAPI + SQLAlchemy 2.0 (async)
- **Database**: PostgreSQL 16
- **Storage**: MinIO (avatars, files)
- **Deployment**: Do
```

**[AI — Answer]**
 ## Innovation Hub là gì?

**Innovation Hub** là nền tảng nội bộ quản lý đổi mới sáng tạo, được xây dựng để số hóa quy trình **"Đăng → Thảo luận → Thực thi"** cho các ý tưởng và vấn đề trong tổ chức.

---

### 🎯 Mục đích
Số hóa toàn bộ vòng đời của một ý tưởng đổi mới — từ khi ai đó phát hiện vấn đề, đến thảo luận, brainstorm, và cuối cùng là thực thi qua các sự kiện/competition.

---

### 🏗️ Tech Stack
| Layer | Công nghệ |
|-------|-----------|
| **Frontend** | React 18 + TypeScript + Vite + Tailwind CSS + TipTap (rich text) |
| **Backend** | Python 3.11 + FastAPI + SQLAlchemy 2.0 (async) |
| **Database** | PostgreSQL 16 |
| **Storage** | MinIO (avatars, files) |
| **Deployment** | Docker Compose + Nginx |

---

### 🚀 Core Features

**1. Problem Feed** — Đăng vấn đề, thảo luận, reaction  
**2. Idea Lab** — Brainstorming rooms, kanban board, star voting  
**3. Events** — Innovation events, team formation, scoring  
**4. Dashboard** — Statistics, analytics, tracking

---

### 👥 Phân quyền người dùng
- **member**: Người dùng thông thường
- **admin**: Quản trị viên hệ thống
- **team_lead**: Trưởng nhóm (theo từng sự kiện)

---

### 📋 Quy trình trạng thái chính

| Feature | Workflow |
|---------|----------|
| **Problem** | `open` → `discussing` → `brainstorming` → `solved/closed` |
| **Idea** | `draft` ↔ `refining` ↔ `reviewing` → `submitted/closed` |

---

### 🔒 Privacy Model
Hỗ trợ **Public/Private** với khả năng chia sẻ cho specific users.

---

*Source: `00_Index/MOC_Overview.md`*

---

## Test 2: Feature question

**Question:** Làm sao để tham gia một event?

### Agent Trace

**[USER]** Làm sao để tham gia một event?

**[AI — Tool Calls]**
- `read_file({'path': '08_User_Guide/MOC_User_Guide.md'})`
- `read_file({'path': '03_Events/MOC_Events.md'})`

**[AI — Answer]**
 Tôi sẽ tìm thông tin về cách tham gia event trong wiki. Để trả lời câu hỏi này, tôi cần đọc các tài liệu hướng dẫn người dùng và thông tin về Events. 

**[Tool Result]**
```
---
type: moc
category: User Guide
related: ["MOC_For_End_Users", "Quick_Start", "MOC_Problem_Feed"]
tags: [user-guide, index]
updated: 2026-04-28
---

# MOC User Guide

Hướng dẫn sử dụng Innovation Hub cho end-users.

## Bắt đầu
- [[08_User_Guide/Quick_Start]] — Đăng nhập lần đầu, cấu hình profile
- [[08_User_Guide/Change_Password]] — Thay đổi mật khẩu

## Sử dụng tính năng
- [[08_User_Guide/Find_Problem]] — Tìm và xem problems
- [[08_User_Guide/Participate_Event]] — Tham gia sự kiện đổi mới

#
```

**[Tool Result]**
```
---
type: moc
category: Events
related: ["MOC_Idea_Lab", "MOC_Problem_Feed", "Event_Endpoints"]
tags: [events, index]
updated: 2026-04-28
---

# MOC Events

Events là tính năng overlay cho chạy các cuộc thi đổi mới sáng tạo có cấu trúc.

## Các khía cạnh
- [[03_Events/Event_Lifecycle]] — draft → active → closed
- [[03_Events/Team_Formation]] — Tạo đội, join, approve/reject
- [[03_Events/Event_Idea_Submission]] — Nộp idea (manual hoặc từ Room)
- [[03_Events/Scoring_System]] — Chấm điểm 8 criteria
```

**[AI — Tool Calls]**
- `read_file({'path': '08_User_Guide/Participate_Event.md'})`
- `read_file({'path': '03_Events/Team_Formation.md'})`

**[AI — Answer]**
 Tôi thấy có file `Participate_Event` trong User Guide. Để trả lời chi tiết, tôi sẽ đọc file này và thêm thông tin về Team Formation. 

**[Tool Result]**
```
---
type: guide
category: User Guide
related: ["MOC_Events", "Team_Formation", "Event_Idea_Submission"]
tags: [user-guide, how-to]
updated: 2026-04-28
---

# Participate Event

## Tìm Event
1. Click **"Events"** ở sidebar → `/events`.
2. Filter: All, Active, Draft, Closed.
3. Click vào event card để xem chi tiết.

## Join Team
1. Trong tab **Teams**, xem danh sách teams.
2. Click **"Join"** trên team muốn tham gia.
3. Chờ team leader approve.
4. Nếu approve → bạn là thành viên active.
- Mỗi user
```

**[Tool Result]**
```
---
type: atomic-note
category: Events
related: ["MOC_Events", "Event_Idea_Submission", "Scoring_System", "User_Roles"]
tags: [events, teams]
updated: 2026-04-28
---

# Team Formation

## Tổng quan
Teams là đơn vị tham gia Event. Mỗi team có leader, members, và có thể được assign chấm điểm team khác.

## Tạo Team
- Bất kỳ ai đã đăng nhập đều có thể tạo team trong event active.
- Người tạo tự động trở thành **Team Leader**.
- Fields: name (bắt buộc), slogan (optional).

## Join Team
1. Click **"J
```

**[AI — Answer]**
 Dựa trên wiki, đây là các bước để **tham gia một event** trên Innovation Hub:

## 1. Tìm và Xem Event
- Click **"Events"** ở sidebar → đến trang `/events`
- Filter theo trạng thái: All, Active, Draft, Closed
- Click vào event card để xem chi tiết

## 2. Tham Gia Team (2 cách)

### Cách A: Join Team có sẵn
1. Trong tab **Teams**, xem danh sách các team
2. Click **"Join"** trên team muốn tham gia
3. Trạng thái: `pending` — chờ team leader duyệt
4. Nếu leader **approve** → bạn trở thành thành viên `active`

> ⚠️ **Lưu ý**: Mỗi user chỉ được active trong **1 team duy nhất** per event.

### Cách B: Tạo Team mới
1. Click **"Tạo Team"**
2. Nhập: tên team (bắt buộc), slogan (tùy chọn)
3. Bạn tự động trở thành **Team Leader**
4. Có quyền: approve/reject join requests, disband team, transfer leadership, submit ideas

## 3. Submit Idea (nếu event yêu cầu)
1. Chuyển sang tab **Ideas**
2. Click nộp idea
3. Điền form hoặc import từ Room (Idea Lab)

## 4. Theo Dõi Tiến Độ
- Tab **Dashboard**: Xem leaderboard — ranking ideas (theo điểm) và teams (theo số lượng submission)

---

**Source:**
- `08_User_Guide/Participate_Event.md` — Hướng dẫn tham gia event
- `03_Events/Team_Formation.md` — Chi tiết về tạo/join team

---

## Test 3: Technical question

**Question:** API endpoint để tạo problem là gì?

### Agent Trace

**[USER]** API endpoint để tạo problem là gì?

**[AI — Tool Calls]**
- `read_file({'path': '07_API_Reference/MOC_API.md'})`
- `read_file({'path': '01_Problem_Feed/MOC_Problem_Feed.md'})`

**[AI — Answer]**
 Tôi sẽ tìm thông tin về API endpoint tạo problem trong wiki. 

**[Tool Result]**
```
---
type: moc
category: API
related: ["MOC_For_Developers", "MOC_Architecture", "API_Contract_Summary"]
tags: [api, index]
updated: 2026-04-28
---

# MOC API

Full API reference cho Innovation Hub. Base path: `/api/v1`.

## Authentication
- [[07_API_Reference/Auth_Endpoints]] — Register, login, refresh, password change

## Core Resources
- [[07_API_Reference/Problem_Endpoints]] — CRUD + reactions + create room
- [[07_API_Reference/Idea_Endpoints]] — CRUD + votes + reactions
- [[07_API_Reference/
```

**[Tool Result]**
```
---
type: moc
category: Problem Feed
related: ["MOC_Idea_Lab", "MOC_Dashboard", "Problem_Endpoints"]
tags: [problem-feed, index]
updated: 2026-04-28
---

# MOC Problem Feed

Problem Feed là "newsfeed" của những điểm nghẽn trong bộ phận. Nơi đăng, thảo luận và theo dõi các vấn đề cần giải quyết.

## Các khía cạnh
- [[01_Problem_Feed/Create_Problem]] — Quy trình đăng bài vấn đề
- [[01_Problem_Feed/Problem_Privacy]] — Ai có thể xem bài đăng của bạn
- [[01_Problem_Feed/Problem_Status_Workflow]] — Tr
```

**[AI — Tool Calls]**
- `read_file({'path': '07_API_Reference/Problem_Endpoints.md'})`

**[Tool Result]**
```
---
type: reference
category: API
related: ["MOC_API", "Create_Problem", "Room_Endpoints"]
tags: [api, problems]
updated: 2026-04-28
---

# Problem Endpoints

Base path: `/api/v1/problems`

## Authentication
Tất cả endpoints yêu cầu Bearer token (trừ GET list/detail có thể public).
Xem [[07_API_Reference/Auth_Endpoints]].

## GET /problems
List problems với filters.

**Query params:** `page`, `limit`, `category`, `status`, `search`, `author_id`, `is_private`, `sort`, `date_from`, `date_to`

**Re
```

**[AI — Answer]**
 ## API Endpoint Tạo Problem

**Endpoint:** `POST /api/v1/problems`

### Thông tin kỹ thuật

| Thuộc tính | Giá trị |
|------------|---------|
| Method | POST |
| Path | `/api/v1/problems` |
| Authentication | ✅ Required (Bearer token) |
| Response | `201 Created` |

### Request Body

```json
{
  "title": "string (max 200)",
  "summary": "string?",
  "content": "TipTap JSON object",
  "category": "process|technical|people|tools|patent",
  "visibility": "public|private?",
  "shared_user_ids": ["uuid?"]
}
```

### Giải thích các trường

| Trường | Bắt buộc | Mô tả |
|--------|----------|-------|
| `title` | ✅ | Tiêu đề problem (tối đa 200 ký tự) |
| `summary` | ❌ | Tóm tắt ngắn |
| `content` | ✅ | Nội dung chi tiết (định dạng TipTap JSON) |
| `category` | ✅ | Loại: `process`, `technical`, `people`, `tools`, `patent` |
| `visibility` | ❌ | `public` hoặc `private` (mặc định: public) |
| `shared_user_ids` | ❌ | Danh sách user ID được chia sẻ (khi private) |

**Source:** `07_API_Reference/Problem_Endpoints.md` — section "POST /problems"

---

## Test 4: Permission question

**Question:** Role admin và member khác gì nhau?

### Agent Trace

**[USER]** Role admin và member khác gì nhau?

**[AI — Tool Calls]**
- `search_wiki({'query': 'permission matrix admin member'})`
- `search_wiki({'query': 'role admin member'})`

**[AI — Answer]**
 Tôi sẽ tìm thông tin về phân quyền admin và member trong wiki. 

**[Tool Result]**
```
No files found matching: permission matrix admin member
```

**[Tool Result]**
```
No files found matching: role admin member
```

**[AI — Tool Calls]**
- `read_file({'path': '04_Authentication/MOC_Auth.md'})`

**[Tool Result]**
```
---
type: moc
category: Authentication
related: ["MOC_Overview", "User_Roles", "Auth_Endpoints"]
tags: [auth, index]
updated: 2026-04-28
---

# MOC Auth

Authentication & Authorization trong Innovation Hub.

## Các khía cạnh
- [[04_Authentication/JWT_Flow]] — Access token + Refresh token lifecycle
- [[04_Authentication/User_Roles]] — Phân quyền: member, admin (team_lead là event-specific)
- [[04_Authentication/Permission_Matrix]] — Bảng quyền chi tiết cho từng role

## Mối liên hệ
- Auth bảo vệ 
```

**[AI — Tool Calls]**
- `read_file({'path': '04_Authentication/User_Roles.md'})`
- `read_file({'path': '04_Authentication/Permission_Matrix.md'})`

**[Tool Result]**
```
---
type: atomic-note
category: Authentication
related: ["Permission_Matrix", "JWT_Flow", "Privacy_Model"]
tags: [auth, roles]
updated: 2026-04-28
---

# User Roles

## System Roles

### Member
- Role mặc định khi đăng ký.
- Quyền:
  - Tạo problems, ideas, rooms, comments, reactions, votes.
  - Tham gia events (tạo/join teams, submit ideas).
  - Xem dashboard cá nhân.
  - Sửa/xóa nội dung của mình.

### Admin
- Quyền đầy đủ:
  - Tất cả quyền của Member.
  - Quản lý users (sửa role, deactivate, r
```

**[Tool Result]**
```
---
type: atomic-note
category: Authentication
related: ["User_Roles", "Privacy_Model", "MOC_Auth"]
tags: [auth, permissions]
updated: 2026-04-28
---

# Permission Matrix

## Problem Feed
| Action | Member | Admin |
|--------|--------|-------|
| Xem problems (public) | ✅ | ✅ |
| Xem problems (private của người khác) | ❌ | ✅ |
| Tạo problem | ✅ | ✅ |
| Sửa problem | Chỉ của mình | ✅ (mọi problem) |
| Xóa problem | Chỉ của mình | ✅ |
| Thay đổi status | Chỉ của mình | ✅ |

## Idea Lab
| Action | M
```

**[AI — Answer]**
 ## Sự khác biệt giữa Admin và Member

### **Member** (Role mặc định khi đăng ký)

Member có quyền cơ bản để sử dụng nền tảng:

| Tính năng | Quyền của Member |
|-----------|------------------|
| **Problem Feed** | Tạo, sửa, xóa problem của mình; xem public problems |
| **Idea Lab** | Tạo room, tạo idea, vote, reaction; chỉ sửa/xóa nội dung của mình |
| **Events** | Tạo/join team, submit ideas (khi là team member) |
| **Dashboard** | Xem dashboard cá nhân |
| **Privacy** | ❌ Không xem được private content của người khác |

---

### **Admin** (Full quyền)

Admin có **tất cả quyền của Member** cộng thêm quyền quản lý hệ thống:

| Tính năng | Quyền thêm của Admin |
|-----------|----------------------|
| **Problem Feed** | ✅ Sửa/xóa **mọi problem** (không chỉ của mình), pin/close problems |
| **Idea Lab** | ✅ Sửa/xóa **mọi room và idea** |
| **Events** | ✅ **Tạo/quản lý events**, scoring criteria, awards |
| **User Management** | ✅ Xem danh sách users, sửa role, deactivate, reset password |
| **Privacy** | ✅ **Bypass privacy** — xem được mọi nội dung private |
| **Analytics** | ✅ Xem analytics dashboard |

---

### **Tóm tắt khác biệt chính**

| Khía cạnh | Member | Admin |
|-----------|--------|-------|
| **Phạm vi sửa/xóa** | Chỉ nội dung của mình | Mọi nội dung trong hệ thống |
| **Tạo Event** | ❌ Không được | ✅ Được phép |
| **Quản lý User** | ❌ Không được | ✅ Được phép |
| **Xem nội dung private** | ❌ Không được | ✅ Bypass được |
| **Analytics** | Chỉ cá nhân | Toàn hệ thống |

---

**Source:**
- `04_Authentication/User_Roles.md` — Định nghĩa các roles
- `04_Authentication/Permission_Matrix.md` — Bảng quyền chi tiết

---

## Test 5: Multi-hop question

**Question:** Workflow của một problem từ lúc tạo đến khi solved?

### Agent Trace

**[USER]** Workflow của một problem từ lúc tạo đến khi solved?

**[AI — Tool Calls]**
- `read_file({'path': '01_Problem_Feed/MOC_Problem_Feed.md'})`

**[AI — Answer]**
 Tôi sẽ tìm hiểu workflow của một problem trong hệ thống. Để trả lời câu hỏi này, tôi cần đọc các tài liệu về Problem Feed. 

**[Tool Result]**
```
---
type: moc
category: Problem Feed
related: ["MOC_Idea_Lab", "MOC_Dashboard", "Problem_Endpoints"]
tags: [problem-feed, index]
updated: 2026-04-28
---

# MOC Problem Feed

Problem Feed là "newsfeed" của những điểm nghẽn trong bộ phận. Nơi đăng, thảo luận và theo dõi các vấn đề cần giải quyết.

## Các khía cạnh
- [[01_Problem_Feed/Create_Problem]] — Quy trình đăng bài vấn đề
- [[01_Problem_Feed/Problem_Privacy]] — Ai có thể xem bài đăng của bạn
- [[01_Problem_Feed/Problem_Status_Workflow]] — Tr
```

**[AI — Tool Calls]**
- `read_file({'path': '01_Problem_Feed/Problem_Status_Workflow.md'})`
- `read_file({'path': '01_Problem_Feed/Create_Problem.md'})`

**[AI — Answer]**
 Tôi thấy có file chuyên về workflow. Để trả lời đầy đủ, tôi cần đọc thêm các file liên quan: 

**[Tool Result]**
```
---
type: atomic-note
category: Problem Feed
related: ["Create_Problem", "MOC_Problem_Feed", "Idea_Status_Workflow"]
tags: [feature, workflow]
updated: 2026-04-28
---

# Problem Status Workflow

## Trạng thái

| Status | Mô tả |
|--------|-------|
| `open` | Mới đăng, chờ thảo luận |
| `discussing` | Đang có bình luận |
| `brainstorming` | Đã tạo Room brainstorm |
| `solved` | Đã giải quyết (terminal) |
| `closed` | Đã đóng (terminal) |

## Chuyển trạng thái

### Tự động
- `open` → `discussing`:
```

**[Tool Result]**
```
---
type: atomic-note
category: Problem Feed
related: ["Problem_Privacy", "Comment_Threading", "MOC_Problem_Feed", "Problem_Status_Workflow"]
tags: [user-guide, how-to]
updated: 2026-04-28
---

# Tạo Problem

## Điều kiện tiên quyết
- Người dùng phải đăng nhập (JWT valid). Xem [[04_Authentication/JWT_Flow]].
- Role: `member`, `team_lead`, hoặc `admin`. Xem [[04_Authentication/User_Roles]].

## Các bước thực hiện
1. Vào trang **Problem Feed** (route `/problems`).
2. Click nút **"Đăng vấn đề"** ở 
```

**[AI — Tool Calls]**
- `read_file({'path': '01_Problem_Feed/Comment_Threading.md'})`
- `read_file({'path': '02_Idea_Lab/Create_Brainstorm_Room.md'})`

**[AI — Answer]**
 Tôi cũng cần đọc thêm về giai đoạn thảo luận và brainstorm để có đầy đủ workflow: 

**[Tool Result]**
```
---
type: atomic-note
category: Problem Feed
related: ["Reactions", "MOC_Problem_Feed", "Notification_System"]
tags: [feature, comments]
updated: 2026-04-28
---

# Comment Threading

## Tổng quan
Hệ thống comment hỗ trợ **threaded comments** (bình luận phân cấp) trên Problems, Ideas, và Event Ideas.

## Cách hoạt động

### Root Comments
- Comment trực tiếp trên target (problem, idea, event_idea).
- Sắp xếp theo thời gian giảm dần (mới nhất trước).

### Replies (Thread)
- Reply vào một comment đã
```

**[Tool Result]**
```
---
type: atomic-note
category: Idea Lab
related: ["MOC_Idea_Lab", "Create_Problem", "Room_vs_Problem_Link", "Kanban_Board"]
tags: [user-guide, how-to]
updated: 2026-04-28
---

# Tạo Brainstorm Room

## Điều kiện tiên quyết
- Đã đăng nhập. Xem [[04_Authentication/JWT_Flow]].
- Role: `member`, `admin`.

## Hai cách tạo Room

### 1. Tạo độc lập
1. Vào **Idea Lab** (`/rooms`).
2. Click **"Tạo Room mới"**.
3. Điền: tên, mô tả (optional), privacy.
4. Không bắt buộc gắn Problem.

### 2. Tạo từ Problem
```

**[AI — Answer]**
 Dưới đây là **workflow đầy đủ** của một Problem từ lúc tạo đến khi solved:

---

## 1. Tạo Problem (Status: `open`)

Người dùng đăng nhập vào **Problem Feed** và thực hiện:

1. Click **"Đăng vấn đề"**
2. Điền form:
   - **Tiêu đề**: Tối đa 200 ký tự
   - **Tóm tắt**: Nội dung chính (optional)
   - **Nội dung**: Rich text editor (TipTap) - hỗ trợ format, hình ảnh
   - **Category**: `Process`, `Technical`, `People`, `Tools`, `Patent`
   - **Privacy**: `public` (toàn bộ) hoặc `private` (chỉ admin + người được share)
3. Click **"Đăng"**

→ Problem được tạo với `status = "open"` và xuất hiện trên Problem Feed.

> **Source**: `Create_Problem.md`

---

## 2. Thảo luận (Status: `open` → `discussing`)

Khi có **comment từ người khác** (không phải tác giả), status tự động chuyển sang `discussing`:

- Hệ thống hỗ trợ **threaded comments** (bình luận phân cấp):
  - **Root comments**: Comment trực tiếp trên problem, sắp xếp mới nhất trước
  - **Replies**: Reply vào comment đã có, sắp xếp cũ nhất trước
- Người dùng có thể thêm **reactions** (like, dislike, insight)
- Tác giả problem và người tương tác nhận **notification**

> **Source**: `Problem_Status_Workflow.md`, `Comment_Threading.md`

---

## 3. Brainstorm (Status: `discussing` → `brainstorming`)

Từ trang chi tiết Problem, người dùng có thể:

1. Click **"Tạo Room"** (1-click)
2. Room tự động **link với Problem** đó
3. Status Problem tự động chuyển sang `brainstorming`

Trong Room:
- Mọi người đóng góp **ideas** qua Kanban board
- Room có privacy **độc lập** với Problem (có thể public/private khác nhau)

> **Source**: `Create_Brainstorm_Room.md`, `Problem_Status_Workflow.md`

---

## 4. Giải quyết (Status: `solved` hoặc `closed`)

**Chuyển trạng thái thủ công** bởi:
- **Tác giả** của problem, hoặc
- **Admin**

| Status | Ý nghĩa |
|--------|---------|
| `solved` | ✅ Đã giải quyết (terminal state) |
| `closed` | ⛔ Đã đóng (terminal state) |

⚠️ **Lưu ý**: Từ `solved` hoặc `closed` **không thể quay lại** các status trước đó.

> **Source**: `Problem_Status_Workflow.md`

---

## Sơ đồ tổng quan

```
┌─────────┐    comment    ┌─────────────┐    tạo Room    ┌─────────────┐
│  open   │ ─────────────→│  discussing  │ ──────────────→│ brainstorming│
│ (tạo)   │   (người khác)│  (thảo luận) │                │  (brainstorm)│
└─────────┘               └─────────────┘                └──────┬──────┘
     │                                                          │
     │                                                          │
     └──────────────────────────────────────────────────────────┘
                              ↓
                    ┌─────────────────┐
                    │  solved/closed  │ ← tác giả/admin chuyển thủ công
                    │   (kết thúc)    │
                    └─────────────────┘
```

---

## API liên quan

| Endpoint | Mô tả |
|----------|-------|
| `POST /api/v1/problems` | Tạo problem |
| `POST /api/v1/comments` | Thêm comment |
| `POST /api/v1/problems/{id}/rooms` | Tạo room từ problem |
| `PATCH /api/v1/problems/{id}` | Cập nhật status (`solved`/`closed`) |

> **Source**: `Problem_Endpoints` (trong `MOC_API.md`)

---

## Summary

- Total tests: 5
- All tests completed
