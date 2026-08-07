# Linux 服务中心（Linux Service Center）设计文档 V1.0

> 项目落地文档。前端禁止使用 Element UI；列表优先使用卡片或图标网格，避免表格。  
> 远程文件（SFTP）与平台本地「文件管理 `/files`」完全分离，禁止混用接口与页面。

---

## 1. 产品概述

### 1.1 定位

企业级 Web SSH / SFTP 管理中心，统一管理 Linux 主机，提供：

- 主机资产管理
- 浏览器在线 SSH
- 基于 SFTP 的远程文件管理
- 权限与操作审计（分阶段）

替代 XShell / FinalShell / SecureCRT 等桌面工具。

### 1.2 建设目标

| 目标 | 说明 |
|------|------|
| 统一主机 | 分组、标签、搜索、收藏 |
| Web SSH | 多标签终端、自动重连 |
| 远程文件 | SFTP 浏览 / 上传 / 下载 / 编辑 |
| 安全 | 凭证加密、操作确认、审计（规划） |
| 扩展 | 为 Docker / K8s / 监控等打底 |

---

## 2. 功能结构与菜单

```
Linux 服务中心（一级，Launchpad 文件夹）
├── 主机管理（二级）
├── SSH 终端（二级）
├── 远程文件（二级，SFTP，≠ 本地文件管理）
└── 会话审计（二级）
```

| 菜单 | path | name | 组件 |
|------|------|------|------|
| Linux 服务中心 | `linux` | `linuxService` | 无（redirect → hosts） |
| 主机管理 | `hosts` | `linuxHosts` | `@/views/linux/hosts/HostManageView.vue` |
| SSH 终端 | `ssh` | `linuxSsh` | `@/views/linux/ssh/SshTerminalView.vue` |
| 远程文件 | `sftp` | `linuxSftp` | `@/views/linux/sftp/SftpFileView.vue` |
| 会话审计 | `audit` | `linuxAudit` | `@/views/linux/audit/SshAuditView.vue` |

完整路由示例：`/linux/hosts`、`/linux/ssh`、`/linux/sftp`、`/linux/audit`。

---

## 3. 技术约束

### 3.1 前端

- 使用 Max* 组件：`MaxButton`、`MaxInput`、`MaxSelect`、`MaxCard`、`MaxPopup`、`MaxConfirm`、`Message`、`LayoutToolbar`
- **禁止** Element Plus 业务组件 / `ElMessage` / `ElTable`
- 主机列表：卡片网格
- 远程文件：图标网格（可切换紧凑列表，仍非表格组件）
- SSH：`@xterm/xterm` + WebSocket

### 3.2 后端

- Flask Blueprint：`/api/linux`
- 主机凭证使用 Fernet 加密存储
- SSH / SFTP：`paramiko`
- 终端通道：`flask-sock` WebSocket `/ws/linux/ssh/<hostId>`

### 3.3 与本地文件管理隔离

| | 本地文件管理 | 远程文件（本模块） |
|--|-------------|-------------------|
| 路径 | `/files` | `/linux/sftp` |
| API | `/api/files` | `/api/linux/sftp/*` |
| 存储 | `python/uploads` | 目标主机文件系统 |

---

## 4. 数据模型

### 4.1 `linux_host_group`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | |
| parent_id | INT NULL | 无限层级 |
| name | VARCHAR(128) | |
| sort_order | INT | |
| created_at / updated_at | TIMESTAMP | |

### 4.2 `linux_host`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | |
| name | VARCHAR(128) | 显示名 |
| host | VARCHAR(255) | IP / 域名 |
| port | INT | 默认 22 |
| username | VARCHAR(128) | |
| auth_type | VARCHAR(16) | `password` / `key` |
| password_enc | TEXT | 加密密码 |
| private_key_enc | TEXT | 加密私钥 |
| group_id | INT NULL | |
| os_name | VARCHAR(64) | |
| env_type | VARCHAR(32) | prod/dev/test/... |
| owner | VARCHAR(64) | 负责人 |
| remark | VARCHAR(512) | |
| is_favorite | TINYINT | 收藏 |
| status | VARCHAR(16) | unknown/online/offline |
| last_connected_at | DATETIME NULL | |
| created_by / updated_by | VARCHAR(64) | |
| created_at / updated_at | TIMESTAMP | |

### 4.3 `linux_tag` / `linux_host_tag`

标签字典 + 主机多对多关联。

---

## 5. 模块一：主机管理

### 5.1 页面布局

```
┌────────────┬──────────────────────────────────────┐
│ 分组树     │ LayoutToolbar：搜索 / 环境 / 状态 / 操作 │
│ 标签快捷   ├──────────────────────────────────────┤
│            │ 主机卡片网格                           │
│            │ [图标] 名称  IP  状态  标签…          │
└────────────┴──────────────────────────────────────┘
```

