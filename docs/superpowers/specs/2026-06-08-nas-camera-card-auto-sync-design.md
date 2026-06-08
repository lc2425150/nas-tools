# 绿联 NAS 相机储存卡自动同步系统 — 设计文档

> 日期：2026-06-08
> 项目：photo-sync

## 1. 项目概述

在绿联 NAS 上部署一个 Docker 应用，自动检测外部相机储存卡插入，按用户自定义规则将新照片同步到指定目录，并提供 Web 管理界面。

### 1.1 技术栈

| 层 | 技术 |
|---|---|
| 后端框架 | Python FastAPI |
| 前端框架 | Vue.js 3 (Vite) |
| 数据库 | SQLite (通过 SQLAlchemy + aiosqlite) |
| 部署 | Docker 单容器 (python:3.11-slim) |
| 实时通信 | WebSocket |
| 架构模式 | 单体架构（后端+前端+Worker 同一容器） |

### 1.2 适用环境

- NAS 系统：绿联 UGOS（基于 Linux）
- USB 挂载路径：通常为 `/media/` 或 `/mnt/`
- 容器访问：通过 Docker bind mount 挂载宿主机 USB 目录

## 2. 功能清单

### 2.1 核心功能

- [x] 自动检测储存卡插入/拔出（轮询 /media/ 目录，3 秒间隔）
- [x] 手动触发同步
- [x] 按日期自动归档 (YYYY/MM/DD)
- [x] 按原始目录结构保留
- [x] 自定义路径模板 (如 {Camera}/{Date}/{FileName})

### 2.2 同步引擎

- [x] 去重同步：通过 SHA256 哈希比对，只同步新文件
- [x] 文件筛选：按文件类型（RAW/JPEG/视频）、日期范围、文件大小
- [x] 冲突处理：跳过 / 覆盖 / 自动重命名 / 保留两者
- [x] 复制/剪切模式可选
- [x] 数据完整性校验（同步后自动校验 SHA256）
- [x] 同步前检查目标盘空间，不足时告警
- [x] 同步队列 + 互斥锁，防止并发冲突

### 2.3 多卡配置

- [x] 支持按卷标自动匹配配置模板
- [x] 支持插卡即用（always 模式）
- [x] 支持仅手动触发
- [x] 每套配置独立规则：目录、模式、筛选、冲突策略等

### 2.4 用户界面

- [x] Dashboard：同步状态、储存卡状态、存储空间概览、最近同步
- [x] 配置管理：CRUD 同步配置模板
- [x] 历史记录：浏览和搜索同步历史、文件明细
- [x] 储存卡浏览器：预览卡上文件内容
- [x] 系统设置：全局参数
- [x] 日志查看器：按级别筛选、搜索
- [x] WebSocket 实时推送同步进度
- [x] 深色/浅色模式切换
- [x] 缩略图浏览已同步照片（支持 RAW 格式）

### 2.5 通知与集成

- [x] 通知渠道：Telegram / 钉钉 / 微信 / 邮件 / Webhook
- [x] 触发时机：卡插入、同步完成、同步失败、空间不足
- [x] REST API 暴露全部功能
- [x] 配置导入/导出

### 2.6 其他

- [x] 自动同步模式（检测到卡即同步）
- [x] 定时扫描（无热插拔事件也定期检查）
- [x] EXIF 智能归档（按拍摄日期而非文件修改时间）
- [x] 同步后支持安全弹出提示
- [x] 支持并行同步多文件
- [x] 同步中断自动重试
- [x] Docker 优雅停止（SIGTERM 处理）
- [x] 不设认证（局域网信任环境）

## 3. 系统架构

