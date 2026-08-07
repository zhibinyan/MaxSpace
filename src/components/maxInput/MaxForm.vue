<template>
  <form class="max-form">
    <slot />
  </form>
</template>

<style scoped>
.max-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
