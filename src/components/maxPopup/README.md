# MaxPopup 表单弹窗

macOS 毛玻璃风格**表单弹窗**，顶栏固定（标题 + 确定/取消），下方 body 区域可滚动放表单。

> 删除确认、二次确认请用 [`../maxConfirm/README.md`](../maxConfirm/README.md) 里的 `MaxConfirm`。

## 挂载

```vue
<MaxPopupHost />
```

## 基础用法

```ts
import MaxPopup from '@/components/maxPopup'
import MyFormBody from './MyFormBody.vue'

const ok = await MaxPopup.open({
  title: '编辑提报内容',
  content: MyFormBody,
  contentProps: {
    modelValue: form,
    'onUpdate:modelValue': (v) => Object.assign(form, v),
  },
  onConfirm: async () => {
    await submitForm()
    return true // 返回 false 阻止关闭
  },
})
```

## 配置项

| 字段 | 说明 | 默认 |
|------|------|------|
| `title` | 标题 | `编辑` |
| `size` | `sm` / `md` / `lg` | `md` |
| `direction` | `top` / `bottom` / `left` / `right` | `top` |
| `content` | 表单 Vue 组件 | — |
| `contentProps` | 传给 content 的 props | — |
| `onConfirm` | 确定回调，返回 `false` 不关闭 | — |
| `onCancel` | 取消回调 | — |
| `confirmText` | 确定文案 | `确定` |
| `cancelText` | 取消文案 | `取消` |
| `showCancel` | 是否显示取消 | `true` |

## 布局

```
┌─────────────────────────────────────┐
│ ●●●   标题          [取消] [确定]   │  ← 固定不滚动
├─────────────────────────────────────┤
│                                     │
│   表单 content 组件（可滚动）        │
│                                     │
└─────────────────────────────────────┘
```

## 原生表单样式

content 组件内可使用全局类名（由 MaxPopupHost 提供）：

```html
<form class="max-popup-form">
  <div class="max-popup-form__row">
    <label class="max-popup-form__label">用户名</label>
    <input class="max-popup-form__input" />
  </div>
</form>
```

## 示例

见 `src/views/settings/AdminListView.vue` + `AdminFormBody.vue`。
