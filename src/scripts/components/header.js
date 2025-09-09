document.addEventListener('alpine:init', () => {
    // 全域 banner 狀態
    Alpine.store('banner', {
        visible: true,
        height: 0,
        isInitialized: false,
        isTransitioning: false,

        init() {
            // 檢查 localStorage 中的關閉狀態
            this.visible = localStorage.getItem('bannerClosed') !== 'true';
            this.isInitialized = true;
        },

        close() {
            this.isTransitioning = true;
            this.visible = false;
            localStorage.setItem('bannerClosed', 'true');
            
            // 動畫完成後移除 transitioning 狀態
            setTimeout(() => {
                this.isTransitioning = false;
            }, 300);
        },

        reset() {
            this.isTransitioning = true;
            this.visible = true;
            localStorage.removeItem('bannerClosed');
            
            // 動畫完成後移除 transitioning 狀態
            setTimeout(() => {
                this.isTransitioning = false;
            }, 300);
        }
    });

    // Header 組件
    Alpine.data('header', () => ({
        // 快取 banner store 引用
        get banner() {
            return Alpine.store('banner');
        },

        init() {
            // 初始化全域狀態
            this.banner.init();
            
            this.$nextTick(() => {
                this.initializeBanner();
            });
        },

        // 初始化 banner 高度
        initializeBanner() {
            try {
                this.banner.height = this.$refs.topBanner?.offsetHeight || 0;
            } catch (error) {
                console.warn('Header initialization error:', error);
            }
        },

        // 處理滾動邏輯
        handleScroll() {
            requestAnimationFrame(() => {
                if (!this.banner.isInitialized || !this.banner.visible) return;
                
                if (window.scrollY > this.banner.height) {
                    this.banner.visible = false;
                }
            });
        },

    }));
});
