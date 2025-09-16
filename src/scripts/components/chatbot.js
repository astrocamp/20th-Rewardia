// 常數定義
const CONSTANTS = {
  STORAGE_KEY: 'chatbot_memory',
  MAX_MESSAGE_LENGTH: 500,
  MAX_HISTORY_LENGTH: 50,
  SAVE_THROTTLE_DELAY: 300,
  DUPLICATE_MESSAGE_THRESHOLD: 3000, // 3秒防重複
  TEXTAREA_MAX_HEIGHT: 120,
  CONVERSATION_HISTORY_LENGTH: 6, // 傳遞最近對話數量
  // 視窗尺寸限制
  MIN_WINDOW_WIDTH: 250,
  MIN_WINDOW_HEIGHT: 300,
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
  if (!text || typeof text !== 'string') {
    return '';
  }
  
  try {
    return text
      .replace(/<br\s*\/?>/gi, '\n') // 將 <br> 轉換為換行
      .replace(/<\/p>/gi, '\n\n') // 將 </p> 轉換為雙換行
      .replace(/<[^>]*>/g, '') // 移除所有其他 HTML 標籤
      .replace(/\n\s*\n\s*\n/g, '\n\n') // 清理多餘的換行
      .trim(); // 移除首尾空白
  } catch (error) {
    console.warn('文字清理失敗:', error);
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
      // 驗證資料格式
      if (Array.isArray(data.messages) && typeof data.isOpen === 'boolean') {
        // 轉換 ISO 字串回 Date 物件
        chatbotMemory.messages = data.messages.map(msg => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }));
        chatbotMemory.isOpen = data.isOpen;
        // 載入視窗狀態，如果沒有則使用預設值
        chatbotMemory.windowState = data.windowState || createDefaultWindowState();
      } else {
        console.warn('聊天記錄資料格式不正確，重置為預設值');
        chatbotMemory.messages = [];
        chatbotMemory.isOpen = false;
        chatbotMemory.windowState = createDefaultWindowState();
      }
    }
  } catch (e) {
    console.warn('無法載入聊天記錄:', e);
    chatbotMemory.messages = [];
    chatbotMemory.isOpen = false;
    chatbotMemory.windowState = createDefaultWindowState();
  }
}

