<script setup lang="ts" generic="T extends Record<string, unknown>">
import { computed, nextTick, onMounted, onUnmounted, ref, useSlots, watch } from 'vue'
import type { MaxColumn, MaxRowContext } from './types'

const CHECKBOX_WIDTH = 28
const STATUS_WIDTH = 72
const ACTIONS_WIDTH = 168
const CELL_GAP = 8
const ROW_HORIZONTAL_PADDING = 24
const DEFAULT_FLEX_MIN_WIDTH = 120

const props = withDefaults(
  defineProps<{
    columns: MaxColumn<T>[]
    data: T[]
    rowKey?: keyof T & string
    loading?: boolean
    selectable?: boolean
    /** 选中行的 key 列表 */
    modelValue?: Array<string | number>
    emptyText?: string
    /** 占满父容器剩余高度 */
    fill?: boolean
    /** 表体最大高度，超出后纵向滚动；fill 为 true 时默认不限制 */
    maxHeight?: string | number | null
  }>(),
  {
    rowKey: 'id' as keyof T & string,
    loading: false,
    selectable: false,
    modelValue: () => [],
    emptyText: '暂无数据',
    fill: true,
    maxHeight: undefined,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: Array<string | number>]
  'row-click': [payload: MaxRowContext<T>]
}>()

const slots = useSlots()
const viewportRef = ref<HTMLElement | null>(null)
const headScrollerRef = ref<HTMLElement | null>(null)
const trackMinWidth = ref(0)
const canScrollX = ref(false)
const canScrollY = ref(false)

const selectedSet = ref(new Set<string | number>(props.modelValue))

watch(
  () => props.modelValue,
  (value) => {
    selectedSet.value = new Set(value)
  },
)

const allSelected = computed(() => {
  if (!props.data.length) return false
  return props.data.every((row) => selectedSet.value.has(getRowKey(row)))
})

const indeterminate = computed(() => {
  if (!props.data.length || allSelected.value) return false
  return props.data.some((row) => selectedSet.value.has(getRowKey(row)))
})

function getRowKey(row: T): string | number {
  const key = (row as any)[props.rowKey]
  if (key === undefined || key === null) return JSON.stringify(row)
  return key as string | number
}

function getCellValue(row: T, column: MaxColumn<T>) {
  return row[column.key]
}

