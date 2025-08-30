export default function () {
  return {
    init() {
      // 4 秒自動淡出（多則訊息稍微錯開）
      document.querySelectorAll('.tw-toast').forEach((el, i) => {
        setTimeout(() => {
          el.style.opacity = '0';
          el.style.transform = 'translateY(-6px)';
          setTimeout(() => el.remove(), 200);
        }, 4000 + i * 200);
      });
    }
  };
}
