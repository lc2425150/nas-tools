# PhotoSync - NAS 相机储存卡自动同步系统

## 简介

PhotoSync 是一个运行在绿联 NAS 上的 Docker 应用，自动检测外部相机储存卡插入，按自定义规则将新照片同步到指定目录，并提供 Web 管理界面。

## 快速开始

### 1. 部署

```bash
# 克隆项目并进入目录
cd PhotoSync

# 构建并启动
docker compose up -d --build

# 查看日志
docker logs -f photosync
```

### 2. 访问

打开浏览器访问 `http://<NAS_IP>:8932`

首次访问会显示引导向导，帮助你完成初始化设置。

### 3. 配置同步目录

默认同步目标为 `/photos`，你可以在 Settings 页面修改。

## 功能特性

- ✅ 自动检测 USB 储存卡插入（轮询 /media/ 等路径）
- ✅ 多种归档模式：按日期 / 原结构 / 自定义模板
- ✅ SHA256 去重，不会重复同步同一张照片
- ✅ 文件筛选：按类型（RAW/JPEG/视频）、大小、日期
- ✅ 多卡配置模板：不同相机不同规则
- ✅ 冲突处理：跳过 / 覆盖 / 重命名 / 保留两者
- ✅ 数据完整性校验（同步后校验 SHA256）
- ✅ 同步队列：多卡插入排队处理
- ✅ 实时进度（WebSocket 推送）
- ✅ 通知集成：Telegram / 钉钉 / 企业微信 / 邮件 / Webhook
- ✅ 照片画廊浏览
- ✅ 深色/浅色模式
- ✅ Docker 健康检查 + 优雅停止

## API 文档

启动后在 `http://<NAS_IP>:8932/docs` 查看 Swagger 文档。

## 环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| TZ | Asia/Shanghai | 时区 |
| PUID | 1000 | 运行用户 UID |
| PGID | 100 | 运行用户 GID |
| POLL_INTERVAL | 5 | USB 检测轮询间隔（秒） |

## 目录说明

| 路径 | 说明 |
|---|---|
| /media (ro) | USB 储存卡挂载点 |
| /mnt (ro) | 备选 USB 挂载点 |
| /photos (rw) | 照片同步目标目录 |
| /app/data | SQLite 数据库 + 配置 |

## 开发

```bash
# 开发模式（需要 Node.js）
docker compose -f docker-compose.dev.yml up
```

## 技术栈

- 后端: Python FastAPI + SQLAlchemy (async) + SQLite (WAL)
- 前端: Vue 3 + Vite + Tailwind CSS
- 部署: Docker (多阶段构建, ~180MB)
