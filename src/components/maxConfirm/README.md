# MaxConfirm 确认 / 删除弹窗

专门用于**删除确认**和**二次确认**的轻量弹窗，不是表单容器。

> 编辑表单请用 [`../maxPopup/README.md`](../maxPopup/README.md) 里的 `MaxPopup`。

## 挂载

```vue
<MaxConfirmHost />
```

## 删除确认

```ts
import MaxConfirm from '@/components/maxConfirm'

const ok = await MaxConfirm.delete({
  title: '删除确认',
  message: '确定删除该管理员吗？此操作不可恢复。',
})

if (ok) {
  await deleteAdmin(id)
}
```

简写：

```ts
const ok = await MaxConfirm.delete('确定删除吗？')
```

## 普通确认

```ts
const ok = await MaxConfirm.open({
  title: '提示',
  message: '是否保存当前修改？',
  confirmText: '保存',
})
```

## 对比 MaxPopup

| | MaxPopup | MaxConfirm |
|---|----------|------------|
| 用途 | 表单编辑 | 删除 / 二次确认 |
| 内容 | `content` 组件 | `message` 文本 |
| 按钮位置 | 顶栏右上 | 底部居中 |
| 确定按钮 | 蓝色 | 删除时红色 |

## 关闭方式

- 确定 → `true`
- 取消 / 红灯 / Esc / 点遮罩 → `false`
- Enter → `true`

## 示例

见 `src/views/settings/AdminListView.vue` 的 `removeAdmin`。