```
┌─────────────────────────────────────────────────┐
│             Docker Container: photo-sync          │
│                                                   │
│  ┌─────────────────┐     ┌────────────────────┐  │
│  │  FastAPI Web     │     │  Background Worker │  │
│  │  (端口 8932)     │     │                    │  │
│  │  - REST API      │     │  - USB 轮询检测    │  │
│  │  - Vue.js 前端    │     │  - 同步引擎        │  │
│  │  - WebSocket      │     │  - 文件校验        │  │
│  │  - 缩略图服务     │     │  - 缩略图生成      │  │
│  └────────┬─────────┘     └──────────┬─────────┘  │
│           │                          │            │
│           └──────────┬───────────────┘            │
│                      │                            │
│           ┌──────────▼──────────┐                 │
│           │     SQLite DB       │                 │
│           │  (/app/data/*.db)   │                 │
│           └─────────────────────┘                 │
└─────────────────────────────────────────────────┘
         │                 │               │
         ▼                 ▼               ▼
   /media (ro)       /photos (rw)      ./data (rw)
   USB 挂载点         照片目标目录      SQLite + 配置
```

### 3.1 Docker Compose

```yaml
version: '3.8'
services:
  photo-sync:
    image: photo-sync:latest
    container_name: photo-sync
    ports:
      - "8932:8932"
    volumes:
      - /media:/media:ro          # USB 挂载点（只读）
      - /volume2/照片:/photos    # 同步目标目录
      - ./photo-sync-data:/app/data  # 数据库和配置
    environment:
      - TZ=Asia/Shanghai
      - POLL_INTERVAL=3           # USB 轮询间隔（秒）
    restart: unless-stopped
```

## 4. 数据库设计

### 4.1 sync_profiles（同步配置模板）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 自增主键 |
| name | TEXT NOT NULL | 配置名称，如"索尼 A7M4" |
| match_type | TEXT NOT NULL | 匹配方式: label / always / manual |
| match_value | TEXT | 匹配值（卷标名） |
| destination | TEXT NOT NULL | 目标目录 |
| sync_mode | TEXT NOT NULL | 归档模式: date / original / custom |
| custom_template | TEXT | 自定义路径模板 |
| file_filters | JSON | 文件筛选规则 |
| conflict_strategy | TEXT | 冲突策略: skip/overwrite/rename/keep_both |
| copy_mode | TEXT | copy / move |
| auto_eject | BOOLEAN | 同步后弹出提示 |
| checksum_verify | BOOLEAN | 是否校验 |
| auto_sync | BOOLEAN | 自动同步 |
| poll_interval | INTEGER | 扫描间隔（秒） |
| enabled | BOOLEAN | 启用 |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### 4.2 sync_history（同步记录）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | |
| profile_id | INTEGER FK | 关联配置 |
| profile_name | TEXT | 冗余：配置名（配置删除后仍可读） |
| status | TEXT | running / completed / failed / cancelled |
| total_files / synced_files | INTEGER | |
| skipped_files / failed_files | INTEGER | |
| total_bytes / synced_bytes | INTEGER | |
| source_path / dest_path | TEXT | |
| started_at / completed_at | DATETIME | |
| error_message | TEXT | |

### 4.3 sync_files（同步文件明细）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | |
| history_id | INTEGER FK | |
| filename / relative_path | TEXT | |
| source_path / dest_path | TEXT | |
| file_size | INTEGER | |
| checksum / checksum_alg | TEXT | SHA256 |
| thumbnail_path | TEXT | 缩略图路径 |
| status | TEXT | synced / skipped / failed |
| error_message | TEXT | |
| created_at | DATETIME | |

### 4.4 file_registry（文件哈希注册表 — 持久去重）

| 字段 | 类型 | 说明 |
|---|---|---|
| file_hash | TEXT PK | SHA256 哈希 |
| original_path | TEXT | 原始路径 |
| file_size | INTEGER | |
| dest_path | TEXT | 已同步到的位置 |
| first_synced_at | DATETIME | |
| last_synced_at | DATETIME | |

### 4.5 其他表

- **settings**: key (TEXT PK) / value (JSON) — 全局设置
- **sync_logs**: id / history_id / level / message / timestamp
- **notification_configs**: id / type / enabled / config (JSON) / created_at

