<script setup lang="ts">
import { computed, ref, watch, nextTick, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import type { MenuItem } from '@/api/menu'
import { MaxSvg } from '@/components/maxSvg'
import { getFullPath } from '@/router/dynamicRoutes'
import { useMenuStore } from '@/stores/menu'

const MAIN_COLS = 7
const MAIN_ROWS = 5
const MAIN_PAGE_SIZE = MAIN_COLS * MAIN_ROWS
const FOLDER_MAX = 9

type LaunchpadItem = {
  id: number
  title: string
  icon: string
  fullPath: string
  sortOrder: number
  isFolder: boolean
  children: LaunchpadItem[]
}

const open = defineModel<boolean>('open', { default: false })

const router = useRouter()
const menuStore = useMenuStore()

const keyword = ref('')
const currentPage = ref(0)
const activeFolder = ref<LaunchpadItem | null>(null)
const folderVisible = ref(false)
const shellVisible = ref(false)
const panelOpen = ref(false)
const shellClosing = ref(false)
const dockRef = ref<HTMLElement | null>(null)

const PANEL_MS = 400

function mapMenuItem(menu: MenuItem, parentPath = ''): LaunchpadItem {
  const fullPath = getFullPath(menu, parentPath)
  const children = sortItems(
    (menu.children ?? []).map((child) => mapMenuItem(child, fullPath)),
  )
  return {
    id: menu.id,
    title: menu.title,
    icon: menu.icon,
    fullPath,
    sortOrder: menu.sortOrder,
    isFolder: children.length > 0,
    children,
  }
}

function sortItems(items: LaunchpadItem[]) {
  return [...items].sort((a, b) => a.sortOrder - b.sortOrder || a.id - b.id)
}

const launchpadItems = computed(() =>
  sortItems(menuStore.tree.map((menu) => mapMenuItem(menu))),
)

const filteredItems = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  if (!query) return launchpadItems.value
  return launchpadItems.value.filter((item) => item.title.toLowerCase().includes(query))
})

const totalPages = computed(() =>
  Math.max(1, Math.ceil(filteredItems.value.length / MAIN_PAGE_SIZE)),
)

const pagedItems = computed(() => {
  const start = currentPage.value * MAIN_PAGE_SIZE
  return filteredItems.value.slice(start, start + MAIN_PAGE_SIZE)
})

const folderChildren = computed(() =>
  activeFolder.value ? activeFolder.value.children.slice(0, FOLDER_MAX) : [],
)

function folderPreviewChildren(item: LaunchpadItem) {
  return item.children.slice(0, FOLDER_MAX)
}

function resetView() {
  keyword.value = ''
  currentPage.value = 0
  activeFolder.value = null
  folderVisible.value = false
}

function closeDock() {
  open.value = false
}

function closeFolder() {
  folderVisible.value = false
}

function onFolderAfterLeave() {
  if (!folderVisible.value) activeFolder.value = null
}

function openFolder(item: LaunchpadItem) {
  activeFolder.value = item
  requestAnimationFrame(() => {
    folderVisible.value = true
  })
}

function openItem(item: LaunchpadItem) {
  if (item.isFolder) {
    openFolder(item)
    return
  }
  router.push(item.fullPath)
  closeDock()
}

function onBackdropClick() {
  if (folderVisible.value) {
    closeFolder()
    return
  }
  closeDock()
}

function onMainBlankClick() {
  if (folderVisible.value) {
    closeFolder()
    return
  }
  closeDock()
}

function onPanelAfterLeave() {
  if (open.value || !shellVisible.value) return
  shellVisible.value = false
  shellClosing.value = false
  document.body.style.overflow = ''
  resetView()
}

function onKeydown(event: KeyboardEvent) {
  if (!shellVisible.value) return
  if (event.key === 'Escape') {
    event.preventDefault()
    if (folderVisible.value) {
      closeFolder()
      return
    }
    closeDock()
  }
}

watch(keyword, () => {
  currentPage.value = 0
})

watch(open, async (visible) => {
  if (visible) {
    shellClosing.value = false
    panelOpen.value = false
    shellVisible.value = true
    document.body.style.overflow = 'hidden'
    resetView()
    await nextTick()
    if (!open.value) return
    panelOpen.value = true
    await nextTick()
    dockRef.value?.focus()
    return
  }
  shellClosing.value = true
  panelOpen.value = false
})

