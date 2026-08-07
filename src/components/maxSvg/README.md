# MaxSvg 图标

统一渲染 `src/assets/svg/` 目录下的 SVG 图标，替代手动 `import` + `<img>` 或 Element Plus `el-icon`。

## 导出

```ts
import {
  MaxSvg,
  svgMap,
  resolveSvgByName,
  type MaxSvgSize,
} from '@/components/maxSvg'
```

| 导出 | 说明 |
|------|------|
| `MaxSvg` | 图标组件 |
| `svgMap` | 文件名 → URL 映射表（构建时扫描 `@/assets/svg/*.svg`） |
| `resolveSvgByName` | 按文件名解析 SVG URL |
| `MaxSvgSize` | 预设尺寸类型 |

## 基础用法

按文件名引用（不含 `.svg` 扩展名）：

```vue
<script setup lang="ts">
import { MaxSvg } from '@/components/maxSvg'

function handleLogout() {
  // ...
}
</script>

<template>
  <MaxSvg name="loginout" alt="退出登录" @click="handleLogout" />
</template>
```

深色背景需要反色时，在使用处通过 `class` + CSS `filter` 处理，组件本身不修改 SVG 颜色：

```vue
<MaxSvg name="loginout" class="logout-icon" alt="退出登录" />
```

```css
.logout-icon {
  filter: brightness(0) invert(1);
}
```

## 直接传入 URL

`src` 优先级高于 `name`，适合引用 `assets/` 根目录或其他路径的 SVG：

```vue
<script setup lang="ts">
import logo from '@/assets/logo.svg'
import { MaxSvg } from '@/components/maxSvg'
</script>

<template>
  <MaxSvg :src="logo" size="lg" alt="Logo" />
</template>
```

## Props

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `name` | `string` | — | 文件名，对应 `@/assets/svg/{name}.svg` |
| `src` | `string` | — | 直接传入 SVG URL，优先级高于 `name` |
| `size` | `MaxSvgSize \| number` | `'md'` | 图标尺寸 |
| `alt` | `string` | `''` | 无障碍替代文本 |
| `opacity` | `number` | `1` | 透明度（0–1） |

未声明的 HTML 属性（如 `class`、`title`、`@click`）会通过 `$attrs` 透传到根 `<img>`。

## 尺寸 `size`

```vue
<MaxSvg name="setting" size="sm" />
<MaxSvg name="setting" size="md" />
<MaxSvg name="setting" size="lg" />
<MaxSvg name="setting" size="xl" />
<MaxSvg name="setting" :size="20" />
```

| `size` | 像素 |
|--------|------|
| `sm` | 12px |
| `md` | 14px |
| `lg` | 18px |
| `xl` | 24px |
| `number` | 自定义 |

## 与 AdminLayout 配合

顶部菜单栏退出按钮：

```vue
<MaxSvg
  name="loginout"
  :opacity="0.92"
  class="logout-icon"
  alt="退出登录"
  @click="handleLogout"
/>
```

## 编程式获取 SVG URL

无需渲染组件时，可直接使用 `svgMap` 或 `resolveSvgByName`：

```ts
import { svgMap, resolveSvgByName } from '@/components/maxSvg'

console.log(svgMap.loginout)           // 构建后的 URL
console.log(resolveSvgByName('menu'))  // 同上，找不到时返回 undefined
```

## 添加新图标

1. 将 `.svg` 文件放入 `src/assets/svg/`
2. 通过 `name` 引用即可，无需手动 import

```vue
<MaxSvg name="my-new-icon" />
```

> 图标在构建时通过 `import.meta.glob` 自动扫描；新增文件后若开发环境未生效，重启 dev server。

## 对比其他方案

| | 手动 `import` + `<img>` | `el-icon` + icons-vue | `MaxSvg` |
|---|-------------------------|----------------------|----------|
| 引用方式 | 每个图标单独 import | 按需 import 组件 | 仅传 `name` |
| 图标来源 | 任意路径 | Element Plus 内置 | `assets/svg/` |
| 尺寸控制 | 手写 CSS | `font-size` | `size` prop |
| 深色背景 | 手写 filter | `color` 继承 | 使用处 CSS filter |

## 注意事项

1. `name` 匹配 `src/assets/svg/` 下文件（含子目录）
2. `name` 或 `src` 均无效时，组件不渲染任何内容
3. 组件默认保持 SVG 原始颜色，不做任何着色或反色
4. 可点击图标建议同时设置 `alt` 并绑定 `@click`，或外层包 `<button>` 以提升可访问性
