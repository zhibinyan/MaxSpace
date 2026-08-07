
import { ref, onUnmounted } from 'vue';

export function useTime() {
  const currentTime = ref('');
  let timer = null;

  const updateTime = () => {
    const now = new Date();
    currentTime.value = now.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  };

  const startTimer = () => {
    updateTime();
    timer = setInterval(updateTime, 1000);
  };

  const stopTimer = () => {
    if (timer) clearInterval(timer);
  };

  onUnmounted(() => {
    stopTimer();
  });

  return {
    currentTime,
    startTimer,
    stopTimer
  };
}