watch(
  () => menuStore.tree,
  () => {
    if (activeFolder.value) {
      const latest = launchpadItems.value.find((item) => item.id === activeFolder.value?.id)
      activeFolder.value = latest ?? null
      if (!activeFolder.value) closeFolder()
    }
  },
)

onUnmounted(() => {
  document.body.style.overflow = ''
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="shellVisible"
      ref="dockRef"
      class="app-dock"
      :class="{ 'app-dock--closing': shellClosing }"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
      aria-label="程序坞"
      @keydown="onKeydown"
    >
      <div class="app-dock__blur" aria-hidden="true" />

      <button
        type="button"
        class="app-dock__backdrop"
        aria-label="关闭程序坞"
        @click="onBackdropClick"
      />

      <Transition
        name="app-dock-fade"
        appear
        :duration="{ enter: PANEL_MS, leave: PANEL_MS }"
        @after-leave="onPanelAfterLeave"
      >
        <div
          v-if="panelOpen"
          class="app-dock__panel"
          :class="{ 'app-dock__panel--dimmed': folderVisible }"
        >
          <div class="app-dock__search-wrap">
            <div class="app-dock__search">
              <svg class="app-dock__search-icon" viewBox="0 0 16 16" aria-hidden="true">
                <circle cx="7" cy="7" r="4.5" stroke="currentColor" stroke-width="1.4" fill="none" />
                <path
                  d="M10.5 10.5L14 14"
                  stroke="currentColor"
                  stroke-width="1.4"
                  stroke-linecap="round"
                />
              </svg>
              <input
                v-model="keyword"
                class="app-dock__search-input"
                type="search"
                placeholder="搜索"
              />
            </div>
          </div>

          <div class="app-dock__main" @click.self="onMainBlankClick">
            <div class="app-dock__grid app-dock__grid--main" @click.self="onMainBlankClick">
              <button
                v-for="item in pagedItems"
                :key="item.id"
                type="button"
                class="app-dock__cell"
                :data-menu-id="item.id"
                :data-sort-order="item.sortOrder"
                draggable="false"
                @click="openItem(item)"
              >
                <div v-if="item.isFolder" class="app-dock__folder">
                  <div class="app-dock__folder-grid">
                    <span
                      v-for="child in folderPreviewChildren(item)"
                      :key="child.id"
                      class="app-dock__folder-mini"
                    >
                      <MaxSvg :name="child.icon" :size="16" />
                    </span>
                  </div>
                </div>
                <div v-else class="app-dock__icon">
                  <MaxSvg :name="item.icon" :size="64" />
                </div>
                <span class="app-dock__label">{{ item.title }}</span>
              </button>
            </div>

            <div v-if="totalPages > 1" class="app-dock__pager">
              <button
                v-for="page in totalPages"
                :key="page"
                type="button"
                class="app-dock__dot"
                :class="{ 'app-dock__dot--active': page - 1 === currentPage }"
                :aria-label="`第 ${page} 页`"
                @click="currentPage = page - 1"
              />
            </div>
          </div>
        </div>
      </Transition>

      <Transition name="app-dock-folder" @after-leave="onFolderAfterLeave">
        <div
          v-if="activeFolder && folderVisible && panelOpen"
          class="app-dock__folder-layer"
          @click="closeFolder"
        >
          <div class="app-dock__folder-stack" @click.stop>
            <div class="app-dock__folder-title">{{ activeFolder.title }}</div>
            <div
              class="app-dock__folder-popup"
              role="dialog"
              :aria-label="`${activeFolder.title} 文件夹`"
            >
              <div class="app-dock__grid app-dock__grid--folder">
                <button
                  v-for="child in folderChildren"
                  :key="child.id"
                  type="button"
                  class="app-dock__cell"
                  :data-menu-id="child.id"
                  :data-sort-order="child.sortOrder"
                  draggable="false"
                  @click="openItem(child)"
                >
                  <div v-if="child.isFolder" class="app-dock__folder app-dock__folder--sm">
                    <div class="app-dock__folder-grid">
                      <span
                        v-for="grand in folderPreviewChildren(child)"
                        :key="grand.id"
                        class="app-dock__folder-mini"
                      >
                        <MaxSvg :name="grand.icon" :size="10" />
                      </span>
                    </div>
                  </div>
                  <div v-else class="app-dock__icon app-dock__icon--sm">
                    <MaxSvg :name="child.icon" :size="48" />
                  </div>
                  <span class="app-dock__label">{{ child.title }}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </div>
  </Teleport>
</template>

<style scoped>
.app-dock {
  --dock-col: 112px;
  --dock-row: 118px;
  --dock-col-gap: 74px;
  --dock-row-gap: 54px;
  --dock-icon: 88px;
  --dock-bottom-reserve: 40px;
  --dock-main-duration: 0.4s;
  --dock-panel-duration: 0.32s;
  --dock-panel-ease: cubic-bezier(0.22, 1, 0.36, 1);

  position: fixed;
  inset: 0;
  z-index: 12000;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.app-dock__blur {
  position: absolute;
  inset: 0;
  backdrop-filter: blur(42px) saturate(140%);
  -webkit-backdrop-filter: blur(42px) saturate(140%);
  background: rgba(20, 16, 28, 0.28);
  opacity: 1;
}

.app-dock--closing .app-dock__blur {
  opacity: 0;
  transition: opacity var(--dock-main-duration) var(--dock-panel-ease);
}

.app-dock--closing {
  z-index: 90;
  pointer-events: none;
}

.app-dock__backdrop {
  position: absolute;
  inset: 0;
  border: none;
  background: transparent;
  cursor: default;
}

.app-dock__panel {
  position: relative;
  z-index: 1;
  width: min(1120px, 92vw);
  height: min(820px, 90vh);
  margin-top: -32px;
  display: flex;
  flex-direction: column;
  pointer-events: none;
  transform-origin: center center;
  transition:
    opacity var(--dock-panel-duration) var(--dock-panel-ease),
    transform var(--dock-panel-duration) var(--dock-panel-ease),
    filter var(--dock-panel-duration) var(--dock-panel-ease);
}

.app-dock__panel--dimmed {
  opacity: 0.52;
  transform: scale(0.98);
  filter: blur(0.6px);
  pointer-events: none;
}

.app-dock__search-wrap {
  display: flex;
  justify-content: center;
  padding: 0px 0 16px;
  pointer-events: auto;
}

.app-dock__search {
  display: flex;
  align-items: center;
  gap: 8px;
  width: min(260px, 72vw);
  height: 34px;
  padding: 0 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.app-dock__search-icon {
  width: 14px;
  height: 14px;
  color: rgba(255, 255, 255, 0.72);
  flex-shrink: 0;
}

.app-dock__search-input {
  flex: 1;
  min-width: 0;
  border: none;
  outline: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.95);
  font-size: 14px;
}

.app-dock__search-input::placeholder {
  color: rgba(255, 255, 255, 0.58);
}

.app-dock__main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  pointer-events: auto;
}

.app-dock__grid {
  display: grid;
  justify-content: center;
  align-content: start;
  padding: 8px 12px 0;
}

.app-dock__grid--main {
  grid-template-columns: repeat(7, var(--dock-col));
  grid-auto-rows: var(--dock-row);
  gap: var(--dock-row-gap) var(--dock-col-gap);
  flex: 1;
  min-height: 0;
  padding: 12px 12px var(--dock-bottom-reserve);
}

.app-dock__grid--main .app-dock__cell {
  width: var(--dock-col);
  height: var(--dock-row);
  gap: 12px;
  justify-content: flex-start;
}

.app-dock__grid--main .app-dock__icon,
.app-dock__grid--main .app-dock__folder {
  width: var(--dock-icon);
  height: var(--dock-icon);
  border-radius: 20px;
  flex-shrink: 0;
}

.app-dock__grid--main .app-dock__label {
  max-width: var(--dock-col);
  min-height: 30px;
  display: flex;
  align-items: flex-start;
  justify-content: center;
}

.app-dock__grid--folder {
  display: grid;
  grid-template-columns: repeat(3, var(--folder-col));
  grid-template-rows: repeat(3, var(--folder-row));
  gap: var(--folder-gap);
  width: calc(var(--folder-col) * 3 + var(--folder-gap) * 2);
  height: calc(var(--folder-row) * 3 + var(--folder-gap) * 2);
  padding: 0;
  flex-shrink: 0;
}

.app-dock__grid--folder .app-dock__cell {
  width: var(--folder-col);
  height: var(--folder-row);
  gap: 8px;
  justify-content: flex-start;
}

.app-dock__grid--folder .app-dock__label {
  max-width: var(--folder-col);
  min-height: 30px;
  display: flex;
  align-items: flex-start;
  justify-content: center;
}

.app-dock__folder-stack {
  --folder-col: var(--dock-col);
  --folder-row: var(--dock-row);
  --folder-gap: var(--dock-col-gap);
  --folder-icon: 76px;
  --folder-pad-x: 48px;
  --folder-pad-y: 40px;

  display: flex;
  flex-direction: column;
  align-items: center;
  pointer-events: auto;
}

.app-dock__folder-layer {
  position: absolute;
  inset: 0;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.18);
}

.app-dock__folder-popup {
  box-sizing: border-box;
  width: calc(var(--folder-pad-x) * 2 + var(--folder-col) * 3 + var(--folder-gap) * 2);
  height: calc(
    var(--folder-pad-y) * 2 + var(--folder-row) * 3 + var(--folder-gap) * 2
  );
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--folder-pad-y) var(--folder-pad-x);
  border-radius: 28px;
  background: rgba(72, 72, 78, 0.72);
  backdrop-filter: blur(36px) saturate(160%);
  -webkit-backdrop-filter: blur(36px) saturate(160%);
  border: 1px solid rgba(255, 255, 255, 0.14);
  box-shadow:
    0 24px 64px rgba(0, 0, 0, 0.38),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.app-dock__folder-title {
  width: calc(var(--folder-pad-x) * 2 + var(--folder-col) * 3 + var(--folder-gap) * 2);
  margin: 0 0 14px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 600;
  text-align: center;
  color: rgba(255, 255, 255, 0.92);
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.35);
}

