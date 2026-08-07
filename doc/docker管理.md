# Docker 容器管理 — 产品与落地说明

## 一、模块概述

### 1.1 产品定位

Docker 容器管理是 **Infrastructure Center（基础设施中心）** 的核心模块，用于统一管理企业服务器上的 Docker 环境、容器、镜像、网络、存储及应用运行状态。

通过 Web 替代传统命令行，实现：

- Docker 环境统一管理（按主机切换）
- 容器生命周期管理
- 镜像管理（拉取 / 删除 / 导入 / 导出）
- Compose 应用管理
- 容器日志查看（搜索 / 时间过滤 / 自动刷新 / 下载）
- 容器终端（`docker exec`）
- 资源监控（CPU / 内存 / 网络 / IO）
- 运维审计

### 1.2 MaxSpace 落地方式

| 项 | 说明 |
|----|------|
| 入口 | Linux 服务中心 → Docker管理（`/linux/docker`） |
| 执行面 | 后端经 SSH 在目标机执行 `docker` / `docker compose` CLI |
| 前端 | `src/views/linux/docker/`（侧栏导航 + 主内容） |
| API | `/api/linux/docker/*` |
| 终端 | WebSocket `/ws/linux/docker/<hostId>/exec?container=` |
| 审计 | 表 `linux_docker_audit` |

> 要求：目标机已安装 Docker；SSH 用户具备 `docker` 权限（或在 docker 组）。暂不支持 Windows 主机。

---

## 二、模块位置

```
基础设施中心 Infrastructure Center
├── Server Management（主机管理）
├── Docker 容器管理          ← 本模块
├── Kubernetes 管理
├── 网络管理
├── 存储管理
├── 监控中心
└── 自动化中心
```

在 MaxSpace 菜单中挂在 **Linux 服务中心** 下：

| path | name | 组件 |
|------|------|------|
| `docker` | `linuxDocker` | `@/views/linux/docker/DockerManageView.vue` |

---

## 三、功能架构与页面布局

### 3.1 功能树

```
Docker 容器管理
├── Docker 概览
├── 容器管理（列表 / 操作 / 详情 / 日志 / 终端）
├── 镜像管理
├── Compose 应用
├── 网络管理
├── 数据卷管理
├── 资源监控
└── 操作审计
```

### 3.2 页面布局（已实现）

```
┌─────────────────────────────────────────────────────┐
│ Toolbar：主机选择 | 刷新 | 主机管理 / SSH           │
├──────────┬──────────────────────────────────────────┤
│ 侧栏导航  │  主内容区（卡片 / 列表，非表格）          │
│ · 概览   │                                          │
│ · 容器   │                                          │
│ · 镜像   │                                          │
│ · Compose│                                          │
│ · 网络   │                                          │
│ · 数据卷 │                                          │
│ · 监控   │                                          │
│ · 审计   │                                          │
└──────────┴──────────────────────────────────────────┘
```

---

## 四、Docker 概览 Dashboard

| 展示项 | 说明 | 落地 |
|--------|------|------|
| Docker 版本 | Engine 版本 | ✅ |
| 运行状态 | Running / Stop | ✅ |
| 容器总数 / 运行 / 停止 / 暂停 | 来自 `docker info` | ✅ |
| 镜像数量 | 本地镜像数 | ✅ |
| 数据卷 / 网络数量 | `volume ls` / `network ls` | ✅ |
| 存储占用 | `docker system df` | ✅ |
| 快捷跳转 | 点击卡片进入对应页签 | ✅ |

---

## 五、容器管理

### 5.1 列表字段

| 字段 | 说明 | 落地 |
|------|------|------|
| 名称 / ID | Container Name / 短 ID | ✅ |
| 镜像 | Image | ✅ |
| 状态 | running / exited / … | ✅ |
| 创建时间 | CreatedAt | ✅ |
| CPU / 内存 | `docker stats --no-stream` 合并进列表 | ✅ |
| 网络 / 端口 | Networks / Ports | ✅ |

