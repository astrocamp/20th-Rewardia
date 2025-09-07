document.addEventListener('alpine:init', () => {
    Alpine.data('header', () => ({
        topBannerVisible: true,
        topBannerHeight: 0,

        init() {
            this.$nextTick(() => {
                this.topBannerHeight = this.$refs.topBanner?.offsetHeight || 0;
                this.handleScroll();
            });

            // Watch for the banner visibility to change
            this.$watch('topBannerVisible', (isVisible) => {
                const targetElement = document.querySelector('.banner-spacing');
                if (!targetElement) return;

                if (isVisible) {
                    // This part of the logic won't be triggered in the current flow,
                    // but it is good practice to handle reverting the style.
                    targetElement.style.marginTop = '';
                } else {
                    // Apply the new, smaller margin when banner is hidden
                    targetElement.style.transition = 'margin-top 0.3s ease-in-out';
                    targetElement.style.marginTop = '130px';
                }
            });
        },

        handleScroll() {
            // This function only ever sets topBannerVisible to false, it never reverts.
            if (this.topBannerVisible && window.scrollY > this.topBannerHeight) {
                this.topBannerVisible = false;
            }
        },

        closeTopBanner() {
            this.topBannerVisible = false;
        }
    }));
});
