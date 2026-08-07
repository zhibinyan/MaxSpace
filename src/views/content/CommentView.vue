<script setup lang="ts">
defineOptions({ name: 'CommentView' })

const SRC = 'https://xdclass.net/'
</script>

<template>
  <div class="embed-page">
    <iframe
      class="embed-page__frame"
      :src="SRC"
      title="评论管理"
      referrerpolicy="no-referrer-when-downgrade"
      allow="fullscreen"
    />
  </div>
</template>

<style scoped>
.embed-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  border-radius: 12px;
}

.embed-page__frame {
  flex: 1;
  width: 100%;
  min-height: 0;
  border: 0;
  background: #fff;
}
</style>
