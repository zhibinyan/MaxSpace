# MaxSvgPicker 图标选择器

macOS 风格的 **SVG 图标选择器**，自动读取 `src/assets/svg/` 目录下的图标，配合 [`MaxSvg`](../maxSvg/README.md) 渲染。适用于表单字段、弹窗内选图标等场景。

## 导出

```ts
import { MaxSvgPicker, MaxSvgGrid } from '@/components/maxSvgPicker'
```

| 导出 | 说明 |
|------|------|
| `MaxSvgPicker` | 带触发器 + 下拉面板的完整选择器 |
| `MaxSvgGrid` | 独立的搜索 + 网格集合（无触发器） |

## 基础用法

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { MaxSvgPicker } from '@/components/maxSvgPicker'

const icon = ref('menu')
</script>

<template>
  <MaxSvgPicker v-model="icon" label="图标" />
</template>
```

`v-model` 绑定的是 SVG **文件名**（不含 `.svg`），例如 `menu` 对应 `@/assets/svg/menu.svg`。

## 与 MaxForm 配合

布局与 `MaxInput`、`MaxSelect` 一致：传入 `label` 时左侧 80px 标签 + 右侧控件。

```vue
<MaxForm @submit.prevent>
  <MaxSvgPicker id="menu-icon" v-model="form.icon" label="图标" />
</MaxForm>
```

当前已在 [`MenuFormBody.vue`](../../views/settings/menu/MenuFormBody.vue) 中用于菜单图标选择。

## 独立网格 `MaxSvgGrid`

不需要触发器、只要图标集合面板时，可直接使用 `MaxSvgGrid`：

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { MaxSvgGrid } from '@/components/maxSvgPicker'

const icon = ref('')
</script>

<template>
  <MaxSvgGrid v-model="icon" :columns="8" :icon-size="32" />
</template>
```

## MaxSvgPicker Props

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `v-model` | `string` | `''` | 选中的 SVG 文件名 |
| `label` | `string` | — | 表单标签；传入后启用左右布局 |
| `id` | `string` | — | 触发按钮 `id`，并与 `label` 关联 |
| `placeholder` | `string` | `'选择图标'` | 未选中时的占位文案 |
| `columns` | `number` | `6` | 网格列数（传给内部 `MaxSvgGrid`） |
| `iconSize` | `number` | `28` | 网格内图标尺寸（px） |

未声明的 HTML 属性（如 `class`、`disabled`）会通过 `$attrs` 透传到触发按钮。

## MaxSvgPicker Events

| 事件 | 参数 | 说明 |
|------|------|------|
| `change` | `value: string` | 选中图标后触发（同时更新 `v-model` 并关闭面板） |

## MaxSvgGrid Props

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `v-model` | `string` | `''` | 当前选中的 SVG 文件名 |
| `columns` | `number` | `6` | 网格列数 |
| `iconSize` | `number` | `28` | 每个图标的尺寸（px） |
| `searchPlaceholder` | `string` | `'搜索'` | 搜索框占位符 |
| `emptyText` | `string` | `'未找到图标'` | 搜索无结果时的提示 |

## 交互说明

| 行为 | 说明 |
|------|------|
| 点击触发器 | 展开 / 收起下拉面板 |
| 点击图标 | 选中并自动关闭面板 |
| 点击外部 | 通过 `mousedown` 捕获阶段检测，点击组件外任意区域关闭面板 |
| 搜索 | 按文件名实时过滤（不区分大小写） |
| 指向箭头 | 面板顶部中央有 caret，指向上方触发器 |

> 在 `MaxPopup` 等带 `@click.stop` 的容器内也能正常「点击空白关闭」，因为外部检测使用捕获阶段而非冒泡。

## 图标来源

与 `MaxSvg` 共用 [`svgMap`](../maxSvg/svgMap.ts)，构建时扫描 `@/assets/svg/**/*.svg`：

1. 将 `.svg` 放入 `src/assets/svg/`
2. 重启 dev server 后即可在列表中看到
3. 通过 `v-model` 存文件名，用 [`MaxSvg`](../maxSvg/README.md) 渲染

## 与 MaxPopup 配合

```ts
void MaxPopup.open({
  title: '编辑菜单',
  content: MenuFormBody,
  contentProps: { form },
  onConfirm: saveMenu,
})
```

弹窗内使用 `MaxSvgPicker` 时：

- 展开后 `z-index: 20`，面板 `z-index: 50`，避免被下方表单项遮挡
- 若面板底部被弹窗 `overflow: auto` 裁切，可考虑后续改为 `Teleport` 到 `body`

## 样式结构

```
max-svg-picker
├── max-svg-picker__label        # 可选标签
└── max-svg-picker__field
    ├── max-svg-picker__trigger  # 触发按钮（预览图标 / 占位符）
    └── max-svg-picker__panel    # 下拉容器
        ├── max-svg-picker__caret # 向上指向箭头
        └── MaxSvgGrid            # 搜索 + 网格
```

## 对比 Element Plus

| | `el-select` + 文字选项 | `MaxSvgPicker` |
|---|------------------------|----------------|
| 选项展示 | 纯文字 | SVG 图标预览 + 网格 |
| 图标来源 | 需手动维护 options | 自动扫描 `assets/svg` |
| 搜索 | 需自行实现 | 内置 |
| 风格 | Element 默认 | macOS 深色面板 |

## 注意事项

1. `v-model` 值为 SVG **文件名**，不是 Element Plus 图标组件名（如 `Menu`）
2. 选中后仅存字符串；渲染时配合 [`MaxSvg`](../maxSvg/README.md)
3. 新增 SVG 文件后若列表未更新，重启 dev server
4. 网格默认可滚动，最高 `240px`；图标较多时可搜索快速定位