function parseCssSize(value: string | number, fallback: number) {
  if (typeof value === 'number') return value
  const parsed = Number.parseFloat(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

function getColumnMinWidth(column: MaxColumn<T>) {
  if (column.width != null) {
    return parseCssSize(column.width, DEFAULT_FLEX_MIN_WIDTH)
  }
  if (column.minWidth != null) {
    return parseCssSize(column.minWidth, DEFAULT_FLEX_MIN_WIDTH)
  }
  return DEFAULT_FLEX_MIN_WIDTH
}

function measureTrackMinWidth() {
  let cellCount = props.columns.length
  let width = ROW_HORIZONTAL_PADDING

  if (props.selectable) {
    width += CHECKBOX_WIDTH
    cellCount += 1
  }
  if (slots.status) {
    width += STATUS_WIDTH
    cellCount += 1
  }
  if (slots.actions) {
    width += ACTIONS_WIDTH
    cellCount += 1
  }

  for (const column of props.columns) {
    width += getColumnMinWidth(column)
  }

  if (cellCount > 1) {
    width += (cellCount - 1) * CELL_GAP
  }

  return Math.ceil(width)
}

function readOverflow(el: HTMLElement) {
  return {
    x: el.scrollWidth > el.clientWidth + 1,
    y: el.scrollHeight > el.clientHeight + 1,
  }
}

function updateScrollMetrics() {
  trackMinWidth.value = measureTrackMinWidth()
  const viewport = viewportRef.value
  if (!viewport) return
  const { x, y } = readOverflow(viewport)
  canScrollX.value = x
  canScrollY.value = y
}

let layoutRaf = 0
function scheduleLayout() {
  cancelAnimationFrame(layoutRaf)
  layoutRaf = requestAnimationFrame(() => {
    updateScrollMetrics()
    syncHeadScrollLeft()
  })
}

let scrollRaf = 0
function syncHeadScrollLeft() {
  const viewport = viewportRef.value
  const headScroller = headScrollerRef.value
  if (!viewport || !headScroller) return
  headScroller.scrollLeft = viewport.scrollLeft
}

function onViewportScroll() {
  cancelAnimationFrame(scrollRaf)
  scrollRaf = requestAnimationFrame(() => {
    syncHeadScrollLeft()
    updateScrollMetrics()
  })
}

/** 左键拖拽横向/纵向滚动 */
const DRAG_THRESHOLD = 4
const dragging = ref(false)
let dragPointerId: number | null = null
let dragStartX = 0
let dragStartY = 0
let dragScrollLeft = 0
let dragScrollTop = 0
let dragMoved = false

function isInteractiveTarget(target: EventTarget | null) {
  if (!(target instanceof Element)) return false
  return !!target.closest(
    'input, button, a, label, textarea, select, [role="button"], .max-check',
  )
}

function onViewportPointerDown(e: PointerEvent) {
  if (e.button !== 0) return
  const el = viewportRef.value
  if (!el) return
  if (isInteractiveTarget(e.target)) return

  // 以当前 DOM 溢出为准，避免 class/ref 滞后导致拖不动
  const { x, y } = readOverflow(el)
  canScrollX.value = x
  canScrollY.value = y
  if (!x && !y) return

  dragPointerId = e.pointerId
  dragStartX = e.clientX
  dragStartY = e.clientY
  dragScrollLeft = el.scrollLeft
  dragScrollTop = el.scrollTop
  dragMoved = false
  dragging.value = true
  el.setPointerCapture(e.pointerId)
}

function onViewportPointerMove(e: PointerEvent) {
  if (!dragging.value || e.pointerId !== dragPointerId) return
  const el = viewportRef.value
  if (!el) return

  const dx = e.clientX - dragStartX
  const dy = e.clientY - dragStartY
  if (!dragMoved && Math.hypot(dx, dy) < DRAG_THRESHOLD) return
  dragMoved = true

  const { x, y } = readOverflow(el)
  if (x) el.scrollLeft = dragScrollLeft - dx
  if (y) el.scrollTop = dragScrollTop - dy
}

function endViewportDrag(e: PointerEvent) {
  if (e.pointerId !== dragPointerId) return
  const el = viewportRef.value
  if (el?.hasPointerCapture(e.pointerId)) {
    el.releasePointerCapture(e.pointerId)
  }
  dragging.value = false
  dragPointerId = null
}

/** 拖拽后抑制一次 click，避免误触 row-click */
function onViewportClickCapture(e: MouseEvent) {
  if (!dragMoved) return
  e.preventDefault()
  e.stopPropagation()
  dragMoved = false
}

let resizeObserver: ResizeObserver | null = null

onMounted(() => {
  nextTick(() => {
    scheduleLayout()
    const viewport = viewportRef.value
    if (!viewport) return
    resizeObserver = new ResizeObserver(scheduleLayout)
    resizeObserver.observe(viewport)
  })
})

onUnmounted(() => {
  cancelAnimationFrame(layoutRaf)
  cancelAnimationFrame(scrollRaf)
  resizeObserver?.disconnect()
})

watch(
  () => [props.columns, props.selectable, slots.status, slots.actions],
  () => nextTick(scheduleLayout),
  { deep: true },
)

watch(
  () => props.data.length,
  () => nextTick(scheduleLayout),
)

const trackStyle = computed(() => ({
  '--max-track-min': `${trackMinWidth.value}px`,
}))

const viewportStyle = computed(() => {
  if (props.fill && props.maxHeight == null) return undefined
  const maxHeight =
    props.maxHeight ?? 'min(65vh, 640px)'
  const value = typeof maxHeight === 'number' ? `${maxHeight}px` : maxHeight
  return { maxHeight: value }
})

function columnStyle(column: MaxColumn<T>) {
  const style: Record<string, string> = {}
  if (column.width != null) {
    const width = typeof column.width === 'number' ? `${column.width}px` : column.width
    style.width = width
    style.minWidth = width
    style.maxWidth = width
    style.flex = '0 0 auto'
  } else {
    style.flex = '1 1 0'
    style.minWidth =
      column.minWidth != null
        ? typeof column.minWidth === 'number'
          ? `${column.minWidth}px`
          : column.minWidth
        : `${DEFAULT_FLEX_MIN_WIDTH}px`
  }
  return style
}

function syncSelection() {
  emit('update:modelValue', [...selectedSet.value])
}

function toggleRow(row: T) {
  const key = getRowKey(row)
  if (selectedSet.value.has(key)) {
    selectedSet.value.delete(key)
  } else {
    selectedSet.value.add(key)
  }
  syncSelection()
}

function toggleAll() {
  if (allSelected.value) {
    selectedSet.value.clear()
  } else {
    props.data.forEach((row) => selectedSet.value.add(getRowKey(row)))
  }
  syncSelection()
}

function onRowClick(row: T, index: number) {
  emit('row-click', { row, index })
}
</script>

<template>
  <div
    class="max-table"
    :class="{
      'max-table--loading': loading,
      'max-table--fill': fill,
    }"
  >
    <div class="max-table__shell">
      <div ref="headScrollerRef" class="max-table__head-scroller">
        <div class="max-table__head" :style="trackStyle" role="row">
          <div
            v-if="selectable"
            class="max-table__cell max-table__cell--checkbox"
            role="columnheader"
          >
            <label class="max-check">
              <input
                type="checkbox"
                class="max-check__input"
                :checked="allSelected"
                :indeterminate="indeterminate"
                @change="toggleAll"
              />
              <span class="max-check__box" aria-hidden="true" />
            </label>
          </div>

          <div
            v-for="column in columns"
            :key="column.key"
            class="max-table__cell max-table__cell--head"
            :class="[
              column.className,
              column.align ? `max-table__cell--${column.align}` : '',
            ]"
            :style="columnStyle(column)"
            role="columnheader"
          >
            <slot :name="`header-${column.key}`" :column="column">
              {{ column.label }}
            </slot>
          </div>

          <div
            v-if="$slots.status"
            class="max-table__cell max-table__cell--status max-table__cell--head"
            role="columnheader"
          >
            <slot name="header-status">状态</slot>
          </div>

          <div
            v-if="$slots.actions"
            class="max-table__cell max-table__cell--actions max-table__cell--head"
            role="columnheader"
          >
            <slot name="header-actions">操作</slot>
          </div>
        </div>
      </div>

      <div
        ref="viewportRef"
        class="max-table__viewport"
        :class="{
          'max-table__viewport--scrollable-x': canScrollX,
          'max-table__viewport--scrollable-y': canScrollY,
          'max-table__viewport--dragging': dragging,
        }"
        :style="viewportStyle"
        @scroll="onViewportScroll"
        @pointerdown="onViewportPointerDown"
        @pointermove="onViewportPointerMove"
        @pointerup="endViewportDrag"
        @pointercancel="endViewportDrag"
        @click.capture="onViewportClickCapture"
      >
        <div class="max-table__track" :style="trackStyle">
          <div class="max-table__body" role="rowgroup">
            <div v-if="loading" class="max-table__overlay">
              <span class="max-table__spinner" />
            </div>

            <div v-if="!loading && !data.length" class="max-table__empty">
              <slot name="empty">{{ emptyText }}</slot>
            </div>

            <div
              v-for="(row, index) in data"
              :key="getRowKey(row)"
              class="max-table__row"
              role="row"
              @click="onRowClick(row, index)"
            >
              <div
                v-if="selectable"
                class="max-table__cell max-table__cell--checkbox"
                role="cell"
                @click.stop
              >
                <label class="max-check">
                  <input
                    type="checkbox"
                    class="max-check__input"
                    :checked="selectedSet.has(getRowKey(row))"
                    @change="toggleRow(row)"
                  />
                  <span class="max-check__box" aria-hidden="true" />
                </label>
              </div>

              <div
                v-for="column in columns"
                :key="column.key"
                class="max-table__cell"
                :class="[
                  column.className,
                  column.align ? `max-table__cell--${column.align}` : '',
                ]"
                :style="columnStyle(column)"
                role="cell"
              >
                <slot
                  :name="column.key"
                  :row="row"
                  :column="column"
                  :value="getCellValue(row, column)"
                  :index="index"
                >
                  {{ getCellValue(row, column) }}
                </slot>
              </div>

              <div
                v-if="$slots.status"
                class="max-table__cell max-table__cell--status"
                role="cell"
                @click.stop
              >
                <slot name="status" :row="row" :index="index" />
              </div>

              <div
                v-if="$slots.actions"
                class="max-table__cell max-table__cell--actions"
                role="cell"
                @click.stop
              >
                <slot name="actions" :row="row" :index="index" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.max-table {
  position: relative;
  width: 100%;
  max-width: 100%;
  /* flex 子项默认 min-width:auto，会被列宽撑开导致无法内部横向滚动 */
  min-width: 0;
  --max-text: #ffffff;
  --max-head-text: rgba(255, 255, 255, 0.96);
  --max-font-size: 16px;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.max-table--fill {
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  min-width: 0;
  min-height: 0;
  height: 100%;
  max-width: 100%;
}

.max-table__shell {
  padding: 10px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(24px) saturate(160%);
  -webkit-backdrop-filter: blur(24px) saturate(160%);
  border: 1px solid rgba(255, 255, 255, 0.22);
  box-shadow:
    0 0 0 0.5px rgba(255, 255, 255, 0.08),
    0 12px 40px rgba(0, 0, 0, 0.12);
  min-width: 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.max-table--fill .max-table__shell {
  flex: 1 1 auto;
  height: 100%;
}

.max-table__head-scroller {
  flex-shrink: 0;
  min-width: 0;
  overflow: hidden;
}

.max-table__viewport {
  flex: 1;
  min-width: 0;
  min-height: 0;
  overflow: auto;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.28) transparent;
}

.max-table__viewport--scrollable-x,
.max-table__viewport--scrollable-y {
  cursor: grab;
}

.max-table__viewport--dragging {
  cursor: grabbing;
  user-select: none;
}

.max-table__viewport::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.max-table__viewport::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.28);
}

