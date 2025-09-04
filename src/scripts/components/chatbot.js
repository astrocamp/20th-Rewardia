/**
 * Chatbot Alpine.js 組件
 * 處理 AI 聊天機器人的互動邏輯
 */
export default function chatbot() {
  return {
    // 狀態管理
    isOpen: false,
    isLoading: false,
    currentMessage: '',
    messages: [],
    errorMessage: '',

    // 初始化
    init() {
      // 監聽視窗大小變化，在小螢幕模式下自動關閉聊天視窗
      window.addEventListener('resize', () => {
        if (window.innerWidth <= 768 && this.isOpen) {
          this.closeChat();
        }
      });
    },

    // 檢查是否為小螢幕模式
    isSmallScreen() {
      return window.innerWidth <= 768;
    },

    // 切換聊天視窗顯示狀態
    toggleChat() {
      // 小螢幕模式下不允許開啟聊天視窗
      if (this.isSmallScreen()) {
        return;
      }
      
      if (this.isOpen) {
        this.closeChat();
      } else {
        this.openChat();
      }
    },

    // 開啟聊天視窗
    openChat() {
      this.isOpen = true;
      this.errorMessage = '';
      this.focusInput();
    },

    // 關閉聊天視窗
    closeChat() {
      this.isOpen = false;
      this.errorMessage = '';
    },

    // 發送訊息
    async sendMessage() {
      const message = this.currentMessage.trim();
      
      if (!message || this.isLoading) {
        return;
      }

      // 清除錯誤訊息
      this.errorMessage = '';

      // 添加用戶訊息到聊天記錄
      this.messages.push({
        type: 'user',
        content: message,
        timestamp: new Date()
      });

      // 清空輸入框
      this.currentMessage = '';
      
      // 滾動到底部
      this.scrollToBottom();

      // 設置載入狀態
      this.isLoading = true;

      try {
        // 調用 Django API
        const response = await fetch('/api/chatbot/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
          },
          body: JSON.stringify({
            message: message
          })
        });

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.error || '發生未知錯誤');
        }

        // 添加 AI 回應到聊天記錄
        this.messages.push({
          type: 'ai',
          content: data.response,
          timestamp: new Date()
        });

      } catch (error) {
        console.error('Chatbot API error:', error);
        
        // 顯示錯誤訊息
        this.errorMessage = error.message || '無法連接到 AI 服務，請稍後再試';
        
        // 添加錯誤訊息到聊天記錄
        this.messages.push({
          type: 'ai',
          content: '抱歉，我現在無法回應。請稍後再試，或聯絡客服人員協助。',
          timestamp: new Date()
        });
      } finally {
        // 取消載入狀態
        this.isLoading = false;
        
        // 滾動到底部
        this.scrollToBottom();
        
        // 重新聚焦到輸入框
        this.focusInput();
      }
    },

    // 滾動聊天記錄到底部
    scrollToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.messagesContainer;
        if (container) {
          container.scrollTop = container.scrollHeight;
        }
      });
    },


    // 自動調整 textarea 高度
    autoResize(event) {
      const textarea = event.target;
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    },

    // 處理鍵盤事件
    handleKeyDown(event) {
      if (event.key === 'Enter' && !event.shiftKey) {
        // Enter 鍵發送訊息
        event.preventDefault();
        this.sendMessage();
      }
      // Shift+Enter 允許換行（預設行為）
    },

    // 聚焦到輸入框
    focusInput() {
      this.$nextTick(() => {
        if (this.$refs.messageInput) {
          this.$refs.messageInput.focus();
        }
      });
    }
  }
}