### 5.2 操作

| 操作 | CLI 对应 | 落地 |
|------|----------|------|
| 启动 / 停止 / 重启 | start / stop / restart | ✅ |
| 暂停 / 恢复 | pause / unpause | ✅ |
| 删除 / 强制删除 | rm / rm -f | ✅（二次确认） |
| 详情 | inspect → 结构化摘要 | ✅ |
| 日志 | logs（见第七节） | ✅ |
| 终端 | exec -it bash/sh | ✅ WebSocket |

### 5.3 详情结构化字段

| 分组 | 内容 | 落地 |
|------|------|------|
| 基础 | 名称、ID、状态、镜像、创建时间、重启策略、启动命令 | ✅ |
| 端口 | 主机端口 → 容器端口 | ✅ |
| 网络 | 网络名、IP、网关 | ✅ |
| 挂载 | type / source / destination | ✅ |
| 资源 | CPU / 内存 / Swap / GPU 是否配置 | ✅ |
| 环境变量 | Env 列表 | ✅ |
| 原始 JSON | 可选查看完整 inspect | ✅（保留 inspect API） |

---

## 六、容器终端

| 能力 | 落地 |
|------|------|
| `docker exec -it` 交互 | ✅ PTY + WebSocket |
| 优先 bash，回退 sh | ✅ |
| 窗口 resize | ✅ |
| 审计记录 open terminal | ✅ |

---

## 七、容器日志

| 能力 | 落地 | 说明 |
|------|------|------|
| 历史日志 | ✅ | `--tail` |
| 时间过滤 | ✅ | `--since`（如 `1h`、时间戳） |
| 时间戳 | ✅ | `--timestamps` |
| 搜索 | ✅ | 前端行过滤 |
| 自动刷新 | ✅ | 5s 轮询（近似实时；非真正 follow 流） |
| 下载 | ✅ | 浏览器下载 txt |
| 清空视图 | ✅ | 仅清空前端展示，不改容器日志文件 |
| 清理远端日志文件 | ⏸ | Docker 日志驱动相关，需主机级 truncate，本期不做 |

---

## 八、镜像管理

| 能力 | 落地 |
|------|------|
| 列表（名称 / Tag / ID / 大小 / 创建时间） | ✅ |
| 使用该镜像的容器 | ✅ `usedBy` / `usedCount` |
| 搜索过滤 | ✅ |
| 拉取 | ✅ `docker pull` |
| 删除 / 强制删除 | ✅ |
| 详情 inspect | ✅ |
| 导出 | ✅ `docker save` → 下载 tar（中小镜像） |
| 导入 | ✅ 上传 tar → `docker load` |
| Registry 远程搜索 | ⏸ 需对接 Hub/私有仓库 API，本期不做 |

---

## 九、Compose 应用

| 能力 | 落地 |
|------|------|
| 应用列表 | ✅ `docker compose ls` |
| 服务数量 | ✅ 解析 Status 或 `ps -q` |
| 启动 / 停止 / 重启 / Down | ✅ |
| 更新（pull + up -d） | ✅ action=`update` |
| 单独 pull | ✅ |
| 查看配置 | ✅ `compose config` |
| 查看日志 | ✅ `compose logs --tail` |
| 编辑 compose 文件 | ⏸ 建议走 SFTP 编辑 |

---

## 十、网络管理

| 能力 | 落地 |
|------|------|
| 列表（名称 / driver / scope） | ✅ |
| 连接容器列表 / 数量 | ✅ 来自 network inspect |
| 创建（bridge / host / overlay） | ✅ |
| 删除 | ✅（二次确认） |
| 详情 | ✅ |

---

## 十一、数据卷 Volume

| 能力 | 落地 |
|------|------|
| 列表 | ✅ |
| 创建时间 / 存储路径 | ✅ inspect |
| 使用中的容器 | ✅ |
| 创建 / 删除 / 详情 | ✅ |
| 备份 | ✅ alpine+tar → 下载 `.tgz` |
| 恢复 | ✅ 上传 `.tgz` → 解压进 volume |

