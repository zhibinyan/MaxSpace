<script setup lang="ts">
import { computed, ref } from 'vue'
import { MaxSvg } from '@/components/maxSvg'
import { svgNames } from '@/components/maxSvg/svgMap'

const model = defineModel<string>({ default: '' })

withDefaults(
  defineProps<{
    columns?: number
    iconSize?: number
    searchPlaceholder?: string
    emptyText?: string
  }>(),
  {
    columns: 6,
    iconSize: 28,
    searchPlaceholder: '搜索',
    emptyText: '未找到图标',
  },
)

const keyword = ref('')

const filteredNames = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  if (!query) return svgNames
  return svgNames.filter((name) => name.toLowerCase().includes(query))
})

function selectIcon(name: string) {
  model.value = name
}
</script>

<template>
  <div class="max-svg-grid">
    <div class="max-svg-grid__search">
      <svg class="max-svg-grid__search-icon" viewBox="0 0 16 16" aria-hidden="true">
        <circle cx="7" cy="7" r="4.5" stroke="currentColor" stroke-width="1.4" fill="none" />
        <path d="M10.5 10.5L14 14" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" />
      </svg>
      <input
        v-model="keyword"
        class="max-svg-grid__search-input"
        type="search"
        :placeholder="searchPlaceholder"
      />
    </div>

    <div v-if="filteredNames.length" class="max-svg-grid__list" :style="{ '--svg-grid-cols': columns }">
      <button
        v-for="name in filteredNames"
        :key="name"
        type="button"
        class="max-svg-grid__item"
        :class="{ 'max-svg-grid__item--active': model === name }"
        :title="name"
        @click="selectIcon(name)"
      >
        <MaxSvg :name="name" :size="iconSize" />
      </button>
    </div>

    <div v-else class="max-svg-grid__empty">{{ emptyText }}</div>
  </div>
</template>

<style scoped>
.max-svg-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 10px;
  border-radius: 14px;
  background: rgba(28, 28, 30, 0.96);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow:
    0 18px 48px rgba(0, 0, 0, 0.42),
    inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.max-svg-grid__search {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 34px;
  padding: 0 10px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.max-svg-grid__search:focus-within {
  border-color: rgba(10, 132, 255, 0.55);
  box-shadow: 0 0 0 3px rgba(10, 132, 255, 0.14);
}

.max-svg-grid__search-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  color: rgba(255, 255, 255, 0.42);
}

.max-svg-grid__search-input {
  flex: 1;
  min-width: 0;
  border: none;
  outline: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.92);
  font-size: 13px;
}

.max-svg-grid__search-input::placeholder {
  color: rgba(255, 255, 255, 0.34);
}

.max-svg-grid__list {
  display: grid;
  grid-template-columns: repeat(var(--svg-grid-cols), minmax(0, 1fr));
  gap: 4px;
  max-height: 240px;
  overflow: auto;
  padding-right: 2px;
}

.max-svg-grid__list::-webkit-scrollbar {
  width: 6px;
}

.max-svg-grid__list::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
}

.max-svg-grid__item {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  aspect-ratio: 1;
  border: none;
  border-radius: 10px;
  background: transparent;
  cursor: pointer;
  transition:
    background 0.16s ease,
    transform 0.16s ease,
    box-shadow 0.16s ease;
}

.max-svg-grid__item:hover {
  background: rgba(255, 255, 255, 0.08);
}

.max-svg-grid__item:active {
  transform: scale(0.94);
}

.max-svg-grid__item--active {
  background: rgba(10, 132, 255, 0.18);
  box-shadow: inset 0 0 0 1px rgba(10, 132, 255, 0.45);
}

.max-svg-grid__empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 120px;
  color: rgba(255, 255, 255, 0.42);
  font-size: 13px;
}
</style>
