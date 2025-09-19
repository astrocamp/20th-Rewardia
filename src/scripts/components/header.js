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
                if (window.RewardiaLogger) {
                  window.RewardiaLogger.warn('Header initialization error:', error);
                }
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

        // 行動選單狀態
        mobileMenuOpen: false,

        // 切換行動選單
        toggleMobileMenu() {
            this.mobileMenuOpen = !this.mobileMenuOpen;
            const toggleButton = document.getElementById('menu-toggle');

            // 更新 aria-expanded 屬性以提升無障礙性
            if (toggleButton) {
                toggleButton.setAttribute('aria-expanded', this.mobileMenuOpen.toString());
            }
        },

        // 關閉行動選單
        closeMobileMenu() {
            if (this.mobileMenuOpen) {
                this.mobileMenuOpen = false;
                const toggleButton = document.getElementById('menu-toggle');

                if (toggleButton) {
                    toggleButton.setAttribute('aria-expanded', 'false');
                }
            }
        }

    }));
});
