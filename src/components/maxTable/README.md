# MaxTable 液态玻璃表格

macOS 毛玻璃风格的**原生 Flex 表格**，不依赖 Element Plus `el-table`。每行独立圆角边框，透明背景 + 模糊外壳，适合深色桌面背景。

## 导出

```ts
import {
  MaxTable,
  MaxActionBtn,
  type MaxColumn,
  type MaxRowContext,
  type MaxCellContext,
  type MaxAlign,
  type MaxActionIcon,
} from '@/components/maxTable'
```

## 基础用法

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { MaxTable, type MaxColumn } from '@/components/maxTable'

interface User {
  id: number
  name: string
  email: string
}

const loading = ref(false)
const users = ref<User[]>([])

const columns: MaxColumn<User>[] = [
  { key: 'id', label: 'ID', width: 72, align: 'center' },
  { key: 'name', label: '姓名', minWidth: 120 },
  { key: 'email', label: '邮箱', minWidth: 180 },
]
</script>

<template>
  <MaxTable
    :columns="columns"
    :data="users"
    :loading="loading"
    row-key="id"
  />
</template>
```

未自定义插槽时，单元格会直接显示 `row[column.key]` 的值。

## Props

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `columns` | `MaxColumn<T>[]` | — | 列配置（必填） |
| `data` | `T[]` | — | 行数据（必填） |
| `rowKey` | `keyof T & string` | `'id'` | 行唯一标识字段 |
| `loading` | `boolean` | `false` | 加载中，显示遮罩 + 半透明行 |
| `selectable` | `boolean` | `false` | 是否显示多选列 |
| `modelValue` | `(string \| number)[]` | `[]` | 选中行的 key 列表，`selectable` 时配合 `v-model` |
| `emptyText` | `string` | `'暂无数据'` | 无数据时的文案 |
| `maxHeight` | `string \| number` | `'min(65vh, 640px)'` | 表体区域最大高度，超出后纵向滚动 |

## Events

| 事件 | 参数 | 说明 |
|------|------|------|
| `update:modelValue` | `(string \| number)[]` | 多选变化时触发 |
| `row-click` | `{ row: T, index: number }` | 点击行（操作列、多选列、status 列不会冒泡） |

## 列配置 `MaxColumn<T>`

```ts
interface MaxColumn<T> {
  key: keyof T & string   // 字段 key，也是默认插槽名
  label: string           // 表头文案
  width?: string | number // 固定列宽，如 72 / '120px'
  minWidth?: string | number
  align?: 'left' | 'center' | 'right'
  className?: string      // 额外 class
}
```

**列宽规则：**

- 设置了 `width` → 固定宽度，不参与压缩；总宽度超出容器时在表格内横向滚动
- 未设置 `width` → `flex: 1 1 0` 均分剩余空间，默认最小宽度 `120px`（可用 `minWidth` 覆盖）
- 表体默认最大高度 `min(65vh, 640px)`，行数多时在表格内纵向滚动；可通过 `maxHeight` 调整
- 表头固定，表体横纵滚动；横向滚动时表头与表体通过 `requestAnimationFrame` 同步 `scrollLeft`

## 插槽

### 数据列插槽

插槽名 = 列的 `key`，作用域参数：

| 参数 | 说明 |
|------|------|
| `row` | 当前行数据 |
| `column` | 列配置 |
| `value` | `row[column.key]` |
| `index` | 行索引 |

```vue
<template #isSuper="{ row }">
  <span>{{ row.isSuper ? '超级管理员' : '普通管理员' }}</span>
</template>
```

### 表头插槽

插槽名 = `header-${column.key}`，作用域参数：`{ column }`

```vue
<template #header-username="{ column }">
  {{ column.label }} *
</template>
```

### 固定扩展列

| 插槽 | 表头插槽 | 作用域参数 | 说明 |
|------|----------|------------|------|
| `status` | `header-status`（默认「状态」） | `{ row, index }` | 右侧状态列，宽 72px |
| `actions` | `header-actions`（默认「操作」） | `{ row, index }` | 最右操作列，宽 168px |
| `empty` | — | — | 自定义空状态 |

> 只有使用了 `#status` 或 `#actions` 插槽时，对应列才会渲染。

## 多选