## 5. API 接口设计

### 5.1 REST API

#### 配置管理
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/profiles | 列出配置 (?page=1&page_size=50) |
| POST | /api/profiles | 创建配置 |
| GET | /api/profiles/{id} | 查看配置 |
| PUT | /api/profiles/{id} | 更新配置 |
| DELETE | /api/profiles/{id} | 删除配置 |
| GET | /api/profiles/{id}/export | 导出配置 JSON |
| POST | /api/profiles/import | 导入配置 JSON |

#### 同步操作
| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /api/sync/trigger | 手动触发同步 |
| GET | /api/sync/status | 当前状态 |
| POST | /api/sync/cancel | 取消同步 |

#### 储存卡
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/cards | 列出已检测到的卡 |
| GET | /api/cards/{id}/preview | 预览卡上文件 (?page=&file_types=) |

#### 历史
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/history | 同步历史列表 (?page=&status=&profile_id=) |
| GET | /api/history/{id} | 单次同步详情 |
| GET | /api/history/{id}/files | 文件列表 (?page=&status=) |
| DELETE | /api/history | 清理历史 |

#### 系统
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/settings | 获取全局设置 |
| PUT | /api/settings | 更新全局设置 |
| GET | /api/system/health | 健康检查 |
| GET | /api/system/storage | 磁盘空间 |
| GET | /api/logs | 系统日志 (?page=&level=&search=) |

#### 通知
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/notification-configs | 列表 |
| POST | /api/notification-configs | 创建 |
| PUT | /api/notification-configs/{id} | 更新 |
| DELETE | /api/notification-configs/{id} | 删除 |
| POST | /api/test-notification | 测试通知 |

### 5.2 WebSocket

| 路径 | 说明 |
|---|---|
| WS /ws/sync/status | 实时推送同步进度、卡状态变更 |

**推送消息格式：**
```json
{"type": "card_inserted", "path": "/media/SDCARD", "label": "SONY-A7M4"}
{"type": "card_removed", "path": "/media/SDCARD"}
{"type": "sync_started", "profile": "索尼 A7M4", "total_files": 120}
{"type": "sync_progress", "current": 45, "total": 120, "file": "DSC_0045.ARW"}
{"type": "sync_completed", "status": "success", "synced": 118, "skipped": 2}
{"type": "sync_error", "message": "目标空间不足"}
```

## 6. 前端页面结构

```
Dashboard          → 同步状态、卡状态、存储空间、最近同步
├─ 储存卡状态卡片（绿色=已插入，灰色=无）
├─ 同步进度条（实时 WebSocket 更新）
├─ 存储空间环形图
└─ 最近 5 条同步记录

Profiles           → 同步配置模板列表
├─ 新增配置按钮
├─ 配置卡片列表（名称、匹配方式、目标目录、启停开关）
└─ 点击 → 配置详情/编辑页

ProfileDetail      → 单个配置编辑
├─ 基本信息：名称、匹配方式、卷标
├─ 同步规则：模式、目标目录、自定义模板
├─ 筛选规则：文件类型、大小、日期
├─ 高级选项：冲突策略、复制/剪切、校验、自动弹出
└─ 操作：保存 / 删除 / 导出 / 测试同步

History            → 同步记录列表
├─ 搜索和筛选（日期范围、状态、配置）
├─ 分页表格（时间、配置名、状态、文件数、大小）
└─ 点击 → 详情页

HistoryDetail      → 单次同步详情
├─ 概要卡片（状态、时间、统计）
├─ 文件列表（文件名、大小、状态、哈希）
└─ 日志时间线

CardBrowser        → 插入的卡上文件预览
├─ 卡信息（路径、卷标、总大小、已用空间）
├─ 文件浏览器（树形/列表，带缩略图）
└─ 选择文件 → 手动同步

Settings           → 全局设置
├─ 通知配置管理（新增/编辑/删除/测试）
├─ 默认同步设置
├─ 系统设置（轮询间隔、日志保留天数）
└─ 配置导入/导出

Logs               → 系统日志查看器
├─ 级别筛选（INFO/WARN/ERROR）
├─ 搜索框
├─ 日志时间线
└─ 自动滚动 / 刷新
```

