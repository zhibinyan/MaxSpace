# Python API

Flask 后端，默认端口 `5050`。

## 环境

```bash
cd python
pip install -r requirements.txt
```

环境变量（可选，见 `config.py`）：

| 变量 | 默认值 |
|------|--------|
| `DB_HOST` | `127.0.0.1` |
| `DB_PORT` | `3306` |
| `DB_USER` | `root` |
| `DB_PASSWORD` | `12345678` |
| `DB_NAME` | `maxadmin` |
| `PORT` | `5050` |

## 数据库迁移

**首次部署或表结构变更后**，在 MySQL 已启动的前提下执行：

```bash
cd python
python -m db migrate
```

该命令会：

- 创建数据库（`CREATE DATABASE IF NOT EXISTS`）
- 创建/补齐表：`admin`、`menu`、`process`、`markdown`、`file_entry`、`linux_*`
- 种子菜单：本地文件管理、Linux 服务中心（主机管理 / SSH / 远程文件）
- 执行必要的列补丁（如 `admin.is_super`）

迁移是幂等的，可重复执行，**不会清空已有数据**。

`python app.py` 启动服务时**不再**自动跑迁移，需手动执行上述命令。

## 启动服务

```bash
cd python
python app.py
```

健康检查：`GET /api/health`