.app-dock__cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  border: none;
  background: transparent;
  cursor: pointer;
  padding: 0;
  color: #fff;
  transition: transform 0.18s ease;
}

.app-dock__cell:hover {
  transform: scale(1.04);
}

.app-dock__cell:active {
  transform: scale(0.96);
}

.app-dock__icon,
.app-dock__folder {
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 10px 24px rgba(0, 0, 0, 0.18),
    inset 0 0 0 0.5px rgba(255, 255, 255, 0.18);
}

.app-dock__icon {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.18), rgba(255, 255, 255, 0.06));
}

.app-dock__icon--sm {
  width: var(--folder-icon, 76px);
  height: var(--folder-icon, 76px);
  border-radius: 18px;
  flex-shrink: 0;
}

.app-dock__folder {
  background: rgba(255, 255, 255, 0.22);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  padding: 8px;
}

.app-dock__folder--sm {
  width: var(--folder-icon, 76px);
  height: var(--folder-icon, 76px);
  border-radius: 18px;
  padding: 8px;
  flex-shrink: 0;
}

.app-dock__folder-grid {
  width: 100%;
  height: 100%;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: repeat(3, 1fr);
  gap: 3px;
}

.app-dock__folder-mini {
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.12);
}

.app-dock__label {
  font-size: 12px;
  line-height: 1.25;
  text-align: center;
  color: rgba(255, 255, 255, 0.96);
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.45);
  word-break: break-word;
}

