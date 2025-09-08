document.addEventListener('alpine:init', () => {
    Alpine.data('header', () => ({
        // 狀態管理
        topBannerVisible: true,
        topBannerHeight: 0,
        isInitialized: false,
        
        // 快取 DOM 元素
        elements: {
            bannerSpacing: null,
            authSpacing: null,
            calculatorSpacing: []
        },

        // 間距配置
        spacingConfig: {
            banner: { property: 'marginTop', value: '8rem' },
            auth: { property: 'paddingTop', value: '6rem' },
            calculator: { property: 'marginTop', value: '8rem' }
        },

        init() {
            // 檢查 localStorage 中的關閉狀態
            this.topBannerVisible = localStorage.getItem('bannerClosed') !== 'true';
            
            this.$nextTick(() => {
                this.initializeElements();
                this.bindEvents();
                this.updateSpacing();
            });
        },

        // 初始化 DOM 元素快取
        initializeElements() {
            try {
                this.elements.bannerSpacing = document.querySelector('.banner-spacing');
                this.elements.authSpacing = document.querySelector('.auth-spacing');
                this.elements.calculatorSpacing = document.querySelectorAll('.calculator-spacing');
                
                this.topBannerHeight = this.$refs.topBanner?.offsetHeight || 0;
                this.isInitialized = true;
            } catch (error) {
                console.warn('Header initialization error:', error);
            }
        },

        // 綁定事件監聽器
        bindEvents() {
            // 滾動事件
            const handleScroll = () => {
                if (!this.isInitialized) return;
                
                requestAnimationFrame(() => {
                    this.handleScroll();
                });
            };
            
            window.addEventListener('scroll', handleScroll, { passive: true });
            
            // 視窗大小改變事件
            const handleResize = () => {
                if (!this.isInitialized) return;
                
                this.topBannerHeight = this.$refs.topBanner?.offsetHeight || 0;
                this.updateSpacing();
            };
            
            window.addEventListener('resize', handleResize, { passive: true });
            
            // 監聽 banner 可見性變化
            this.$watch('topBannerVisible', (isVisible) => {
                this.updateSpacing();
            });
        },

        // 統一的間距更新函數
        updateSpacing() {
            if (!this.isInitialized) return;

            const isVisible = this.topBannerVisible;
            
            // 更新 banner spacing
            this.updateElementSpacing(this.elements.bannerSpacing, 'banner', isVisible);
            
            // 更新 auth spacing
            this.updateElementSpacing(this.elements.authSpacing, 'auth', isVisible);
            
            // 更新 calculator spacing
            this.elements.calculatorSpacing.forEach(element => {
                this.updateElementSpacing(element, 'calculator', isVisible);
            });
        },

        // 更新單個元素的間距
        updateElementSpacing(element, type, isVisible) {
            if (!element) return;

            const config = this.spacingConfig[type];
            if (!config) return;

            try {
                if (isVisible) {
                    // 重置為原始樣式
                    element.style[config.property] = '';
                } else {
                    // 應用調整後的間距
                    element.style.transition = `${config.property} 0.3s ease-in-out`;
                    element.style[config.property] = config.value;
                }
            } catch (error) {
                console.warn(`Error updating ${type} spacing:`, error);
            }
        },

        // 處理滾動邏輯
        handleScroll() {
            if (!this.isInitialized || !this.topBannerVisible) return;
            
            if (window.scrollY > this.topBannerHeight) {
                this.topBannerVisible = false;
            }
        },

        // 關閉 banner
        closeTopBanner() {
            this.topBannerVisible = false;
            localStorage.setItem('bannerClosed', 'true');
        },

        // 重置 banner（用於測試或管理）
        resetBanner() {
            this.topBannerVisible = true;
            localStorage.removeItem('bannerClosed');
        }
    }));
});
