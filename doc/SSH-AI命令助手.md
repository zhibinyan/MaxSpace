# SSH AI 命令助手

侧栏 **AI** Tab：用自然语言描述需求，返回一条可执行的 Shell 命令，并可一键发到当前终端。

## 怎么用

1. 打开 **SSH 终端** → 左侧切到 **AI**
2. 输入需求，**回车**查询（`Shift+Enter` 换行）
3. 生成结果后，点 **运行到当前窗口** 发到 SSH
4. AI 页下方 **历史记录**（最近 30 条）可回填；侧栏 **命令** Tab 也可翻看记录并一键运行
## 结构

| 位置 | 说明 |
|------|------|
| `src/views/linux/ssh/AIssh.vue` | AI 侧栏 UI |
| `SshTerminalView.vue` | 引入 AI Tab，`@run` → 当前窗格 |
| `POST /api/linux/ai/command` | 流式生成（完成后落库） |
| `GET /api/linux/ai/history` | 当前用户问答历史 |
| 表 `linux_ai_chat` | `username / prompt / answer / created_at` |
| `python/services/linux_ai_service.py` | TokenHub + 落库 |

密钥只放服务端，不进前端。

## 配置

在 `python/.env`（已 gitignore）写入：

```bash
AI_API_KEY=你的TokenHub密钥
AI_MODEL=deepseek-v4-flash-202605
AI_API_URL=https://tokenhub.tencentmaas.com/v1/chat/completions
```

改完后重启：`cd python && python app.py`

## 说明

- 模型被要求**只输出命令**，尽量不带解释 / markdown
- 未配置 `AI_API_KEY` 时接口会报错提示
- 需已登录（走现有 JWT）
