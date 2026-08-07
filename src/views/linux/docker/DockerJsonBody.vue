<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  data: Record<string, unknown> | null
}>()

const text = computed(() => {
  try {
    return JSON.stringify(props.data ?? {}, null, 2)
  } catch {
    return String(props.data ?? '')
  }
})
</script>

<template>
  <pre class="docker-json">{{ text }}</pre>
</template>

<style scoped>
.docker-json {
  margin: 0;
  max-height: min(60vh, 480px);
  overflow: auto;
  padding: 12px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.35);
  color: #d7e6ff;
  font-size: 12px;
  line-height: 1.45;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: Menlo, Monaco, 'Courier New', monospace;
}
</style>
