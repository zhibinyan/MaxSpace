<script setup lang="ts">
import { Handle, Position, type NodeProps } from '@vue-flow/core'

const props = defineProps<NodeProps<{ label: string }>>()

function onInput(event: Event) {
  props.data.label = (event.target as HTMLInputElement).value
}
</script>

<template>
  <div class="process-flow-node">
    <Handle type="target" :position="Position.Top" />
    <input
      class="process-flow-node__input"
      :value="props.data.label"
      placeholder="节点名称"
      spellcheck="false"
      @input="onInput"
      @mousedown.stop
      @pointerdown.stop
      @click.stop
      @keydown.stop
    />
    <Handle type="source" :position="Position.Bottom" />
  </div>
</template>

<style scoped>
.process-flow-node {
  min-width: 120px;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.28);
  background: rgba(255, 255, 255, 0.12);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.process-flow-node__input {
  width: 100%;
  min-width: 96px;
  border: none;
  outline: none;
  background: transparent;
  color: #ffffff;
  font-size: 13px;
  font-weight: 600;
  text-align: center;
}

.process-flow-node__input::placeholder {
  color: rgba(255, 255, 255, 0.45);
}
</style>
