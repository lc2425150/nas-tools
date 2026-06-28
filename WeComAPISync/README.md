# 企业微信 IP 同步工具

本项目的主线实现是 macOS 原生壳 + Python/Playwright 同步核心。

## 成功标准

同步成功不以企业微信开放 API 返回 `errcode=0` 为准。真正成功必须满足：

```text
当前公网 IP 出现在企业微信管理后台可信 IP 页面中
```

Python 同步器会在提交后重新读取页面，只有页面验证到 IP 才会返回 `ok=true` 和 `verified=true`。

## 目录

```text
app/main.m                 macOS 原生窗口和菜单栏
sync/wecom_sync.py         同步命令入口，输出 JSON
sync/browser_sync.py       Playwright 页面同步与验证
sync/wecom_api.py          企业微信 API 辅助尝试，不作为成功依据
sync/ip_provider.py        公网 IP 获取
sync/state.py              状态、日志、last_ip 文件
scripts/build_app.sh       构建 .app
archive/old_attempts/      历史试验方案归档
```

## 使用

构建：

```bash
/Users/achen/Documents/调试绿联nas/WeComAPISync/scripts/build_app.sh
```

运行单次同步：

```bash
/Users/achen/Documents/调试绿联nas/WeComAPISync/build/企业微信IP同步.app/Contents/Resources/sync/wecom_sync --once
```

第一次同步会打开 Chromium，需要扫码登录企业微信后台。登录态保存在：

```text
~/.wecom-ip-sync/wecom_auth.json
```

失败截图和日志：

```text
~/.wecom-ip-sync/last_failure.png
~/.wecom-ip-sync/sync.log
```