## 7. 项目目录结构

```
photo-sync/
├── docker-compose.yml
├── Dockerfile
├── README.md
├── .gitignore
│
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI 入口 + 生命周期
│   │   ├── config.py            # 配置管理
│   │   ├── database.py          # 数据库初始化 + session
│   │   ├── models.py            # SQLAlchemy 模型
│   │   ├── schemas.py           # Pydantic 请求/响应模型
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── profiles.py
│   │   │   ├── sync.py
│   │   │   ├── cards.py
│   │   │   ├── history.py
│   │   │   ├── settings.py
│   │   │   ├── notifications.py
│   │   │   └── system.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── card_detector.py  # USB 卡检测
│   │   │   ├── sync_engine.py    # 同步引擎核心
│   │   │   ├── file_organizer.py # 文件命名/归档
│   │   │   ├── file_scanner.py   # 文件扫描+筛选
│   │   │   ├── dedup.py          # 去重逻辑
│   │   │   ├── checksum.py       # 哈希校验
│   │   │   ├── thumbnail.py      # 缩略图生成
│   │   │   ├── notification.py   # 通知发送
│   │   │   └── ws_manager.py     # WebSocket 连接管理
│   │   └── worker.py             # 后台 Worker 主循环
│   └── tests/
│       ├── conftest.py
│       ├── test_card_detector.py
│       ├── test_sync_engine.py
│       ├── test_dedup.py
│       └── test_api.py
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   ├── src/
│   │   ├── App.vue
│   │   ├── router/index.js
│   │   ├── stores/               # Pinia stores
│   │   │   ├── sync.js
│   │   │   ├── profiles.js
│   │   │   └── settings.js
│   │   ├── api/                  # API 调用封装
│   │   │   ├── client.js
│   │   │   ├── profiles.js
│   │   │   ├── sync.js
│   │   │   ├── history.js
│   │   │   └── settings.js
│   │   ├── views/
│   │   │   ├── Dashboard.vue
│   │   │   ├── Profiles.vue
│   │   │   ├── ProfileDetail.vue
│   │   │   ├── History.vue
│   │   │   ├── HistoryDetail.vue
│   │   │   ├── CardBrowser.vue
│   │   │   ├── Settings.vue
│   │   │   └── Logs.vue
│   │   ├── components/
│   │   │   ├── StatusCard.vue
│   │   │   ├── SyncProgress.vue
│   │   │   ├── StorageChart.vue
│   │   │   ├── FileList.vue
│   │   │   ├── NotificationConfig.vue
│   │   │   └── ThemeToggle.vue
│   │   ├── composables/
│   │   │   ├── useWebSocket.js
│   │   │   └── useTheme.js
│   │   └── assets/
│   │       └── styles/
│   └── public/
│       └── favicon.ico
│
└── data/                          # Docker volume 挂载点
    ├── photo-sync.db              # SQLite 数据库
    └── config.json                # 全局配置备份
```

## 8. USB 检测与同步流程

### 8.1 检测流程

```
后台 Worker 每 N 秒 (默认 3s):
  1. 扫描 /media/ 下所有子目录
  2. 比对缓存的上次扫描结果
  3. 新目录出现 → 获取卷标 → 匹配配置模板
     ├─ 匹配到配置 + auto_sync=true → 自动开始同步
     ├─ 匹配到配置 + auto_sync=false → 等待手动触发
     └─ 未匹配到 → 使用默认配置 / 等待手动
  4. 目录消失 → 更新卡状态为已拔出
```

### 8.2 同步流程

