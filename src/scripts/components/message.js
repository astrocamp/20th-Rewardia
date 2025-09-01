export default () => ({
  init() {
    this.$nextTick(() => {
      setTimeout(() => {
        this.$el.style.opacity = '0';
        this.$el.style.transform = 'translateY(-6px)';
        setTimeout(() => this.$el.remove(), 200);
      }, 4000);
    });
  }
});