---

## 十二、资源监控

| 能力 | 落地 |
|------|------|
| 当前 CPU / 内存占用与使用率 | ✅ `docker stats --no-stream` |
| 网络 IO / 块 IO | ✅ |
| 自动刷新（5s） | ✅ 监控页签内 |
| 历史趋势图 / 峰值曲线 | ⏸ 需时序存储，后续接监控中心 |

---

## 十三、安全与确认

| 能力 | 落地 |
|------|------|
| 删除容器 / 镜像 / 网络 / 卷二次确认 | ✅ MaxConfirm |
| Compose down 确认 | ✅ |
| 操作写入审计 | ✅ |
| 细粒度 RBAC（仅看日志/禁止删除） | ⏸ 跟随平台权限体系 |

---

## 十四、操作审计

| 字段 | 说明 |
|------|------|
| 用户 | 操作人 |
| 时间 | created_at |
| 主机 | host_id |
| 操作 | start / stop / rmi / compose:up / exec … |
| 对象 | 容器名 / 镜像 / 卷名等 |
| 结果 | success / fail |
| 详情 | 输出摘要或错误信息 |

页面：侧栏「审计」按当前主机筛选最近记录。

---

## 十五、API 一览（`/api/linux/docker`）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/overview` | 概览 |
| GET | `/containers` | 列表（`stats=1` 合并资源） |
| GET | `/containers/detail` | 结构化详情 |
| GET | `/containers/inspect` | 原始 inspect |
| GET | `/containers/stats` | stats |
| GET | `/containers/logs` | 日志（tail/since/timestamps） |
| POST | `/containers/action` | 生命周期操作 |
| GET | `/images` | 镜像列表 |
| GET | `/images/inspect` | 镜像详情 |
| POST | `/images/pull` | 拉取 |
| POST | `/images/remove` | 删除 |
| GET | `/images/export` | 导出 tar |
| POST | `/images/import` | 导入（multipart） |
| GET | `/networks` | 网络列表 |
| GET | `/networks/inspect` | 网络详情 |
| POST | `/networks` | 创建 |
| POST | `/networks/remove` | 删除 |
| GET | `/volumes` | 卷列表 |
| GET | `/volumes/inspect` | 卷详情 |
| POST | `/volumes` | 创建 |
| POST | `/volumes/remove` | 删除 |
| GET | `/volumes/backup` | 备份下载 |
| POST | `/volumes/restore` | 恢复上传 |
| GET | `/compose` | Compose 列表 |
| GET | `/compose/config` | 渲染配置 |
| GET | `/compose/logs` | 应用日志 |
| POST | `/compose/action` | up/down/update/… |
| GET | `/audit` | 审计列表 |
| WS | `/ws/linux/docker/<hostId>/exec` | 容器终端 |

公共查询参数：`hostId`（必填，除审计可空）。

---

## 十六、代码路径

| 项 | 路径 |
|----|------|
| 主页面 | `src/views/linux/docker/DockerManageView.vue` |
| 终端 | `DockerExecBody.vue` |
| 日志弹窗 | `DockerLogBody.vue`（支持直播拉取 / staticContent） |
| 结构化详情 | `DockerDetailBody.vue` |
| JSON 详情 | `DockerJsonBody.vue` |
| 前端 API | `src/api/linux.ts` |
| 后端服务 | `python/services/linux_docker_service.py` |
| 路由 | `python/routes/linux.py` |
| 审计表 / 菜单 seed | `python/db/linux.py` |

---

## 十七、后续可选增强

1. 日志真正 follow（SSE / WS 推送 `docker logs -f`）
2. 监控历史曲线（Prometheus / 自建采样表）
3. Registry 搜索与登录拉取私有镜像
4. Compose 在线编辑（结合 SFTP）
5. 按角色的 Docker 操作 ACL
6. 大镜像导出改为分块流式（避免 base64 内存压力）