```
1. [准备] 扫描源目录，递归获取所有文件
2. [筛选] 按文件扩展名、大小、日期过滤
3. [去重] 对每个文件:
   a. 计算 SHA256 哈希
   b. 查询 file_registry 是否已存在
   c. 如果已存在 → 跳过 (skipped)
   d. 如果不存在 → 加入同步队列
4. [排序] 按文件大小排序 (小文件先同步，快速出结果)
5. [同步] 并行同步 (最多 4 个 goroutine 等效):
   a. 计算目标路径 (按 sync_mode)
   b. 创建目标目录
   c. copy/move 文件
   d. 如果 checksum_verify → 校验目标文件哈希
   e. 写入 file_registry
   f. 生成缩略图
   g. WebSocket 推送进度
6. [完成] 推送完成通知 / 发送通知消息
```

## 9. 关键技术决策

### 9.1 USB 检测方式
- **轮询 /media/** — 不需要特权模式，bind mount 即可
- 间隔 3 秒可配置，用户可自行调整
- 不使用 inotify/udev：Docker 容器无法直接接收宿主机 udev 事件

### 9.2 文件去重
- 主键：SHA256 哈希
- 同哈希不管文件名是否相同都视为同一文件
- 区分大小写不敏感的路径比较

### 9.3 RAW 缩略图
- 使用 Python `rawpy` + `Pillow` 库
- 支持的 RAW 格式：ARW (Sony), CR3 (Canon), NEF (Nikon), RAF (Fujifilm), DNG, ORF (Olympus)
- 生成 300px JPEG 缩略图
- 缩略图存储在 `/app/data/thumbnails/` 中

### 9.4 EXIF 提取
- 使用 `Pillow` 或 `exifread` 提取 EXIF DateTimeOriginal
- 作为按日期归档的首选依据
- 无 EXIF 时回退到文件修改时间 (mtime)

### 9.5 通知渠道实现
- Telegram: 使用 `python-telegram-bot` API HTTP 调用
- 钉钉: 钉钉机器人 Webhook
- 微信: Server酱 / 企业微信机器人
- 邮件: smtplib (支持 SMTP 自定义)
- Webhook: 通用 HTTP POST

### 9.6 优雅停止
- FastAPI 生命周期事件 + Python signal 处理
- 收到 SIGTERM → 标记停止信号 → 当前文件同步完成 → 保存状态 → 退出

## 10. 安全和网络

- 运行在局域网信任环境，不设认证
- 端口 8932（默认，可在 docker-compose 中修改）
- 所有文件操作在容器内完成
- 敏感配置（通知令牌等）存储在 SQLite 中

---

## 11. 自审查修正 (2026-06-08)

### 11.1 auto_eject 澄清
- Docker 容器无法直接卸载宿主机设备（需 `--privileged` 模式）
- 实际行为：同步完成后发送通知提醒用户手动安全拔出
- 未来可考虑可选 `--privileged` 模式实现自动卸载

### 11.2 custom_template {Camera} 来源
- 优先从照片 EXIF 中读取相机型号 (Make + Model)
- 无 EXIF 时回退到卷标名（match_value）
- 均不可用时回退为 "Unknown"

### 11.3 同步并行数
- 默认 4 个并行文件传输
- 可在设置中调整（1-10）
- 避免过多并行导致 NAS I/O 过载

---

## 12. 第二轮优化（2026-06-08）

### 12.1 SQLite 并发写入保护

**问题：** FastAPI 异步请求 + 后台 Worker 可能同时写数据库，SQLite 默认序列化写入会导致 "database is locked"。

**修复方案：**
- 启用 **WAL 模式**（Write-Ahead Logging）：读写不互斥
- 使用 `aiosqlite` + SQLAlchemy 异步引擎，单连接串行化
- 数据库写操作通过 **单线程队列** 处理，避免并发写入

```python
# database.py 关键配置
engine = create_async_engine(
    "sqlite+aiosqlite:///data/photo-sync.db",
    connect_args={"check_same_thread": False}
)
# 启动时执行 PRAGMA journal_mode=WAL;
# 同步引擎写操作通过 asyncio.Lock 保护
```

### 12.2 异步文件 I/O

**问题：** Python 的文件读写是同步阻塞的，直接 await 会阻塞事件循环。

**修复方案：**
- 大文件复制使用 `asyncio.to_thread()` 放到线程池
- 小文件使用 `aiofiles` 异步库
- 同步引擎独立于 FastAPI 事件循环，在后台线程中运行

```python
# 文件复制示例
async def copy_file(src: str, dst: str):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _sync_copy, src, dst)

def _sync_copy(src: str, dst: str):
    shutil.copy2(src, dst)  # 同步复制，在线程池中执行
```

### 12.3 Docker 镜像优化

**问题：** rawpy 依赖 libraw C 库，安装时需要编译工具链，镜像膨胀到 500MB+。

**修复方案：**
- **多阶段构建**：builder 阶段安装编译依赖，最终镜像只保留运行库
- RAW 缩略图改用 `Pillow` + `exifread` 组合（不依赖 C 扩展），仅提取 JPEG 预览图
- 最终镜像基于 `python:3.11-slim`，仅安装必要的系统库

```dockerfile
# 多阶段 Dockerfile
FROM python:3.11-slim AS builder
RUN apt-get update && apt-get install -y build-essential
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
RUN apt-get update && apt-get install -y libjpeg62-turbo
COPY --from=builder /root/.local /root/.local
COPY ./backend /app/backend
COPY ./frontend/dist /app/static
EXPOSE 8932
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8932"]
```

**预期镜像大小：** ~180MB（vs 未优化时的 500MB+）

### 12.4 Dry-Run 预览同步

**新增功能：** 正式同步前预览将有哪些文件被同步。

**新增 API：**
| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /api/sync/dry-run | 预览同步（只扫描不复制） |
| GET | /api/sync/dry-run/{task_id} | 获取预览结果 |

**返回格式：**
```json
{
  "total_files": 120,
  "total_size": 5368709120,
  "new_files": 85,
  "new_size": 4294967296,
  "skipped_files": 35,
  "skipped_size": 1073741824,
  "files": [
    {"name": "DSC_0045.ARW", "size": 52428800, "will_copy": true, "reason": "新文件"},
    {"name": "DSC_0044.ARW", "size": 50331648, "will_copy": false, "reason": "已同步过"}
  ]
}
```

**前端交互：** 点击"预览同步"→ 展示文件列表和统计 → 用户确认后执行实际同步。

### 12.5 统一 API 错误响应

**新增约定：** 所有 API 错误返回统一格式。

```json
// 400 Bad Request
{
  "error": {
    "code": "INVALID_PROFILE_NAME",
    "message": "配置名称不能为空"
  }
}

// 404 Not Found
{
  "error": {
    "code": "PROFILE_NOT_FOUND",
    "message": "配置 ID 123 不存在"
  }
}

// 409 Conflict
{
  "error": {
    "code": "SYNC_IN_PROGRESS",
    "message": "当前已有同步任务进行中"
  }
}

// 500 Internal Server Error
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "文件复制失败: /media/DCIM/DSC_0045.ARW"
  }
}
```

**错误码规范：** `{RESOURCE}_{ISSUE}` 格式，大写蛇形。

### 12.6 用户界面语言

- 默认语言：**简体中文**
- 所有 UI 文本、通知消息、日志输出均为中文
- 未来可扩展 i18n 支持，但第一期不做多语言

### 12.7 .gitignore 补充

```
# Node
node_modules/
frontend/dist/

# Python
__pycache__/
*.pyc
.venv/

# Docker data
data/
photo-sync-data/

# IDE
.idea/
.vscode/
*.swp

# Brainstorming
.superpowers/
```
