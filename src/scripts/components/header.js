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
                const authElement = document.querySelector('.auth-spacing');
                const calculatorElements = document.querySelectorAll('.calculator-spacing');
                
                if (targetElement) {
                    if (isVisible) {
                        // This part of the logic won't be triggered in the current flow,
                        // but it is good practice to handle reverting the style.
                        targetElement.style.marginTop = '';
                    } else {
                        // Apply the new, smaller margin when banner is hidden
                        targetElement.style.transition = 'margin-top 0.3s ease-in-out';
                        targetElement.style.marginTop = '8rem';
                    }
                }

                if (authElement) {
                    if (isVisible) {
                        // Reset to original padding when banner is visible
                        authElement.style.paddingTop = '';
                    } else {
                        // Apply smaller padding when banner is hidden
                        authElement.style.transition = 'padding-top 0.3s ease-in-out';
                        authElement.style.paddingTop = '6rem'; // pt-40 = 160px, adjusted for smaller header
                    }
                }

                // Handle calculator pages
                calculatorElements.forEach(element => {
                    if (isVisible) {
                        // Reset to original margin when banner is visible
                        element.style.marginTop = '';
                    } else {
                        // Apply smaller margin when banner is hidden
                        element.style.transition = 'margin-top 0.3s ease-in-out';
                        element.style.marginTop = '8rem'; // mt-50 = 200px, adjusted for smaller header
                    }
                });
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