.max-table__viewport::-webkit-scrollbar-track {
  background: transparent;
}

.max-table__track {
  min-width: max(100%, var(--max-track-min, 0px));
}

.max-table__head,
.max-table__row {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  min-width: var(--max-track-min, 0px);
}

.max-table__head {
  padding: 4px 12px 10px;
  color: var(--max-head-text);
  font-size: var(--max-font-size);
  font-weight: 500;
  letter-spacing: 0.03em;
  text-shadow:
    0 0 1px rgba(0, 0, 0, 0.45),
    0 1px 3px rgba(0, 0, 0, 0.28);
}


.max-table__body {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 48px;
}

.max-table__row {
  padding: 0 12px;
  min-height: 54px;
  border-radius: 12px;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.22);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.12);
  color: var(--max-text);
  font-size: var(--max-font-size);
  font-weight: 700;
  text-shadow:
    0 0 1px rgba(0, 0, 0, 0.5),
    0 1px 4px rgba(0, 0, 0, 0.32);
  transition:
    border-color 0.22s ease,
    transform 0.22s ease;
  cursor: pointer;
}

.max-table__row:hover {
  border-color: rgba(255, 255, 255, 0.36);
}

.max-table__cell {
  flex: 1 1 0;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--max-text);
  font-size: var(--max-font-size);
  font-weight: 700;
}

