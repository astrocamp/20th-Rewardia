document.addEventListener('alpine:init', () => {
    Alpine.data('header', () => ({
        topBannerVisible: true,
        topBannerHeight: 0,

        init() {
            this.$nextTick(() => {
                // Get the height of the banner to know when to hide it
                this.topBannerHeight = this.$refs.topBanner?.offsetHeight || 0;
                // Run scroll check on init in case the page is already scrolled
                this.handleScroll();
            });
        },

        handleScroll() {
            // If the banner is currently shown and the user scrolls past its height, hide it.
            // Once hidden, it stays hidden because this condition will no longer be met.
            if (this.topBannerVisible && window.scrollY > this.topBannerHeight) {
                this.topBannerVisible = false;
            }
        },

        closeTopBanner() {
            this.topBannerVisible = false;
        }
    }));
});