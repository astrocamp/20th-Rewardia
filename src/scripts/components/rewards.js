/**
 * Rewards 管理頁面的 JavaScript 功能
 * 包含表格互動、載入效果、批量操作等功能
 */

// 表格行互動功能 - 點擊選中、懸停效果
function initRewardsTableInteraction() {
    const rewardsTable = document.querySelector('tr[data-extracted-sentence]');
    if (!rewardsTable) {
        return;
    }

    // 點擊行的選中效果
    document.addEventListener('click', function(e) {
        const row = e.target.closest('tr[data-extracted-sentence]');
        if (row) {
            // 移除所有行的選中效果
            document.querySelectorAll('tr[data-extracted-sentence]').forEach(tr => {
                tr.classList.remove('bg-blue-100', 'border-l-4', 'border-blue-500', 'bg-gray-100');
            });

            // 加入當前行的選中效果
            row.classList.add('bg-blue-100', 'border-l-4', 'border-blue-500');

            // 顯示回饋描述
            const extractedSentence = row.getAttribute('data-extracted-sentence');
            const displayElement = document.getElementById('description-display');
            if (displayElement && extractedSentence) {
                displayElement.textContent = extractedSentence;
            }
        }
    });

    // 滑鼠懸停效果
    document.addEventListener('mouseover', function(e) {
        const row = e.target.closest('tr[data-extracted-sentence]');
        if (row && !row.classList.contains('bg-blue-100')) {
            row.classList.add('bg-gray-100');
        }
    });

    // 滑鼠移出效果
    document.addEventListener('mouseout', function(e) {
        const row = e.target.closest('tr[data-extracted-sentence]');
        if (row && !row.classList.contains('bg-blue-100')) {
            row.classList.remove('bg-gray-100');
        }
    });
}

// 載入中效果控制
function initLoadingOverlay() {
    const loadingOverlay = document.getElementById('loading-overlay');

    // 初始隱藏 Loading
    if (loadingOverlay) {
        loadingOverlay.style.display = 'none';
    }

    // 為所有狀態按鈕添加點擊事件
    const statusButtons = document.querySelectorAll('a[href*="status="]');
    statusButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            // 點擊時立即顯示 Loading
            if (loadingOverlay) {
                loadingOverlay.style.display = 'flex';
                loadingOverlay.classList.remove('loading-fade-out');
            }
        });
    });

    // 為分頁按鈕添加點擊事件
    const pageButtons = document.querySelectorAll('a[href*="page="]');
    pageButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            // 點擊時立即顯示 Loading
            if (loadingOverlay) {
                loadingOverlay.style.display = 'flex';
                loadingOverlay.classList.remove('loading-fade-out');
            }
        });
    });

    // 等待頁面完全載入後隱藏 Loading
    window.addEventListener('load', function() {
        if (loadingOverlay) {
            // 添加淡出動畫
            loadingOverlay.classList.add('loading-fade-out');

            // 動畫完成後移除元素
            setTimeout(() => {
                loadingOverlay.style.display = 'none';
            }, 500);
        }
    });
}

// 批量操作載入效果
function showLoadingAndSubmit(button, url, confirmMessage) {
    if (confirm(confirmMessage)) {
        // 顯示載入中
        const loadingOverlay = document.getElementById('loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = 'flex';
            loadingOverlay.classList.remove('loading-fade-out');
        }

        // 建立並提交表單
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = url;

        // 加入 CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]') ||
                         document.querySelector('meta[name=csrf-token]');
        if (csrfToken) {
            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrfmiddlewaretoken';
            csrfInput.value = csrfToken.value || csrfToken.content;
            form.appendChild(csrfInput);
        }

        document.body.appendChild(form);
        form.submit();
    }
}

// 初始化所有功能
function initRewardsPage() {
    initRewardsTableInteraction();
    initLoadingOverlay();
}

// 頁面載入完成時初始化
document.addEventListener('DOMContentLoaded', initRewardsPage);

// 將批量操作函數暴露到全域，供 HTML onclick 使用
window.showLoadingAndSubmit = showLoadingAndSubmit;

export default {
    initRewardsPage,
    initRewardsTableInteraction,
    initLoadingOverlay,
    showLoadingAndSubmit
};