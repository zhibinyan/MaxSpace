<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  VueFlow,
  type Connection,
} from '@vue-flow/core'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import { createProcess, fetchProcess, updateProcess, type ProcessFlowData } from '@/api/process'
import { MaxButton } from '@/components/maxButton'
import ProcessFlowNode from './ProcessFlowNode.vue'

defineOptions({ name: 'processEditorView' })

interface FlowNode {
  id: string
  type?: string
  position: { x: number; y: number }
  data: { label: string }
}

const nodeTypes = { editable: ProcessFlowNode }

interface FlowEdge {
  id: string
  source: string
  target: string
}

const route = useRoute()
const router = useRouter()

function parseProcessId(raw: unknown): number | null {
  if (raw === undefined || raw === null || raw === '') return null
  const id = Number(raw)
  return Number.isFinite(id) && id > 0 ? id : null
}

const processId = computed(() => parseProcessId(route.params.id))
const isCreate = computed(() => processId.value === null)

const title = ref('未命名流程')
const description = ref('')
const nodes = ref<FlowNode[]>([])
const edges = ref<FlowEdge[]>([])
const loading = ref(false)
const saving = ref(false)

function defaultNodes(): FlowNode[] {
  return [
    {
      id: 'start',
      type: 'editable',
      position: { x: 120, y: 120 },
      data: { label: '开始' },
    },
  ]
}

function parseFlowNodes(flow: ProcessFlowData | null | undefined): FlowNode[] {
  const raw = flow?.nodes
  if (!Array.isArray(raw) || !raw.length) return defaultNodes()
  return (raw as unknown as FlowNode[]).map((node) => ({
    ...node,
    type: 'editable',
    data: {
      label: String((node.data as { label?: string } | undefined)?.label ?? '节点'),
    },
  }))
}

function parseFlowEdges(flow: ProcessFlowData | null | undefined): FlowEdge[] {
  const raw = flow?.edges
  if (!Array.isArray(raw)) return []
  return raw as unknown as FlowEdge[]
}

async function loadProcess() {
  if (isCreate.value) {
    title.value = '未命名流程'
    description.value = ''
    nodes.value = defaultNodes()
    edges.value = []
    return
  }

  loading.value = true
  try {
    const item = await fetchProcess(processId.value!)
    title.value = item.title
    description.value = item.description
    nodes.value = parseFlowNodes(item.processData)
    edges.value = parseFlowEdges(item.processData)
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push({ name: 'process' })
}

function addNode() {
  const id = `node-${Date.now()}`
  const next: FlowNode = {
    id,
    type: 'editable',
    position: { x: 80 + nodes.value.length * 40, y: 80 + nodes.value.length * 32 },
    data: { label: '新节点' },
  }
  nodes.value = [...nodes.value, next]
}

function onConnect(connection: Connection) {
  if (!connection.source || !connection.target) return
  const next: FlowEdge = {
    id: `e-${connection.source}-${connection.target}-${Date.now()}`,
    source: connection.source,
    target: connection.target,
  }
  edges.value = [...edges.value, next]
}

async function saveProcess() {
  if (!title.value.trim()) {
    window.alert('请填写流程标题')
    return
  }

  saving.value = true
  try {
    const payload = {
      title: title.value.trim(),
      description: description.value.trim(),
      processData: {
        nodes: nodes.value,
        edges: edges.value,
      },
    }

    if (isCreate.value) {
      const created = await createProcess(payload)
      router.replace({ name: 'processEditor', params: { id: String(created.id) } })
    } else {
      await updateProcess(processId.value!, payload)
    }
  } finally {
    saving.value = false
  }
}

watch(processId, () => {
  void loadProcess()
}, { immediate: true })
</script>

<template>
  <div class="process-editor">
    <header class="process-editor__toolbar">
      <div class="process-editor__toolbar-left">
        <MaxButton variant="ghost" @click="goBack">返回</MaxButton>
        <input
          v-model="title"
          class="process-editor__title-input"
          type="text"
          placeholder="流程标题"
          spellcheck="false"
        />
        <input
          v-model="description"
          class="process-editor__desc-input"
          type="text"
          placeholder="描述（可选）"
          spellcheck="false"
        />
      </div>
      <div class="process-editor__toolbar-right">
        <MaxButton variant="ghost" :disabled="loading" @click="addNode">添加节点</MaxButton>
        <MaxButton variant="primary" :loading="saving" @click="saveProcess">保存</MaxButton>
      </div>
    </header>

    <div v-if="loading" class="process-editor__loading">加载中…</div>
    <VueFlow
      v-else
      v-model:nodes="nodes"
      v-model:edges="edges"
      :node-types="nodeTypes"
      class="process-editor__canvas"
      fit-view-on-init
      @connect="onConnect"
    />
  </div>
</template>

<style scoped>
.process-editor {
  display: flex;
  flex-direction: column;
  flex: 1;
  width: 100%;
  min-height: 0;
  height: 100%;
  box-sizing: border-box;
}

.process-editor__toolbar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.18);
}

.process-editor__toolbar-left,
.process-editor__toolbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.process-editor__title-input,
.process-editor__desc-input {
  height: 34px;
  padding: 0 12px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.22);
  background: rgba(255, 255, 255, 0.08);
  color: #ffffff;
  font-size: 14px;
  outline: none;
}

.process-editor__title-input {
  width: min(220px, 28vw);
  font-weight: 600;
}

.process-editor__desc-input {
  width: min(280px, 36vw);
}

.process-editor__title-input:focus,
.process-editor__desc-input:focus {
  border-color: rgba(255, 255, 255, 0.42);
}

.process-editor__loading {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.62);
  font-size: 14px;
}

.process-editor__canvas {
  flex: 1;
  min-height: 0;
  height: 100%;
}

.process-editor__canvas :deep(.vue-flow) {
  width: 100%;
  height: 100%;
}

.process-editor__canvas :deep(.vue-flow__edge-path) {
  stroke: rgba(255, 255, 255, 0.55);
}
</style>