### 5.2 能力清单（本期）

- [x] 分组：增删改、树展示、服务器计数
- [x] 标签：增删改、主机打标
- [x] 主机：增删改、搜索（名称/IP/备注/负责人）、环境筛选、收藏
- [x] 快捷：连接 SSH、打开远程文件、测试连接、复制连接信息、删除
- [x] 批量：删除、收藏、移动分组（基础）
- [ ] 拖拽排序分组（二期）
- [ ] 批量导出（二期）

### 5.3 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/linux/groups` | 分组树 |
| POST | `/api/linux/groups` | 新建分组 |
| PUT | `/api/linux/groups/:id` | 更新 |
| DELETE | `/api/linux/groups/:id` | 删除 |
| GET | `/api/linux/tags` | 标签列表 |
| POST/PUT/DELETE | `/api/linux/tags...` | 标签 CRUD |
| GET | `/api/linux/hosts` | 主机列表（查询参数筛选） |
| POST | `/api/linux/hosts` | 新建 |
| PUT | `/api/linux/hosts/:id` | 更新 |
| DELETE | `/api/linux/hosts/:id` | 删除 |
| POST | `/api/linux/hosts/:id/test` | 测试连接 |
| POST | `/api/linux/hosts/batch` | 批量操作 |

---

## 6. 模块二：SSH 终端

### 6.1 页面布局

```
┌─ 标签/会话 | 最近会话 | 布局：单/左右/上下/四宫格 | 同步输入 ─┐
│ 工具：重连 / 清屏 / 字体 / 全屏 / 命令历史 / 常用命令           │
│ ┌──────────────┬──────────────┐                              │
│ │ 终端 Pane A  │ 终端 Pane B  │  ← 分屏可视区               │
│ └──────────────┴──────────────┘                              │
│ 侧栏：在线会话 / 最近 / 历史 / 命令模板                        │
└──────────────────────────────────────────────────────────────┘
```

### 6.2 能力清单

**分屏**
- [x] 单屏 / 左右分屏 / 上下分屏 / 四宫格
- [x] 多终端同步输入（同步查看与操作）
- [x] 分屏比例拖拽调整（偏好持久化）

**会话管理**
- [x] 在线会话列表
- [x] 最近会话（服务端优先，localStorage 回落）
- [x] 会话历史（跨浏览器）
- [x] 会话恢复（从最近一键重连）
- [x] 心跳保持（WebSocket ping）
- [x] 服务端会话审计日志 + 命令索引（会话审计页）
- [x] 终端录制与回放

**命令**
- [x] 本机会话命令历史
- [x] 常用命令模板
- [x] 命令搜索与一键发送

**偏好**
- [x] 字体 / 主题 / 编码偏好按用户持久化（`linux_user_pref`）

**基础**
- [x] 多标签 + WebSocket Shell + ANSI / UTF-8
- [x] 断线提示与手动重连

### 6.3 协议

- WebSocket：`/ws/linux/ssh/<hostId>?token=<jwt>`
- 客户端 → 服务端：终端输入；`{"type":"resize","cols":n,"rows":n}`；`{"type":"ping"}`；`{"type":"command","text":"..."}`；`{"type":"record","on":true|false}`
- 服务端 → 客户端：终端输出字节流；`{"type":"ready","sessionId":n}`；`{"type":"pong"}`

---

## 7. 模块三：远程文件（SFTP）

### 7.1 页面布局

```
┌─ 选择主机 / 路径面包屑 / 工具栏 ──────────────────┐
│ 上传 新建文件夹 刷新 搜索                         │
│ ┌──────────────────────────────────────────────┐ │
│ │ 图标网格：📁 目录  📄 文件 …                   │ │
│ └──────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

### 7.2 能力清单

- [x] 目录浏览、面包屑跳转、刷新
- [x] 图标网格展示
- [x] 上传（多文件）、下载、删除、重命名、新建目录
- [x] 文本在线编辑（常见文本后缀）
- [x] 拖拽上传
- [x] 权限修改（chmod / chown 可视化）
- [x] 大文件断点续传（≥2MB 分片 + 续传令牌）
- [x] 压缩下载 / 多文件打包下载
- [x] 传输任务队列（进度、暂停、失败重试）
- [x] 文件搜索（当前目录过滤 / 递归服务端搜索）

### 7.3 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/linux/sftp/list` | `hostId` + `path` |
| POST | `/api/linux/sftp/mkdir` | 建目录 |
| POST | `/api/linux/sftp/rename` | 重命名 |
| POST | `/api/linux/sftp/delete` | 删除 |
| POST | `/api/linux/sftp/upload` | 上传 |
| GET | `/api/linux/sftp/download` | 下载 |
| GET | `/api/linux/sftp/read` | 读文本 |
| PUT | `/api/linux/sftp/write` | 写文本 |
| PUT | `/api/linux/sftp/chmod` | 改权限 |
| PUT | `/api/linux/sftp/chown` | 改所有者 |
| POST | `/api/linux/sftp/upload/init` | 分片上传初始化 |
| POST | `/api/linux/sftp/upload/chunk` | 上传分片 |
| POST | `/api/linux/sftp/upload/complete` | 完成分片上传 |
| GET | `/api/linux/sftp/upload/:token` | 查询续传进度 |
| POST | `/api/linux/sftp/download-zip` | 多路径打包下载 |
| GET | `/api/linux/sftp/search` | 递归搜索 |

