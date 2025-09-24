// 常數定義
const CONSTANTS = {
  STORAGE_KEY: 'chatbot_memory',
  MAX_MESSAGE_LENGTH: 500,
  MAX_HISTORY_LENGTH: 50,
  SAVE_THROTTLE_DELAY: 300,
  DUPLICATE_MESSAGE_THRESHOLD: 3000, // 3秒防重複
  TEXTAREA_MAX_HEIGHT: 120,
  CONVERSATION_HISTORY_LENGTH: 6, // 傳遞最近對話數量
  // 外部連結
  CHROME_EXTENSION_URL: 'https://chromewebstore.google.com/detail/rewardia/ahmfkgkefmandfahccfbbpfffnphkakl',
  // 視窗尺寸限制
  MIN_WINDOW_WIDTH: 250,
  MIN_WINDOW_HEIGHT: 350,
  MAX_WINDOW_SCALE: 2, // 最大縮放倍數
  // 視窗預設設定
  DEFAULT_WINDOW: {
    width: 280, // w-70 = 280px
    height: 350,
    right: 48,
    bottom: 40
  }
};

// 文字清理函數 - 移除 HTML 標籤但保留換行
function sanitizeText(text) {
  if (!text || typeof text !== 'string') return '';
  try {
    return text
      .replace(/<br\s*\/?>/gi, '\n')   // 將 <br> 轉換為換行
      .replace(/<\/p>/gi, '\n\n')      // 將 </p> 轉換為雙換行
      .replace(/<[^>]*>/g, '')         // 移除所有其他 HTML 標籤
      .replace(/\n\s*\n\s*\n/g, '\n\n')// 清理多餘的換行
      .trim();                         // 移除首尾空白
  } catch (error) {
    if (window.RewardiaLogger) {
      window.RewardiaLogger.warn('文字清理失敗:', error);
    }
    return text || '';
  }
}

// 輔助函數：創建預設視窗狀態
function createDefaultWindowState() {
  return {
    width: CONSTANTS.DEFAULT_WINDOW.width,
    height: CONSTANTS.DEFAULT_WINDOW.height,
    right: CONSTANTS.DEFAULT_WINDOW.right,
    bottom: CONSTANTS.DEFAULT_WINDOW.bottom
  };
}

// 假存檔（使用 sessionStorage 作為備份）
let chatbotMemory = {
  messages: [],
  isOpen: false,
  windowState: createDefaultWindowState()
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
      if (Array.isArray(data.messages) && typeof data.isOpen === 'boolean') {
        chatbotMemory.messages = data.messages.map(msg => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }));
        chatbotMemory.isOpen = data.isOpen;
        chatbotMemory.windowState = data.windowState || createDefaultWindowState();
      } else {
        if (window.RewardiaLogger) {
          window.RewardiaLogger.warn('聊天記錄資料格式不正確，重置為預設值');
        }
        chatbotMemory.messages = [];
        chatbotMemory.isOpen = false;
        chatbotMemory.windowState = createDefaultWindowState();
      }
    }
  } catch (e) {
    if (window.RewardiaLogger) {
      window.RewardiaLogger.warn('無法載入聊天記錄:', e);
    }
    chatbotMemory.messages = [];
    chatbotMemory.isOpen = false;
    chatbotMemory.windowState = createDefaultWindowState();
  }
}

// 儲存到 sessionStorage
function saveToSession() {
  if (saveThrottleTimer) clearTimeout(saveThrottleTimer);
  saveThrottleTimer = setTimeout(() => {
    try {
      const dataToSave = {
        ...chatbotMemory,
        messages: chatbotMemory.messages.map(msg => ({
          ...msg,
          timestamp: msg.timestamp.toISOString()
        }))
      };
      sessionStorage.setItem(CONSTANTS.STORAGE_KEY, JSON.stringify(dataToSave));
    } catch (e) {
      if (window.RewardiaLogger) {
        window.RewardiaLogger.warn('無法儲存聊天記錄:', e);
      }
    }
  }, CONSTANTS.SAVE_THROTTLE_DELAY);
}