```vue
<script setup lang="ts">
const selectedIds = ref<Array<string | number>>([])
</script>

<template>
  <MaxTable
    v-model="selectedIds"
    selectable
    :columns="columns"
    :data="admins"
    row-key="id"
  />
</template>
```

表头 checkbox 支持全选 / 半选（indeterminate）。

## 配套组件

### MaxActionBtn

操作列常用的小图标按钮，内置 `edit` / `delete` 图标。

```vue
<template #actions="{ row }">
  <MaxActionBtn icon="edit" title="编辑" @click="openEdit(row)" />
  <MaxActionBtn
    icon="delete"
    title="删除"
    :disabled="row.isSuper"
    @click="removeRow(row)"
  />
</template>
```

| Prop | 类型 | 默认 | 说明 |
|------|------|------|------|
| `icon` | `'edit' \| 'delete'` | — | 内置图标 |
| `title` | `string` | `''` | hover 提示 |
| `disabled` | `boolean` | `false` | 禁用 |

也可通过默认 slot 传入自定义 SVG。

## 完整示例

### 管理员列表（含多选、自定义列、操作列）

见 `src/views/settings/AdminListView.vue`：

```vue
<MaxTable
  v-model="selectedIds"
  :columns="columns"
  :data="admins"
  :loading="loading"
  selectable
  row-key="id"
>
  <template #isSuper="{ row }">
    <span class="role-badge" :class="row.isSuper ? 'role-badge--super' : 'role-badge--normal'">
      {{ row.isSuper ? '超级管理员' : '普通管理员' }}
    </span>
  </template>

  <template #actions="{ row }">
    <MaxActionBtn icon="edit" title="编辑" @click="openEdit(row)" />
    <MaxActionBtn icon="delete" title="删除" :disabled="row.isSuper" @click="removeAdmin(row)" />
  </template>
</MaxTable>
```

### 菜单管理（无多选）

见 `src/views/settings/MenuManagementView.vue`：

```vue
<MaxTable
  :columns="columns"
  :data="menus"
  :loading="loading"
  row-key="id"
>
  <template #parentId="{ row }">
    {{ getParentTitle(row.parentId) }}
  </template>

  <template #keepAlive="{ row }">
    <span class="cache-badge" :class="row.keepAlive ? 'cache-badge--yes' : 'cache-badge--no'">
      {{ row.keepAlive ? '是' : '否' }}
    </span>
  </template>

  <template #actions="{ row }">
    <MaxActionBtn icon="edit" title="编辑" @click="openEdit(row)" />
    <MaxActionBtn icon="delete" title="删除" :disabled="!isSuper" @click="removeMenu(row)" />
  </template>
</MaxTable>
```

## 布局结构

```
┌─ max-table__shell（毛玻璃外壳）──────────────────────────────┐
│  [□]  ID    用户名    类型    创建时间    更新时间    操作  │  ← head
│  ─────────────────────────────────────────────────────  │
│  [□]  1     admin     超级     2026-…      2026-…    ✎ 🗑  │  ← row
│  [□]  2     user1     普通     2026-…      2026-…    ✎ 🗑  │
└─────────────────────────────────────────────────────────────────┘
```

## 样式说明

- 表格使用 CSS 变量，可在父级覆盖：
  - `--max-text`：正文颜色（默认 `#ffffff`）
  - `--max-head-text`：表头颜色
  - `--max-font-size`：字号（默认 `16px`）
- 行背景为**透明**，仅保留边框；自定义 badge / 标签样式请在页面层 `scoped` 中编写
- 单元格默认 `white-space: nowrap` + 省略号，长文本请用插槽自行处理

## 注意事项

1. **泛型**：`MaxTable` 支持泛型 `T`，定义 `columns` 时建议写 `MaxColumn<YourType>[]`，key 会有类型提示
2. **rowKey**：确保每行该字段唯一；缺失时会 fallback 到 `JSON.stringify(row)`
3. **行点击**：整行可点，操作列 / 多选 / status 列已 `@click.stop`，不会触发行点击
4. **loading**：加载时行半透明且不可交互，表体上方显示 spinner 遮罩
5. **与 Element Plus 表格的区别**：无内置分页、排序、筛选；需在页面层自行实现