---

## 8. 交互原则

- **高效**：主机卡片上直达 SSH / 远程文件
- **统一**：三模块共用 Max* 视觉与确认弹窗
- **安全**：密码不明文落库；删除二次确认
- **隔离**：SFTP ≠ 本地 uploads 文件管理

---

## 9. 目录结构（落地）

```
python/
  db/linux.py
  services/linux_host_service.py
  services/linux_ssh_service.py
  services/linux_sftp_service.py
  routes/linux.py
  utils/crypto_util.py
src/
  api/linux.ts
  views/linux/
    hosts/HostManageView.vue
    hosts/HostFormBody.vue
    hosts/GroupFormBody.vue
    ssh/SshTerminalView.vue
    ssh/SshTermPane.vue
    ssh/sshSessionStore.ts
    sftp/SftpFileView.vue
    sftp/transferQueue.ts
    audit/SshAuditView.vue
Linux服务中心-设计文档.md   ← 本文档
```

---

## 10. 主机系统类型

`os_name` 前端枚举（存库仍为字符串）：

Windows Server / Linux / Ubuntu / CentOS / Debian / Rocky / AlmaLinux / 麒麟 / UOS / openEuler

- Windows：默认用户 `Administrator`，测试命令 `ver`，SFTP 默认路径 `C:/`（需 OpenSSH Server）
- 其余 Linux 系：默认用户 `root`，测试命令 `uname -a`，SFTP 默认路径 `/`

## 11. 实施顺序

### 11.1 一期（已落地）

1. 数据表 + 菜单种子 + 主机/分组/标签 API  
2. 主机管理前端（卡片网格）  
3. SSH WebSocket + 终端页（含分屏、会话侧栏、命令历史/模板）  
4. SFTP API + 远程文件页（浏览、上传下载、拖拽、文本编辑）

### 11.2 二期（SSH + SFTP 已落地；安全与体验后续）

**主机管理（未做，仍属后续）**
- [ ] 分组拖拽排序 / 树节点拖放归属
- [ ] 主机批量导出 / 导入
- [ ] 收藏置顶、最近打开主机快捷入口

**SSH 终端**
- [x] 服务端会话审计日志（连接/断开、命令回放索引，可按主机/用户/时间查询）
- [x] 会话服务端持久化与跨浏览器恢复（一期为 localStorage）
- [x] 分屏布局自定义（自由拖拽分割比例、可保存布局预设）
- [x] 字体 / 主题 / 编码偏好按用户持久化
- [x] 终端录制与回放
- [x] AI 命令助手（自然语言 → Shell 命令，见 `doc/SSH-AI命令助手.md`）

**远程文件（SFTP）**
- [x] 权限修改（chmod / chown 可视化）
- [x] 大文件断点续传（分片上传 + 续传令牌）
- [x] 压缩下载 / 多文件打包下载
- [x] 传输任务队列（进度、暂停、失败重试）
- [x] 文件搜索（当前目录 / 递归，可配置深度）

**安全与治理（后续）**
- [ ] 操作审计中心：SSH 命令、SFTP 读写删、主机 CRUD 统一落库
- [ ] 细粒度权限（按分组/主机授权只读终端、禁止下载等）
- [ ] 密钥托管增强（多密钥、到期提醒）
- [ ] 连接白名单 / 登录失败锁定策略

**体验与扩展（后续）**
- [ ] 全局快捷键（新建会话、切窗格、同步输入开关）
- [ ] 移动端适配（只读终端 / 简化 SFTP）
- [ ] 为 Docker / 监控等后续模块预留主机能力扩展点

### 11.3 验收要点（SSH + SFTP 二期）

- 换浏览器登录同用户可见最近会话与终端偏好
- 审计页能按主机筛命令；录制可回放
- 左右/四宫格拖拽比例刷新后保持
- SFTP：改权限生效；>2MB 上传中断后续传；多选 zip 下载；队列可见进度；递归搜索可点进目录

# Debian/Ubuntu
sudo apt install tmux
# CentOS/RHEL
sudo yum install tmux
# 或
sudo dnf install tmux