<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  data: Record<string, unknown> | null
}>()

const d = computed(() => props.data || {})

const envList = computed(() => {
  const env = d.value.env
  return Array.isArray(env) ? (env as string[]) : []
})

const ports = computed(() => {
  const p = d.value.ports
  return Array.isArray(p) ? (p as Array<{ container?: string; host?: string }>) : []
})

const networks = computed(() => {
  const n = d.value.networks
  return Array.isArray(n) ? (n as Array<{ name?: string; ip?: string; gateway?: string }>) : []
})

const mounts = computed(() => {
  const m = d.value.mounts
  return Array.isArray(m)
    ? (m as Array<{ type?: string; source?: string; destination?: string; mode?: string }>)
    : []
})

const resources = computed(() => (d.value.resources || {}) as Record<string, unknown>)

function fmtBytes(v: unknown) {
  const n = Number(v || 0)
  if (!n) return '未限制'
  if (n < 1024) return `${n} B`
  if (n < 1024 ** 2) return `${(n / 1024).toFixed(1)} KB`
  if (n < 1024 ** 3) return `${(n / 1024 ** 2).toFixed(1)} MB`
  return `${(n / 1024 ** 3).toFixed(2)} GB`
}

function fmtCpu(v: unknown) {
  const n = Number(v || 0)
  if (!n) return '未限制'
  return `${(n / 1e9).toFixed(2)} 核`
}
</script>

<template>
  <div class="dk-detail">
    <section>
      <h4>基础信息</h4>
      <div class="grid">
        <div><label>名称</label><span>{{ d.name || '-' }}</span></div>
        <div><label>ID</label><span class="mono">{{ d.id || '-' }}</span></div>
        <div><label>状态</label><span>{{ d.status || '-' }}</span></div>
        <div><label>镜像</label><span>{{ d.image || '-' }}</span></div>
        <div><label>创建时间</label><span>{{ d.created || '-' }}</span></div>
        <div><label>重启策略</label><span>{{ d.restartPolicy || '-' }}</span></div>
        <div class="full"><label>启动命令</label><span class="mono">{{ d.command || '-' }}</span></div>
      </div>
    </section>

    <section>
      <h4>端口映射</h4>
      <p v-if="!ports.length" class="empty">无</p>
      <ul v-else>
        <li v-for="(p, i) in ports" :key="i">{{ p.host || '-' }} → {{ p.container }}</li>
      </ul>
    </section>

    <section>
      <h4>网络</h4>
      <p v-if="!networks.length" class="empty">无</p>
      <ul v-else>
        <li v-for="(n, i) in networks" :key="i">
          {{ n.name }} · IP {{ n.ip || '-' }} · GW {{ n.gateway || '-' }}
        </li>
      </ul>
    </section>

    <section>
      <h4>数据卷 / 挂载</h4>
      <p v-if="!mounts.length" class="empty">无</p>
      <ul v-else>
        <li v-for="(m, i) in mounts" :key="i">
          [{{ m.type }}] {{ m.source }} → {{ m.destination }} {{ m.mode || '' }}
        </li>
      </ul>
    </section>

    <section>
      <h4>资源配置</h4>
      <div class="grid">
        <div><label>CPU</label><span>{{ fmtCpu(resources.nanoCpus) }}</span></div>
        <div><label>内存</label><span>{{ fmtBytes(resources.memory) }}</span></div>
        <div><label>Swap</label><span>{{ fmtBytes(resources.memorySwap) }}</span></div>
        <div>
          <label>GPU</label>
          <span>{{
            Array.isArray(resources.deviceRequests) && (resources.deviceRequests as unknown[]).length
              ? '已配置'
              : '无'
          }}</span>
        </div>
      </div>
    </section>

    <section>
      <h4>环境变量</h4>
      <pre v-if="envList.length" class="env">{{ envList.join('\n') }}</pre>
      <p v-else class="empty">无</p>
    </section>
  </div>
</template>

<style scoped>
.dk-detail {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-height: min(62vh, 520px);
  overflow: auto;
}
section h4 {
  margin: 0 0 8px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  font-weight: 500;
}
.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px 12px;
}
.grid .full {
  grid-column: 1 / -1;
}
.grid label {
  display: block;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  margin-bottom: 2px;
}
.grid span {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.88);
  word-break: break-all;
}
.mono {
  font-family: Menlo, Monaco, 'Courier New', monospace;
  font-size: 12px !important;
}
ul {
  margin: 0;
  padding-left: 18px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.78);
  line-height: 1.5;
}
.empty {
  margin: 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.35);
}
.env {
  margin: 0;
  padding: 10px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.35);
  font-size: 11px;
  line-height: 1.45;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 160px;
  overflow: auto;
  color: #c8e0ff;
  font-family: Menlo, Monaco, 'Courier New', monospace;
}
</style>
