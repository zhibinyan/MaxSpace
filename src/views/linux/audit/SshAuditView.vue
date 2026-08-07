<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  fetchAuditCommands,
  fetchAuditSessions,
  fetchLinuxHosts,
  type LinuxHost,
  type SshAuditCommand,
  type SshAuditSession,
} from '@/api/linux'
import Message from '@/components/massage'
import MaxPopup from '@/components/maxPopup'
import { MaxButton } from '@/components/maxButton'
import { MaxInput } from '@/components/maxInput'
import { MaxSelect, type MaxSelectOption } from '@/components/maxSelect'
import { LayoutToolbar } from '@/layout'
import ReplayBody from './ReplayBody.vue'

defineOptions({ name: 'SshAuditView' })

const router = useRouter()
const hosts = ref<LinuxHost[]>([])
const sessions = ref<SshAuditSession[]>([])
const commands = ref<SshAuditCommand[]>([])
const loading = ref(false)

const filterHostId = ref('')
const filterUser = ref('')
const filterFrom = ref('')
const filterTo = ref('')
const cmdKeyword = ref('')
const activeSessionId = ref<number | null>(null)

const hostOptions = computed<MaxSelectOption[]>(() => [
  { label: '全部主机', value: '' },
  ...hosts.value.map((h) => ({ label: `${h.name} (${h.host})`, value: String(h.id) })),
])

async function load() {
  loading.value = true
  try {
    sessions.value = await fetchAuditSessions({
      hostId: filterHostId.value || undefined,
      username: filterUser.value || undefined,
      from: filterFrom.value || undefined,
      to: filterTo.value || undefined,
    })
    if (activeSessionId.value) {
      await loadCommands(activeSessionId.value)
    } else {
      commands.value = await fetchAuditCommands({
        hostId: filterHostId.value || undefined,
        username: filterUser.value || undefined,
        from: filterFrom.value || undefined,
        to: filterTo.value || undefined,
        keyword: cmdKeyword.value || undefined,
      })
    }
  } catch (err) {
    Message.error(err instanceof Error ? err.message : '加载失败')
  } finally {
    loading.value = false
  }
}

async function loadCommands(sessionId: number) {
  activeSessionId.value = sessionId
  commands.value = await fetchAuditCommands({
    sessionId,
    keyword: cmdKeyword.value || undefined,
  })
}

function clearSessionFilter() {
  activeSessionId.value = null
  void load()
}

function openReplay(session: SshAuditSession) {
  if (!session.hasRecording) {
    Message.warning('该会话无录制')
    return
  }
  void MaxPopup.open({
    title: `回放 · ${session.hostTitle || session.host}`,
    size: 'lg',
    content: ReplayBody,
    contentProps: { sessionId: session.id, title: session.hostTitle },
    confirmText: '关闭',
    showCancel: false,
  })
}

onMounted(async () => {
  hosts.value = await fetchLinuxHosts()
  await load()
})
</script>

<template>
  <div class="audit-page">
    <LayoutToolbar>
      <template #left>
        <MaxSelect v-model="filterHostId" :width="200" :options="hostOptions" />
        <MaxInput v-model="filterUser" placeholder="用户名" />
        <MaxInput v-model="filterFrom" placeholder="开始日期 YYYY-MM-DD" />
        <MaxInput v-model="filterTo" placeholder="结束日期 YYYY-MM-DD" />
        <MaxInput v-model="cmdKeyword" placeholder="命令关键词" />
        <MaxButton variant="primary" :disabled="loading" @click="load">查询</MaxButton>
        <MaxButton v-if="activeSessionId" @click="clearSessionFilter">清除会话筛选</MaxButton>
      </template>
      <template #right>
        <MaxButton @click="router.push({ name: 'linuxSsh' })">SSH 终端</MaxButton>
      </template>
    </LayoutToolbar>

    <div class="audit-body">
      <section class="audit-col">
        <header class="audit-col__head">
          <h3>会话</h3>
          <span>{{ sessions.length }}</span>
        </header>
        <p v-if="!sessions.length" class="audit-empty">暂无会话记录</p>
        <button
          v-for="s in sessions"
          :key="s.id"
          type="button"
          class="audit-card"
          :class="{ on: activeSessionId === s.id }"
          @click="loadCommands(s.id)"
        >
          <strong>{{ s.hostTitle || s.host || `主机#${s.hostId}` }}</strong>
          <span>{{ s.username }} · {{ s.status }} · #{{ s.id }}</span>
          <span>{{ s.startedAt }} → {{ s.endedAt || '进行中' }}</span>
          <div class="audit-card__actions">
            <MaxButton
              size="sm"
              :disabled="!s.hasRecording"
              @click.stop="openReplay(s)"
            >
              {{ s.hasRecording ? '回放' : '无录制' }}
            </MaxButton>
          </div>
        </button>
      </section>

      <section class="audit-col">
        <header class="audit-col__head">
          <h3>命令</h3>
          <span>{{ commands.length }}</span>
        </header>
        <p v-if="!commands.length" class="audit-empty">暂无命令记录</p>
        <article v-for="c in commands" :key="c.id" class="audit-cmd">
          <code>{{ c.command }}</code>
          <span>会话 #{{ c.sessionId }} · {{ c.username }} · {{ c.createdAt }}</span>
        </article>
      </section>
    </div>
  </div>
</template>

<style scoped>
.audit-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  gap: 10px;
}

.audit-body {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.audit-col {
  min-height: 0;
  overflow: auto;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.04);
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.audit-col__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.audit-col__head h3 {
  margin: 0;
  font-size: 15px;
}

.audit-col__head span {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.45);
}

.audit-empty {
  margin: 40px 0;
  text-align: center;
  color: rgba(255, 255, 255, 0.4);
  font-size: 13px;
}

.audit-card {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
  margin: 0;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid transparent;
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
  text-align: left;
  cursor: pointer;
}

.audit-card.on,
.audit-card:hover {
  border-color: rgba(10, 132, 255, 0.4);
  background: rgba(10, 132, 255, 0.14);
}

.audit-card strong {
  font-size: 14px;
}

.audit-card span {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
}

.audit-card__actions {
  margin-top: 4px;
}

.audit-cmd {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.22);
}

.audit-cmd code {
  font-size: 13px;
  white-space: pre-wrap;
  word-break: break-all;
  color: #e6edf3;
}

.audit-cmd span {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
}
</style>