// 儲存到 sessionStorage
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
    // 視窗狀態
    windowState: chatbotMemory.windowState,
    isDragging: false,
    isResizing: false,
    dragOffset: { x: 0, y: 0 },
    // IME 輸入法狀態
    isComposing: false,

    // 儲存到記憶體和 sessionStorage
    saveToMemory() {
      // 限制歷史長度，避免記憶體膨脹
      const limitedMessages = this.messages.slice(-CONSTANTS.MAX_HISTORY_LENGTH);
      chatbotMemory.messages = [...limitedMessages];
      chatbotMemory.isOpen = this.isOpen;
      chatbotMemory.windowState = { ...this.windowState };
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
      // 關閉視窗時重置為預設大小和位置
      this.windowState = createDefaultWindowState();
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
        const csrfTokenElement = document.querySelector('meta[name="csrf-token"]');
        if (!csrfTokenElement) {
          throw new Error('CSRF token 未找到');
        }
        const csrfToken = csrfTokenElement.getAttribute('content');

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
            conversation_history: this.messages.slice(-6), // 傳遞最近6條對話
            current_page: window.location.pathname // 傳遞當前頁面路徑
          })
        });

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.error || '發生未知錯誤');
        }

        // 移除所有 HTML 標籤，只保留純文字
        const safeTextContent = sanitizeText(data.response);

        // 檢查是否為導航指令
        if (safeTextContent.startsWith('NAVIGATE:')) {
          this.handleNavigationCommand(safeTextContent);
          return; // 不添加到聊天記錄，直接執行導航
        }

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
      if (event.key === 'Enter' && !event.shiftKey && !this.isComposing) {
        // Enter 鍵發送訊息（只有在非輸入法組合狀態下）
        event.preventDefault();
        this.sendMessage();
      }
      // Shift+Enter 允許換行（預設行為）
    },

    // IME 輸入法事件處理
    handleCompositionStart(event) {
      this.isComposing = true;
    },

    handleCompositionEnd(event) {
      // 在某些瀏覽器中，compositionend 事件可能在 keydown 之後觸發
      // 使用 setTimeout 確保狀態正確更新
      setTimeout(() => {
        this.isComposing = false;
      }, 0);
    },

    // 聚焦到輸入框
    focusInput() {
      this.$nextTick(() => {
        if (this.$refs.messageInput) {
          this.$refs.messageInput.focus();
        }
      });
    },

    // 處理導航指令
    handleNavigationCommand(command) {
      // 解析導航指令格式：NAVIGATE:target:message
      const parts = command.split(':');
      if (parts.length < 3) return;
      
      const target = parts[1];
      const message = parts.slice(2).join(':'); // 處理訊息中可能包含冒號的情況
      
      // 先顯示回應訊息
      this.messages.push({
        type: 'ai',
        content: message,
        timestamp: new Date()
      });
      
      // 執行導航
      this.$nextTick(() => {
        this.executeNavigation(target);
      });
    },

    // 執行具體的導航動作
    executeNavigation(target) {
      const currentPath = window.location.pathname;
      
      switch (target) {
        case 'member_area':
          if (currentPath === '/users/member/') {
            // 已在會員專區
            this.messages.push({
              type: 'ai',
              content: '這裡就是了喔',
              timestamp: new Date()
            });
            this.focusInput();
          } else {
            // 導航到會員專區
            window.location.href = '/users/member/';
          }
          break;
          
        case 'home':
          if (currentPath === '/') {
            // 已在首頁
            this.messages.push({
              type: 'ai',
              content: '這裡就是了喔',
              timestamp: new Date()
            });
            this.focusInput();
          } else {
            // 導航到首頁
            window.location.href = '/';
          }
          break;
          
        case 'download':
          if (currentPath === '/download/') {
            // 已在下載專區
            this.messages.push({
              type: 'ai',
              content: '這裡就是了喔',
              timestamp: new Date()
            });
            this.focusInput();
          } else {
            // 導航到下載專區
            window.location.href = '/download/';
          }
          break;
          
        case 'calculator':
          if (currentPath === '/calculator/') {
            // 已在優惠試算
            this.messages.push({
              type: 'ai',
              content: '這裡就是了喔',
              timestamp: new Date()
            });
            this.focusInput();
          } else {
            // 導航到優惠試算
            window.location.href = '/calculator/';
          }
          break;
          
        case 'about':
          if (currentPath === '/faq/') {
            // 已在關於功能
            this.messages.push({
              type: 'ai',
              content: '這裡就是了喔',
              timestamp: new Date()
            });
            this.focusInput();
          } else {
            // 導航到關於功能
            window.location.href = '/faq/';
          }
          break;
          
        case 'add_card':
          if (currentPath === '/users/cards/new/') {
            // 已在新增卡片頁面，開啟相機
            this.messages.push({
              type: 'ai',
              content: '好的，幫你打開相機',
              timestamp: new Date()
            });
            // 觸發相機開啟事件
            window.dispatchEvent(new CustomEvent('open-camera'));
            this.focusInput();
          } else {
            // 導航到新增卡片頁面
            window.location.href = '/users/cards/new/';
          }
          break;
          
        case 'login':
          // 導航到登入頁面
          window.location.href = '/sessions/login/';
          break;
          
        case 'register':
          // 導航到註冊頁面
          window.location.href = '/users/register/';
          break;
          
        case 'logout':
          // 執行登出並導回首頁
          this.performLogout();
          break;
          
        default:
          console.warn('未知的導航目標:', target);
      }
    },

    // 執行登出
    performLogout() {
      // 創建一個隱藏的 form 來提交登出請求
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = '/accounts/logout/';
      
      // 添加 CSRF token
      const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
      if (csrfToken) {
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfToken.value;
        form.appendChild(csrfInput);
      }
      
      // 添加 next 參數
      const nextInput = document.createElement('input');
      nextInput.type = 'hidden';
      nextInput.name = 'next';
      nextInput.value = '/';
      form.appendChild(nextInput);
      
      // 提交表單
      document.body.appendChild(form);
      form.submit();
    },

    // 計算視窗位置（共用函式）
    getWindowPosition() {
      return {
        left: window.innerWidth - this.windowState.right - this.windowState.width,
        top: window.innerHeight - this.windowState.bottom - this.windowState.height
      };
    },

    // === 拖拽功能 ===
    startDrag(event) {
      this.isDragging = true;
      // 記錄起始位置偏移
      const windowPos = this.getWindowPosition();
      this.dragOffset.x = event.clientX - windowPos.left;
      this.dragOffset.y = event.clientY - windowPos.top;
      event.preventDefault();
    },

    handleDrag(event) {
      if (!this.isDragging) return;
      
      // 計算新位置（從右下角定位）
      const newLeft = event.clientX - this.dragOffset.x;
      const newTop = event.clientY - this.dragOffset.y;
      const newRight = window.innerWidth - newLeft - this.windowState.width;
      const newBottom = window.innerHeight - newTop - this.windowState.height;
      
      // 限制在視窗範圍內
      this.windowState.right = Math.max(0, Math.min(window.innerWidth - this.windowState.width, newRight));
      this.windowState.bottom = Math.max(0, Math.min(window.innerHeight - this.windowState.height, newBottom));
    },

    stopDrag() {
      if (this.isDragging) {
        this.isDragging = false;
        this.saveToMemory();
      }
    },

    // === 調整大小功能 ===
    startResize(event) {
      this.isResizing = true;
      // 記錄初始尺寸和位置
      this.initialWidth = this.windowState.width;
      this.initialHeight = this.windowState.height;
      this.initialDiagonal = Math.sqrt(this.initialWidth ** 2 + this.initialHeight ** 2);
      event.preventDefault();
      event.stopPropagation(); // 防止觸發拖拽
    },

    handleResize(event) {
      if (!this.isResizing) return;
      
      // 計算視窗左上角位置（基於當前的 right/bottom 值）
      const windowPos = this.getWindowPosition();
      
      // 計算滑鼠相對於視窗左上角的距離
      const mouseX = event.clientX - windowPos.left;
      const mouseY = event.clientY - windowPos.top;
      
      // 計算滑鼠距離（相對於視窗左上角）
      const mouseDistance = Math.sqrt(mouseX ** 2 + mouseY ** 2);
      
      // 計算縮放比例：相對於初始對角線距離
      const scaleFactor = mouseDistance / this.initialDiagonal;
      
      // 計算新的等比例大小（基於初始尺寸）
      const newWidth = this.initialWidth * scaleFactor;
      const newHeight = this.initialHeight * scaleFactor;
      
      // 設定最大尺寸限制（預設大小的兩倍）
      const maxAllowedWidth = CONSTANTS.DEFAULT_WINDOW.width * CONSTANTS.MAX_WINDOW_SCALE;
      const maxAllowedHeight = CONSTANTS.DEFAULT_WINDOW.height * CONSTANTS.MAX_WINDOW_SCALE;
      
      // 計算可用空間（考慮螢幕邊界和尺寸限制）
      const maxWidth = Math.min(
        window.innerWidth - windowPos.left,  // 螢幕右邊界限制
        maxAllowedWidth                      // 尺寸限制
      );
      const maxHeight = Math.min(
        window.innerHeight - windowPos.top,  // 螢幕下邊界限制
        maxAllowedHeight                     // 尺寸限制
      );
      
      // 等比例縮放：確保寬度和高度都符合限制，且不超過 1 倍
      const scaleX = maxWidth / newWidth;
      const scaleY = maxHeight / newHeight;
      const finalScale = Math.min(1, scaleX, scaleY); // 限制不超過 1 倍，允許縮小
      
      // 即時更新視窗大小（等比例縮放）
      this.windowState.width = Math.max(CONSTANTS.MIN_WINDOW_WIDTH, newWidth * finalScale);
      this.windowState.height = Math.max(CONSTANTS.MIN_WINDOW_HEIGHT, newHeight * finalScale);
    },

    stopResize() {
      this.isResizing = false;
      // 調整大小結束時保存
      this.saveToMemory();
    },

    // 取得視窗樣式
    get windowStyle() {
      // 將 right/bottom 轉換為 left/top 以便直觀調整大小
      const windowPos = this.getWindowPosition();
      
      return {
        width: `${this.windowState.width}px`,
        height: `${this.windowState.height}px`,
        left: `${Math.max(0, windowPos.left)}px`,
        top: `${Math.max(0, windowPos.top)}px`
      };
    }
  }
}
