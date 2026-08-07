# maxAdmin

基于 Vue 3 + Vite + Element Plus 的后台管理系统。

## 功能

- 登录 / 退出（路由守卫）
- 侧边栏布局
- 仪表盘（统计卡片、操作日志）
- 用户管理（增删改查）
- 系统设置

## 快速开始

```bash
pnpm install
pnpm dev
```

### 后端（首次需迁移数据库）

```bash
cd python
pip install -r requirements.txt
python -m db migrate   # 首次或表结构变更后执行
python app.py
```

详见 [python/README.md](./python/README.md)。

默认账号：`admin` / `123456`

## 技术栈

- Vue 3 + TypeScript
- Vue Router
- Pinia
- Element Plus
