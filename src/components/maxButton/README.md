# MaxButton 按钮

macOS 毛玻璃风格的**原生按钮**，不依赖 Element Plus `el-button`。适用于 MaxPopup、MaxConfirm、表单页、表格操作等场景。

## 导出

```ts
import {
  MaxButton,
  type MaxButtonVariant,
  type MaxButtonSize,
  type MaxButtonNativeType,
} from '@/components/maxButton'
```

## 基础用法

```vue
<MaxButton variant="primary" @click="handleSave">保存</MaxButton>
<MaxButton variant="ghost" @click="handleCancel">取消</MaxButton>
```

## 类型 `variant`

| 值 | 说明 | 典型场景 |
|----|------|----------|
| `primary` | 蓝色主按钮 | 保存、提交、确认 |
| `ghost` | 半透明次级按钮 | 取消、关闭 |
| `danger` | 红色危险按钮 | 删除确认、不可逆操作 |
| `text` | 无边框文字按钮 | 次要操作、工具栏 |
| `link` | 蓝色链接式按钮 | 表格行内「编辑」 |
| `link-danger` | 红色链接式按钮 | 表格行内「删除」 |

```vue
<MaxButton variant="primary">保存</MaxButton>
<MaxButton variant="ghost">取消</MaxButton>
<MaxButton variant="danger">删除</MaxButton>
<MaxButton variant="text">更多</MaxButton>
<MaxButton variant="link">编辑</MaxButton>
<MaxButton variant="link-danger">删除</MaxButton>
```

## Props

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `variant` | `MaxButtonVariant` | `'ghost'` | 按钮类型 |
| `size` | `'sm' \| 'md' \| 'lg'` | `'md'` | 尺寸 |
| `nativeType` | `'button' \| 'submit' \| 'reset'` | `'button'` | 原生 `<button type>` |
| `disabled` | `boolean` | `false` | 禁用 |
| `loading` | `boolean` | `false` | 加载中（自动禁用并显示 `loadingText`） |
| `loadingText` | `string` | `'提交中…'` | 加载中文案 |
| `block` | `boolean` | `false` | 块级按钮，占满容器宽度 |

未声明的 HTML 属性（如 `id`、`class`、`aria-*`）会通过 `$attrs` 透传到根 `<button>`。

## Events

| 事件 | 参数 | 说明 |
|------|------|------|
| `click` | `MouseEvent` | 点击（`disabled` / `loading` 时不会触发） |

## 尺寸

```vue
<MaxButton variant="primary" size="sm">小</MaxButton>
<MaxButton variant="primary" size="md">中</MaxButton>
<MaxButton variant="primary" size="lg">大</MaxButton>
```

| `size` | 高度 | 字号 |
|--------|------|------|
| `sm` | 28px | 13px |
| `md` | 34px | 14px |
| `lg` | 40px | 15px |

## 加载状态

```vue
<MaxButton variant="primary" :loading="saving" @click="save">
  保存
</MaxButton>
```

`loading` 为 `true` 时按钮禁用，文案替换为 `loadingText`（默认「提交中…」）。

## 块级按钮

```vue
<MaxButton variant="primary" block @click="submit">提交</MaxButton>
```

## 表单提交

```vue
<form @submit.prevent="onSubmit">
  <MaxButton native-type="submit" variant="primary">提交</MaxButton>
</form>
```

## 与 MaxPopup / MaxConfirm 配合

MaxPopup 顶栏：

```vue
<MaxButton variant="ghost" :disabled="confirming" @click="cancel">
  取消
</MaxButton>
<MaxButton variant="primary" :loading="confirming" @click="confirm">
  确定
</MaxButton>
```

MaxConfirm 删除确认：

```vue
<MaxButton variant="ghost" @click="onCancel">取消</MaxButton>
<MaxButton variant="danger" @click="onConfirm">删除</MaxButton>
```

## 对比 Element Plus

| | `el-button` | `MaxButton` |
|---|-------------|-------------|
| 风格 | Element 默认 | macOS 毛玻璃 / 系统蓝 |
| 依赖 | Element Plus | 无 |
| 链接按钮 | `link` + `type` | `variant="link"` / `link-danger` |
| 加载 | `loading` | `loading` + `loadingText` |

表格行内操作可优先使用 [`MaxActionBtn`](../maxTable/README.md#maxactionbtn)（图标按钮）；文字链式操作用 `variant="link"`。

## 注意事项

1. 默认 `variant` 为 `ghost`，主操作请显式写 `variant="primary"`
2. `loading` 与 `disabled` 同时为真时以 `loading` 文案为准
3. `link` / `link-danger` / `text` 类型 `min-width` 为 `auto`，适合紧凑布局
4. 需要图标 + 文字组合时，直接在默认插槽内写内容即可