.max-table__cell--head {
  color: var(--max-head-text);
  font-weight: 500;
}

.max-table__cell :deep(*) {
  color: inherit;
  font-weight: inherit;
}

.max-table__cell--left {
  text-align: left;
}

.max-table__cell--center {
  text-align: center;
}

.max-table__cell--right {
  text-align: right;
}

.max-table__cell--checkbox {
  flex: 0 0 28px;
  width: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.max-table__cell--status {
  flex: 0 0 72px;
  width: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.max-table__cell--actions {
  flex: 0 0 168px;
  width: 168px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
}

.max-check {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.max-check__input {
  position: absolute;
  inset: 0;
  margin: 0;
  opacity: 0;
  cursor: pointer;
}

.max-check__box {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  border: 1.5px solid rgba(255, 255, 255, 0.42);
  background: rgba(255, 255, 255, 0.06);
  transition:
    background 0.18s ease,
    border-color 0.18s ease,
    box-shadow 0.18s ease;
}

.max-check__input:checked + .max-check__box {
  border-color: rgba(255, 255, 255, 0.85);
  background: rgba(255, 255, 255, 0.22);
  box-shadow: inset 0 0 0 2px rgba(255, 255, 255, 0.9);
}

.max-check__input:focus-visible + .max-check__box {
  outline: 2px solid rgba(255, 255, 255, 0.45);
  outline-offset: 2px;
}

.max-table__overlay {
  position: absolute;
  inset: 0;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

.max-table__spinner {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.22);
  border-top-color: rgba(255, 255, 255, 0.88);
  animation: max-spin 0.75s linear infinite;
}

.max-table__empty {
  padding: 28px 12px;
  text-align: center;
  color: #fff;
  font-size: var(--max-font-size);
  font-weight: 700;
  text-shadow:
    0 0 1px rgba(0, 0, 0, 0.45),
    0 1px 3px rgba(0, 0, 0, 0.28);
}

.max-table--loading .max-table__row {
  opacity: 0.55;
  pointer-events: none;
}

@keyframes max-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
