<script setup lang="ts">
withDefaults(
  defineProps<{
    gutter?: number
  }>(),
  {
    gutter: 20,
  },
)
</script>

<template>
  <div class="max-card-row" :style="{ gap: `${gutter}px` }">
    <slot />
  </div>
</template>

<style scoped>
.max-card-row {
  display: grid;
  grid-template-columns: repeat(24, 1fr);
}
</style>