.app-dock__pager {
  display: flex;
  justify-content: center;
  gap: 8px;
  padding: 8px 0 12px;
  flex-shrink: 0;
}

.app-dock__dot {
  width: 7px;
  height: 7px;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.34);
  cursor: pointer;
}

.app-dock__dot--active {
  background: rgba(255, 255, 255, 0.92);
}

.app-dock-fade-enter-active,
.app-dock-fade-leave-active {
  transition:
    opacity var(--dock-main-duration) var(--dock-panel-ease),
    transform var(--dock-main-duration) var(--dock-panel-ease);
}

.app-dock-fade-enter-from,
.app-dock-fade-leave-to {
  opacity: 0;
  transform: scale(0.78);
}

.app-dock-folder-enter-active,
.app-dock-folder-leave-active {
  transition: opacity var(--dock-panel-duration) var(--dock-panel-ease);
}

.app-dock-folder-enter-active .app-dock__folder-stack,
.app-dock-folder-leave-active .app-dock__folder-stack {
  transition:
    opacity var(--dock-panel-duration) var(--dock-panel-ease),
    transform var(--dock-panel-duration) var(--dock-panel-ease);
}

.app-dock-folder-enter-from,
.app-dock-folder-leave-to {
  opacity: 0;
}

.app-dock-folder-enter-from .app-dock__folder-stack,
.app-dock-folder-leave-to .app-dock__folder-stack {
  opacity: 0;
  transform: scale(0.78);
}
</style>