// 立即儲存到 sessionStorage（用於導航時）
function saveToSessionImmediate() {
  try {
    const dataToSave = {
      ...chatbotMemory,
      messages: chatbotMemory.messages.map(msg => ({
        ...msg,
        timestamp: msg.timestamp.toISOString()
      }))
    };
    sessionStorage.setItem(CONSTANTS.STORAGE_KEY, JSON.stringify(dataToSave));
  } catch (e) {
    if (window.RewardiaLogger) {
      window.RewardiaLogger.warn('無法立即儲存聊天記錄:', e);
    }
  }
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
    // 視窗狀態
    windowState: chatbotMemory.windowState,
    isDragging: false,
    isResizing: false,
    dragOffset: { x: 0, y: 0 },
    // IME 輸入法狀態
    isComposing: false,

    // 初始化方法
    init() {
      // 頁面載入時確保滾動到最新位置
      this.$nextTick(() => {
        this.scrollToBottom();
        // 初始化時檢查位置，確保不會跑出畫面外
        this.adjustWindowPosition();
      });
      
      // 監聽視窗大小變化，確保聊天框不會跑出畫面外（儲存引用以便清理）
      this.resizeHandler = () => this.adjustWindowPosition();
      window.addEventListener('resize', this.resizeHandler);
      
      // 使用 MutationObserver 監聽 DOM 變化
      this.setupMutationObserver();
      
      // 定期檢查位置（降低頻率到500ms，減少效能負擔）
      this.positionCheckInterval = setInterval(() => {
        if (this.isOpen) {
          this.adjustWindowPosition();
        }
      }, 500);

      // 註冊銷毀時的清理邏輯
      this.$el.addEventListener('alpine:destroy', () => {
        this.destroy();
      });
    },

    // 儲存到記憶體和 sessionStorage
    saveToMemory() {
      const limitedMessages = this.messages.slice(-CONSTANTS.MAX_HISTORY_LENGTH);
      chatbotMemory.messages = [...limitedMessages];
      chatbotMemory.isOpen = this.isOpen;
      chatbotMemory.windowState = { ...this.windowState };
      saveToSession();
    },

    // 立即儲存到記憶體和 sessionStorage（用於導航時）
    saveToMemoryImmediate() {
      const limitedMessages = this.messages.slice(-CONSTANTS.MAX_HISTORY_LENGTH);
      chatbotMemory.messages = [...limitedMessages];
      chatbotMemory.isOpen = this.isOpen;
      chatbotMemory.windowState = { ...this.windowState };
      saveToSessionImmediate();
    },

    // 清除聊天記錄並關閉對話框
    clearChatHistory() {
      // 清除記憶體中的聊天記錄
      this.messages = [];
      chatbotMemory.messages = [];
      
      // 關閉對話框
      this.isOpen = false;
      chatbotMemory.isOpen = false;
      
      // 清除錯誤訊息
      this.errorMessage = '';
      
      // 重置視窗狀態為預設值
      this.windowState = createDefaultWindowState();
      chatbotMemory.windowState = createDefaultWindowState();
      
      // 立即清除 sessionStorage
      try {
        sessionStorage.removeItem(CONSTANTS.STORAGE_KEY);
      } catch (e) {
        if (window.RewardiaLogger) {
          window.RewardiaLogger.warn('無法清除聊天記錄:', e);
        }
      }
    },

    // 切換聊天視窗顯示狀態
    toggleChat() {
      if (this.isOpen) {
        this.closeChat();
      } else {
        // 如果畫面高度小於最小高度，不開啟對話框
        if (window.innerHeight < CONSTANTS.MIN_WINDOW_HEIGHT) {
          return;
        }
        this.openChat();
      }
    },

    // 開啟聊天視窗
    openChat() {
      // 如果畫面高度小於最小高度，不開啟對話框
      if (window.innerHeight < CONSTANTS.MIN_WINDOW_HEIGHT) {
        return;
      }
      
      this.isOpen = true;
      this.errorMessage = '';
      this.saveToMemory();
      this.focusInput();
      // 確保聊天記錄滾動到最新位置
      this.scrollToBottom();
      // 開啟時檢查位置，確保不會跑出畫面外
      this.$nextTick(() => {
        this.adjustWindowPosition();
      });
    },

    // 關閉聊天視窗
    closeChat() {
      this.isOpen = false;
      this.errorMessage = '';
      // 關閉視窗時重置為預設大小和位置
      this.windowState = createDefaultWindowState();
      this.saveToMemory();
    },

    // 設置 MutationObserver 監聽 DOM 變化
    setupMutationObserver() {
      if (typeof MutationObserver !== 'undefined') {
        this.mutationObserver = new MutationObserver(() => {
          if (this.isOpen) {
            this.$nextTick(() => {
              this.adjustWindowPosition();
            });
          }
        });
        
        // 監聽聊天框容器，而不是整個 document（提升效能）
        this.mutationObserver.observe(this.$el, {
          childList: true,
          subtree: false,  // 不監聽子節點，減少效能負擔
          attributes: true,
          attributeFilter: ['style', 'class']
        });
      }
    },

    // 清理定時器和事件監聽器
    destroy() {
      // 清理 setInterval
      if (this.positionCheckInterval) {
        clearInterval(this.positionCheckInterval);
        this.positionCheckInterval = null;
      }
      
      // 清理 MutationObserver
      if (this.mutationObserver) {
        this.mutationObserver.disconnect();
        this.mutationObserver = null;
      }
      
      // 清理 resize 監聽器
      if (this.resizeHandler) {
        window.removeEventListener('resize', this.resizeHandler);
        this.resizeHandler = null;
      }
    },

    // 發送訊息
    async sendMessage() {
      const message = this.currentMessage.trim();

      if (!message || this.isLoading) return;

      if (message.length > CONSTANTS.MAX_MESSAGE_LENGTH) {
        this.errorMessage = `訊息長度不能超過 ${CONSTANTS.MAX_MESSAGE_LENGTH} 字`;
        return;
      }

      const now = Date.now();
      if (now - lastMessageTime < CONSTANTS.DUPLICATE_MESSAGE_THRESHOLD && lastMessageContent === message) {
        this.errorMessage = '請勿重複發送相同訊息';
        return;
      }

      lastMessageTime = now;
      lastMessageContent = message;
      this.errorMessage = '';

      this.messages.push({
        type: 'user',
        content: message,
        timestamp: new Date()
      });

      this.currentMessage = '';
      this.scrollToBottom();
      this.isLoading = true;

      try {
        const csrfTokenElement = document.querySelector('meta[name="csrf-token"]');
        if (!csrfTokenElement) throw new Error('CSRF token 未找到');
        const csrfToken = csrfTokenElement.getAttribute('content');

        const response = await fetch('/api/chatbot/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken
          },
          body: JSON.stringify({
            message: message,
            conversation_history: this.messages.slice(-CONSTANTS.CONVERSATION_HISTORY_LENGTH),
            current_page: window.location.pathname
          })
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.error || '發生未知錯誤');

        const safeTextContent = sanitizeText(data.response);

        if (safeTextContent.startsWith('NAVIGATE:')) {
          this.handleNavigationCommand(safeTextContent);
          return;
        }

        this.messages.push({
          type: 'ai',
          content: safeTextContent,
          timestamp: new Date()
        });

      } catch (error) {
        if (window.RewardiaLogger) {
          window.RewardiaLogger.error('Chatbot API error:', error);
        }
        this.errorMessage = error.message || '無法連接到 AI 服務，請稍後再試';
        this.messages.push({
          type: 'ai',
          content: '抱歉，我現在無法回應。請稍後再試，或聯絡客服人員協助。',
          timestamp: new Date()
        });
      } finally {
        this.saveToMemory();
        this.isLoading = false;
        this.scrollToBottom();
        this.focusInput();
      }
    },

    // 滾動聊天記錄到底部
    scrollToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.messagesContainer;
        if (container) {
          container.scrollTop = container.scrollHeight;
          // 確保滾動完成，使用 setTimeout 作為備用
          setTimeout(() => {
            if (container) {
              container.scrollTop = container.scrollHeight;
            }
          }, 50);
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
      if (event.key === 'Enter' && !event.shiftKey && !this.isComposing) {
        event.preventDefault();
        this.sendMessage();
      }
    },

    // IME 輸入法事件處理
    handleCompositionStart() { this.isComposing = true; },
    handleCompositionEnd() { setTimeout(() => { this.isComposing = false; }, 0); },

    // 聚焦到輸入框
    focusInput() {
      this.$nextTick(() => {
        if (this.$refs.messageInput) this.$refs.messageInput.focus();
      });
    },

    // 處理導航指令
    handleNavigationCommand(command) {
      const parts = command.split(':');
      if (parts.length < 3) return;
      const target = parts[1];
      const message = parts.slice(2).join(':');
      this.messages.push({ type: 'ai', content: message, timestamp: new Date() });
      this.scrollToBottom(); // 確保UI更新
      
      // 立即儲存聊天記錄（不使用延遲）
      this.saveToMemoryImmediate();
      
      // 使用 setTimeout 確保儲存完成後再執行導航
      setTimeout(() => { this.executeNavigation(target); }, 50);
    },

    // 執行具體的導航動作
    executeNavigation(target) {
      const currentPath = window.location.pathname;
      switch (target) {
        case 'member_area':
          if (currentPath === '/users/member/') {
            this.messages.push({ type: 'ai', content: '這裡就是了喔', timestamp: new Date() });
            this.focusInput();
          } else {
            window.location.href = '/users/member/';
          }
          break;
        case 'home':
          if (currentPath === '/') {
            this.messages.push({ type: 'ai', content: '這裡就是了喔', timestamp: new Date() });
            this.focusInput();
          } else {
            window.location.href = '/';
          }
          break;
        case 'download':
          if (currentPath === '/download/') {
            this.messages.push({ type: 'ai', content: '這裡就是了喔', timestamp: new Date() });
            this.focusInput();
          } else {
            window.location.href = '/download/';
          }
          break;
        case 'calculator':
          if (currentPath === '/calculator/') {
            this.messages.push({ type: 'ai', content: '這裡就是了喔', timestamp: new Date() });
            this.focusInput();
          } else {
            window.location.href = '/calculator/';
          }
          break;
        case 'about':
          if (currentPath === '/faq/') {
            this.messages.push({ type: 'ai', content: '這裡就是了喔', timestamp: new Date() });
            this.focusInput();
          } else {
            window.location.href = '/faq/';
          }
          break;
        case 'privacy':
          if (currentPath === '/privacy/') {
            this.messages.push({ type: 'ai', content: '這裡就是了喔', timestamp: new Date() });
            this.focusInput();
          } else {
            window.location.href = '/privacy/';
          }
          break;
        case 'tos':
          if (currentPath === '/tos/') {
            this.messages.push({ type: 'ai', content: '這裡就是了喔', timestamp: new Date() });
            this.focusInput();
          } else {
            window.location.href = '/tos/';
          }
          break;
        case 'add_card':
          if (currentPath === '/users/cards/new/') {
            this.messages.push({ type: 'ai', content: '好的，幫你打開相機', timestamp: new Date() });
            window.dispatchEvent(new CustomEvent('open-camera'));
            this.focusInput();
          } else {
            window.location.href = '/users/cards/new/';
          }
          break;
        case 'login':
          window.location.href = '/sessions/login/';
          break;
        case 'register':
          window.location.href = '/users/register/';
          break;
        case 'chrome_extension':
          // 延遲2秒後開啟Chrome Web Store下載頁面
          setTimeout(() => {
            window.open(CONSTANTS.CHROME_EXTENSION_URL, '_blank');
          }, 1000);
          break;
        case 'logout':
          this.performLogout();
          break;
        default:
          if (window.RewardiaLogger) {
            window.RewardiaLogger.warn('未知的導航目標:', target);
          }
      }
    },

    // 執行登出
    performLogout() {
      // 登出前先清除聊天記錄並關閉對話框
      this.clearChatHistory();
      
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = '/accounts/logout/';

      const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
      if (csrfToken) {
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfToken.value;
        form.appendChild(csrfInput);
      }

      const nextInput = document.createElement('input');
      nextInput.type = 'hidden';
      nextInput.name = 'next';
      nextInput.value = '/';
      form.appendChild(nextInput);

      document.body.appendChild(form);
      form.submit();
    },

    // 計算視窗位置（共用函式）
    getWindowPosition() {
      return {
        left: window.innerWidth - this.windowState.right - this.windowState.width,
        top:  window.innerHeight - this.windowState.bottom - this.windowState.height
      };
    },

    // === 拖拽功能（Pointer 版）===
    startDrag(event) {
      this.isDragging = true;
      try { event.target.setPointerCapture?.(event.pointerId); } catch {}
      const windowPos = this.getWindowPosition();
      this.dragOffset.x = event.clientX - windowPos.left;
      this.dragOffset.y = event.clientY - windowPos.top;
      event.preventDefault();
    },

    handleDrag(event) {
      if (!this.isDragging) return;

      const newLeft = event.clientX - this.dragOffset.x;
      const newTop  = event.clientY - this.dragOffset.y;
      const newRight  = window.innerWidth  - newLeft - this.windowState.width;
      const newBottom = window.innerHeight - newTop  - this.windowState.height;

      this.windowState.right  = Math.max(0, Math.min(window.innerWidth  - this.windowState.width,  newRight));
      this.windowState.bottom = Math.max(0, Math.min(window.innerHeight - this.windowState.height, newBottom));
    },

    stopDrag() {
      if (this.isDragging) {
        this.isDragging = false;
        // 拖拽結束後檢查位置
        this.adjustWindowPosition();
        this.saveToMemory();
      }
    },

    // === 調整大小（Pointer 版 + 可放大也可縮小）===
    startResize(event) {
      this.isResizing = true;
      try { event.target.setPointerCapture?.(event.pointerId); } catch {}
      this.initialWidth    = this.windowState.width;
      this.initialHeight   = this.windowState.height;
      this.initialDiagonal = Math.hypot(this.initialWidth, this.initialHeight);
      event.preventDefault();
      event.stopPropagation(); // 防止同時觸發拖拽
    },

    handleResize(event) {
      if (!this.isResizing) return;

      const windowPos = this.getWindowPosition();
      const mouseX = event.clientX - windowPos.left;
      const mouseY = event.clientY - windowPos.top;
      const mouseDistance = Math.hypot(mouseX, mouseY);

      // 相對初始對角線的等比縮放（基於初始尺寸）
      let newWidth  = (this.initialWidth  * mouseDistance) / this.initialDiagonal;
      let newHeight = (this.initialHeight * mouseDistance) / this.initialDiagonal;

      // 最小尺寸限制
      newWidth  = Math.max(CONSTANTS.MIN_WINDOW_WIDTH,  newWidth);
      newHeight = Math.max(CONSTANTS.MIN_WINDOW_HEIGHT, newHeight);

      // 最大尺寸限制（基於 DEFAULT_WINDOW * MAX_WINDOW_SCALE）
      const maxAllowedWidth  = CONSTANTS.DEFAULT_WINDOW.width  * CONSTANTS.MAX_WINDOW_SCALE;
      const maxAllowedHeight = CONSTANTS.DEFAULT_WINDOW.height * CONSTANTS.MAX_WINDOW_SCALE;
      newWidth  = Math.min(newWidth,  maxAllowedWidth);
      newHeight = Math.min(newHeight, maxAllowedHeight);

      // 視窗邊界限制：不可超出可視區域
      const maxWidthByViewport  = window.innerWidth  - windowPos.left;
      const maxHeightByViewport = window.innerHeight - windowPos.top;
      newWidth  = Math.min(newWidth,  maxWidthByViewport);
      newHeight = Math.min(newHeight, maxHeightByViewport);

      this.windowState.width  = newWidth;
      this.windowState.height = newHeight;
    },

    stopResize() {
      if (this.isResizing) {
        this.isResizing = false;
        // 調整大小後立即檢查位置
        this.adjustWindowPosition();
        this.saveToMemory();
      }
    },

    // 調整視窗位置，確保不會跑出畫面外
    adjustWindowPosition() {
      if (!this.isOpen) return; // 如果聊天框未開啟，不執行調整
      
      // 如果畫面高度小於最小高度，關閉對話框
      if (window.innerHeight < CONSTANTS.MIN_WINDOW_HEIGHT) {
        this.closeChat();
        return;
      }
      
      // 計算最大允許的寬度和高度（留出更多邊距）
      const maxWidth = window.innerWidth - 32; // 左右各留 16px
      const maxHeight = window.innerHeight - 32; // 上下各留 16px
      
      // 記錄調整前的狀態
      const oldWidth = this.windowState.width;
      const oldHeight = this.windowState.height;
      const oldRight = this.windowState.right;
      const oldBottom = this.windowState.bottom;
      
      // 強制限制寬度
      this.windowState.width = Math.max(CONSTANTS.MIN_WINDOW_WIDTH, Math.min(this.windowState.width, maxWidth));
      
      // 強制限制高度
      this.windowState.height = Math.max(CONSTANTS.MIN_WINDOW_HEIGHT, Math.min(this.windowState.height, maxHeight));
      
      // 計算邊界
      const maxLeft = window.innerWidth - this.windowState.width;
      const maxTop = window.innerHeight - this.windowState.height;
      
      // 確保不會超出邊界
      this.windowState.right = Math.max(0, Math.min(maxLeft, this.windowState.right));
      this.windowState.bottom = Math.max(0, Math.min(maxTop, this.windowState.bottom));
      
      // 如果有調整，儲存狀態
      if (oldWidth !== this.windowState.width || oldHeight !== this.windowState.height || 
          oldRight !== this.windowState.right || oldBottom !== this.windowState.bottom) {
        this.saveToMemory();
      }
    },

    // 取得視窗樣式
    get windowStyle() {
      // 每次計算樣式時都檢查位置
      if (this.isOpen) {
        this.adjustWindowPosition();
      }
      
      const windowPos = this.getWindowPosition();
      return {
        width: `${this.windowState.width}px`,
        height: `${this.windowState.height}px`,
        '--chatbot-left': `${Math.max(0, windowPos.left)}px`,
        '--chatbot-top': `${Math.max(0, windowPos.top)}px`,
        '--chatbot-width': `${this.windowState.width}px`,
        '--chatbot-height': `${this.windowState.height}px`
      };
    }
  };
}
