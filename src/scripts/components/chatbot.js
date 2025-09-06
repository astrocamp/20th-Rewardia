
// 文字清理函數 - 移除 HTML 標籤但保留換行
function sanitizeText(text) {
  return text
    .replace(/<br\s*\/?>/gi, '\n') // 將 <br> 轉換為換行
    .replace(/<\/p>/gi, '\n\n') // 將 </p> 轉換為雙換行
    .replace(/<[^>]*>/g, '') // 移除所有其他 HTML 標籤
    .replace(/\n\s*\n\s*\n/g, '\n\n') // 清理多餘的換行
    .trim(); // 移除首尾空白
}

// 不再需要 marked，直接使用純文字

// 文字清理函數 - 移除 HTML 標籤但保留換行
function sanitizeText(text) {
  return text
    .replace(/<br\s*\/?>/gi, '\n') // 將 <br> 轉換為換行
    .replace(/<\/p>/gi, '\n\n') // 將 </p> 轉換為雙換行
    .replace(/<[^>]*>/g, '') // 移除所有其他 HTML 標籤
    .replace(/\n\s*\n\s*\n/g, '\n\n') // 清理多餘的換行
    .trim(); // 移除首尾空白
}

// 常數定義
const CONSTANTS = {
  STORAGE_KEY: 'chatbot_memory',
  MAX_MESSAGE_LENGTH: 500,
  MAX_HISTORY_LENGTH: 50,
  SAVE_THROTTLE_DELAY: 300,
  DUPLICATE_MESSAGE_THRESHOLD: 3000, // 3秒防重複
  TEXTAREA_MAX_HEIGHT: 120
};

// 假存檔（使用 sessionStorage 作為備份）
let chatbotMemory = {
  messages: [],
  isOpen: false
};

// 節流控制
let saveThrottleTimer = null;
let lastMessageTime = 0;
let lastMessageContent = '';

// 從 sessionStorage 載入（頁面跳轉時保留）
function loadFromSession() {
  try {
    const saved = sessionStorage.getItem(CONSTANTS.STORAGE_KEY);
    if (saved) {
      const data = JSON.parse(saved);
      // 驗證資料格式
      if (Array.isArray(data.messages) && typeof data.isOpen === 'boolean') {
        // 轉換 ISO 字串回 Date 物件
        chatbotMemory.messages = data.messages.map(msg => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }));
        chatbotMemory.isOpen = data.isOpen;
      } else {
        console.warn('聊天記錄資料格式不正確，重置為預設值');
        chatbotMemory.messages = [];
        chatbotMemory.isOpen = false;
      }
    }
  } catch (e) {
    console.warn('無法載入聊天記錄:', e);
    chatbotMemory.messages = [];
    chatbotMemory.isOpen = false;
  }
}

// 儲存到 sessionStorage（節流版本）
function saveToSession() {
  // 清除之前的節流計時器
  if (saveThrottleTimer) {
    clearTimeout(saveThrottleTimer);
  }
  
  // 設定新的節流計時器
  saveThrottleTimer = setTimeout(() => {
    try {
      // 轉換 Date 物件為 ISO 字串
      const dataToSave = {
        ...chatbotMemory,
        messages: chatbotMemory.messages.map(msg => ({
          ...msg,
          timestamp: msg.timestamp.toISOString()
        }))
      };
      sessionStorage.setItem(CONSTANTS.STORAGE_KEY, JSON.stringify(dataToSave));
    } catch (e) {
      console.warn('無法儲存聊天記錄:', e);
    }
  }, CONSTANTS.SAVE_THROTTLE_DELAY);
}

// 頁面載入時立即載入
loadFromSession();

export default function chatbot() {
  return {
    // 狀態管理 - 從記憶體載入
    isOpen: chatbotMemory.isOpen,
    isLoading: false,
    currentMessage: '',
    messages: chatbotMemory.messages,
    errorMessage: '',

    // 初始化
    init() {
      // 不需要額外的監聽器，讓 CSS 完全控制小螢幕的顯示
    },

    // 儲存到記憶體和 sessionStorage
    saveToMemory() {
      // 限制歷史長度，避免記憶體膨脹
      const limitedMessages = this.messages.slice(-CONSTANTS.MAX_HISTORY_LENGTH);
      chatbotMemory.messages = [...limitedMessages];
      chatbotMemory.isOpen = this.isOpen;
      saveToSession(); // 同時儲存到 sessionStorage
    },

    // 切換聊天視窗顯示狀態
    toggleChat() {
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
      this.saveToMemory();
      this.focusInput();
    },

    // 關閉聊天視窗
    closeChat() {
      this.isOpen = false;
      this.errorMessage = '';
      this.saveToMemory();
    },

    // 發送訊息
    async sendMessage() {
      const message = this.currentMessage.trim();
      
      // 輸入驗證
      if (!message || this.isLoading) {
        return;
      }
      
      if (message.length > CONSTANTS.MAX_MESSAGE_LENGTH) {
        this.errorMessage = `訊息長度不能超過 ${CONSTANTS.MAX_MESSAGE_LENGTH} 字`;
        return;
      }

      // 重複訊息防抖
      const now = Date.now();
      if (now - lastMessageTime < CONSTANTS.DUPLICATE_MESSAGE_THRESHOLD && lastMessageContent === message) {
        this.errorMessage = '請勿重複發送相同訊息';
        return;
      }
      
      // 更新防抖記錄
      lastMessageTime = now;
      lastMessageContent = message;

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
        // 讀取 CSRF token
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

        // 調用 Django API
        const response = await fetch('/api/chatbot/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken
          },
          body: JSON.stringify({
            message: message,
            conversation_history: this.messages.slice(-6) // 傳遞最近6條對話
          })
        });

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.error || '發生未知錯誤');
        }

        // 移除所有 HTML 標籤，只保留純文字
        const safeTextContent = sanitizeText(data.response);

        // 添加 AI 回應到聊天記錄
        this.messages.push({
          type: 'ai',
          content: safeTextContent,
          timestamp: new Date()
        });

      } catch (error) {
        console.error('Chatbot API error:', error);
        
        // 統一錯誤處理
        this.errorMessage = error.message || '無法連接到 AI 服務，請稍後再試';
        
        // 添加錯誤訊息到聊天記錄
        this.messages.push({
          type: 'ai',
          content: '抱歉，我現在無法回應。請稍後再試，或聯絡客服人員協助。',
          timestamp: new Date()
        });
      } finally {
        // 統一儲存到記憶體（無論成功或失敗）
        this.saveToMemory();
        
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
      textarea.style.height = Math.min(textarea.scrollHeight, CONSTANTS.TEXTAREA_MAX_HEIGHT) + 'px';
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