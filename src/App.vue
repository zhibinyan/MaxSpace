<template>
  <router-view />
  <MacNotificationHost />
  <MaxPopupHost />
  <MaxConfirmHost />
</template>

<script setup lang="ts">
import { MaxConfirmHost } from '@/components/maxConfirm'
import { MacNotificationHost } from '@/components/massage'
import { MaxPopupHost } from '@/components/maxPopup'
</script>
