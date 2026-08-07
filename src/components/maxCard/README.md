# MaxCard 卡片

macOS 毛玻璃风格的**原生卡片布局**，不依赖 Element Plus `el-row` / `el-col` / `el-card`。视觉与 [`MaxTable`](../maxTable/README.md) 一致，适用于 Dashboard 统计区、内容面板、流程列表等场景。

## 导出

```ts
import { MaxCard, MaxCardRow, type MaxCardShadow } from '@/components/maxCard'
```

## 基础用法

`MaxCardRow` 负责 24 栅格与间距，`MaxCard` 负责单张卡片：

```vue
<MaxCardRow :gutter="20">
  <MaxCard v-for="item in stats" :key="item.title" :span="6">
    <p>{{ item.title }}</p>
    <p>{{ item.value }}</p>
  </MaxCard>
</MaxCardRow>
```

带标题区：

```vue
<MaxCardRow :gutter="20">
  <MaxCard :span="14">
    <template #header>访问趋势</template>
    <div class="chart-placeholder">...</div>
  </MaxCard>
  <MaxCard :span="10">
    <template #header>最近操作</template>
    <el-timeline>...</el-timeline>
  </MaxCard>
</MaxCardRow>
```

## 组件关系

```
MaxCardRow (:gutter="20")
├── MaxCard (:span="6")
├── MaxCard (:span="6")
├── MaxCard (:span="6")
└── MaxCard (:span="6")
```

- **一行总 span 为 24**，与 Element Plus 栅格规则相同（`span="6"` × 4 = 一整行）
- 子项通过 CSS Grid `grid-column: span N` 占位，**无需**再包 `el-col`

## MaxCardRow Props

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `gutter` | `number` | `20` | 卡片之间的间距（px），对应 `el-row :gutter` |

## MaxCard Props

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `span` | `number` | `6` | 占据的栅格列数（1–24），对应 `el-col :span` |
| `shadow` | `MaxCardShadow` | `'hover'` | 阴影模式：`'always' \| 'hover' \| 'never'` |

未声明的 HTML 属性（如 `class`、`id`）会通过 `$attrs` 透传到根节点。

## 插槽

| 插槽 | 说明 |
|------|------|
| 默认 | 卡片内容区（`.max-card__body`） |
| `header` | 可选标题区（`.max-card__header`），有内容时才渲染 |

## 阴影 `shadow`

```vue
<MaxCard :span="8" shadow="always">常驻阴影</MaxCard>
<MaxCard :span="8" shadow="hover">悬停加深（默认）</MaxCard>
<MaxCard :span="8" shadow="never">无阴影</MaxCard>
```

## 空卡片

无默认插槽内容时仍可占位，建议加最小高度：

```vue
<MaxCardRow :gutter="16">
  <MaxCard v-for="id in 10" :key="id" :span="6" class="min-h-[120px]" />
</MaxCardRow>
```

## Dashboard 示例

```vue
<script setup lang="ts">
import { MaxCard, MaxCardRow } from '@/components/maxCard'

const stats = [
  { title: '总用户数', value: '1,284' },
  { title: '今日访问', value: '3,562' },
  { title: '文章数量', value: '892' },
  { title: '月增长率', value: '12.5%' },
]
</script>

<template>
  <MaxCardRow :gutter="20">
    <MaxCard v-for="item in stats" :key="item.title" :span="6">
      <p class="stat-title">{{ item.title }}</p>
      <p class="stat-value">{{ item.value }}</p>
    </MaxCard>
  </MaxCardRow>
</template>
```

统计数字建议使用浅色文字（组件默认白字 + 文字阴影），避免在玻璃底上使用 `#303133` 等深色。

## 与 Element Plus 对比

| | `el-row` + `el-col` + `el-card` | `MaxCardRow` + `MaxCard` |
|---|--------------------------------|--------------------------|
| 布局 | Flex + 24 栅格 | CSS Grid 24 栅格 |
| 卡片容器 | `el-card` | 原生 `div` + 毛玻璃样式 |
| 间距 | `:gutter` | `:gutter`（`gap` 实现） |
| 列宽 | `:span` | `:span` |
| 标题 | `#header` 插槽 | `#header` 插槽 |
| 风格 | Element 默认白底 | macOS 毛玻璃，对齐 MaxTable |

## 内置子组件适配

卡片内已针对常见 Element 子组件做了浅色主题覆盖：

- `el-empty` 描述文字 → 半透明白
- `el-timeline` 节点、连线、时间戳 → 浅色

其他深色文字请在页面级 scoped 样式中改为 `rgba(255, 255, 255, …)`。

## 注意事项

1. `MaxCard` 必须放在 `MaxCardRow` 内，`span` 才生效
2. 同一行多个 `MaxCard` 的 `span` 之和不要超过 24，否则会换行
3. 需要行间距时，给 `MaxCardRow` 加 `class`（如 `margin-bottom`），或在外层容器控制
4. 卡片内容区默认 `font-weight: 700`；标题、辅助文字可在 slot 内自行覆盖
