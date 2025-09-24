export default (config = {}) => ({
  // 攝影機相關狀態
  cameraOpen: false,
  stream: null,
  video: null,
  canvas: null,
  ctx: null,
  
  // 當前操作的卡片 ID
  currentCardId: null,
  
  // API 呼叫狀態
  processing: false,
  cardNumber: '',
  memberZoneRecognizedNumber: '', // 專用於 member_zone 的辨識卡號變數
  maskedNumber: '',
  luhnValid: false,
  retries: 0,
  maxRetries: 3,
  
  // UI 狀態
  showModal: false,
  error: '',
  showEdit: false,
  editNumber: '',
  
  // 初始化
  init() {
    this.video = this.$refs.video;
    this.canvas = this.$refs.canvas;
    
    // 預先獲取 CSRF Token
    this.csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    
    if (this.canvas) {
      this.ctx = this.canvas.getContext('2d', { willReadFrequently: true });
    }
  },
  
  // 開啟攝影機
  async openCamera(eventData) {
    // 保存當前操作的卡片 ID
    this.currentCardId = eventData?.cardId || null;
    
    // member_zone 專用模式
    this.isCardFormMode = false;
    
    try {
      this.error = '';
      this.showModal = true;
      
      // 等待 DOM 更新
      await this.$nextTick();
      
      const constraints = {
        video: {
          width: { min: 1280, ideal: 1920 },
          height: { min: 720, ideal: 1080 },
          facingMode: 'environment'
        }
      };
      
      this.stream = await navigator.mediaDevices.getUserMedia(constraints);
      this.video.srcObject = this.stream;
      this.cameraOpen = true;
    } catch (error) {
      this.cameraOpen = false;
      this.handleError(error, '無法開啟攝影機，請檢查權限設定');
    }
  },
  
  // 關閉攝影機
  closeCamera() {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }
    this.cameraOpen = false;
    this.showModal = false;
    this.error = '';
    this.cardNumber = '';
    this.maskedNumber = '';
    this.retries = 0;
  },
  
  // 驗證必要元素
  validateElements() {
    const frame = this.$refs.frame;
    const video = this.$refs.video;
    
    if (!frame) {
      if (window.RewardiaLogger) {
        window.RewardiaLogger.error('找不到取景框元素');
      }
      return false;
    }
    
    if (!video) {
      if (window.RewardiaLogger) {
        window.RewardiaLogger.error('找不到 video 元素');
      }
      return false;
    }
    
    return { frame, video };
  },
  
  // 計算 ROI 百分比座標
  calculateROI() {
    const elements = this.validateElements();
    if (!elements) return null;
    
    const { frame, video } = elements;
    
    const frameRect = frame.getBoundingClientRect();
    const videoRect = video.getBoundingClientRect();
    
    // 計算相對位置
    const left = ((frameRect.left - videoRect.left) / videoRect.width) * 100;
    const top = ((frameRect.top - videoRect.top) / videoRect.height) * 100;
    const width = (frameRect.width / videoRect.width) * 100;
    const height = (frameRect.height / videoRect.height) * 100;
    
    const roi = {
      left: Math.round(left * 100) / 100,
      top: Math.round(top * 100) / 100,
      width: Math.round(width * 100) / 100,
      height: Math.round(height * 100) / 100
    };
    
    return roi;
  },
  
  // 拍照並呼叫後端 OCR API
  async captureAndRecognize() {
    if (!this.cameraOpen || this.processing) {
      return;
    }
    
    this.processing = true;
    this.error = '';
    
    try {
      // 拍攝 ROI 區域影像（只送 ROI 區域給後端）
      const imageBlob = await this.captureROIImage();
      if (!imageBlob) {
        throw new Error('拍照失敗');
      }
      
      // 呼叫後端 API（不需要 ROI 座標，因為已經裁切了）
      await this.callOCRAPI(imageBlob);
      
    } catch (error) {
      this.handleError(error, '拍照識別失敗，請重試');
      this.retries++;
    } finally {
      this.processing = false;
    }
  },
  
  // 拍攝 ROI 區域影像
  async captureROIImage() {
    if (!this.video || !this.canvas || !this.ctx) {
      throw new Error('攝影機或畫布未初始化');
    }
    
    const { video, canvas, ctx } = this;
    const roi = this.calculateROI();
    
    if (!roi) {
      throw new Error('無法計算 ROI 座標');
    }
    
    // 計算實際像素座標
    const videoWidth = video.videoWidth;
    const videoHeight = video.videoHeight;
    
    const left = Math.round((roi.left / 100) * videoWidth);
    const top = Math.round((roi.top / 100) * videoHeight);
    const width = Math.round((roi.width / 100) * videoWidth);
    const height = Math.round((roi.height / 100) * videoHeight);
    
    // 設定畫布尺寸為 ROI 區域尺寸
    canvas.width = width;
    canvas.height = height;
    
    // 繪製 ROI 區域
    ctx.drawImage(
      video, 
      left, top, width, height,  // 來源區域 (ROI)
      0, 0, width, height        // 目標區域 (整個畫布)
    );
    
    // 轉換為 Blob，降低品質以減少檔案大小
    return new Promise((resolve, reject) => {
      canvas.toBlob((blob) => {
        if (blob) {
          resolve(blob);
        } else {
          reject(new Error('影像轉換失敗'));
        }
      }, 'image/jpeg', 0.8); // 降低品質到 0.8
    });
  },
  
  // 呼叫後端 OCR API
  async callOCRAPI(imageBlob) {
    const formData = new FormData();
    formData.append('image', imageBlob, 'card_image.jpg');
    
    try {
      const response = await fetch('/api/ocr/vision/', {
        method: 'POST',
        body: formData,
        headers: {
          'X-CSRFToken': this.getCSRFToken()
        }
      });
      
      if (!response.ok) {
        throw new Error(`API 請求失敗: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result.success) {
        this.maskedNumber = result.masked || '';
        this.cardNumber = result.card_number || '';
        this.memberZoneRecognizedNumber = result.card_number || ''; // 使用專用變數
        this.luhnValid = result.luhn_valid || false;
        
        // 檢查是否成功識別到16位卡號
        const cardNumberDigits = this.cardNumber ? this.cardNumber.replace(/\D/g, '') : '';
        
        if (cardNumberDigits.length === 16) {
          // 識別成功：顯示確認介面
          this.showMessage('卡號辨識成功，請確認掃描結果', 'success');
          this.showEdit = true;
          this.editNumber = this.cardNumber;
          this.closeCamera();
        } else {
          // 識別失敗：嘗試錯誤回補
          const fallbackNumber = this.extractLongestNumber(result.full_text || '');
          
          // member_zone 模式：顯示編輯模式
          if (fallbackNumber && fallbackNumber.length >= 10) {
            this.showMessage('卡號辨識不完整，已自動填入部分數字，請手動修正', 'info');
            this.showEdit = true;
            this.editNumber = this.formatCardNumber(fallbackNumber);
            this.closeCamera();
          } else {
            this.showMessage('卡號辨識失敗，請重新拍照', 'error');
            this.retries++;
            // 延遲1秒後重新開啟攝影機
            setTimeout(() => {
              this.openCamera();
            }, 1000);
          }
        }
      } else {
        throw new Error(result.error || 'OCR 識別失敗');
      }
      
    } catch (error) {
      this.handleError(error, 'OCR API 呼叫失敗');
      throw error;
    }
  },
  
  // 重新拍照
  retryCapture() {
    if (this.retries < this.maxRetries) {
      this.error = '';
      this.captureAndRecognize();
    } else {
      this.openManualInput();
    }
  },
  
  // 開啟手動輸入
  openManualInput() {
    this.showEdit = true;
    this.editNumber = '';
    this.closeCamera();
  },
  
  // 統一錯誤處理
  handleError(error, defaultMessage = '操作失敗，請重試') {
    const message = error?.message || defaultMessage;
    this.error = message;
    this.showMessage(message, 'error');
    if (window.RewardiaLogger) {
      window.RewardiaLogger.error('操作失敗:', error);
    }
  },
  
  // 顯示訊息（統一處理成功/錯誤）
  showMessage(message, type = 'info') {
    if (type === 'error') {
      this.error = message;
    } else {
      this.error = '';
    }
    
    // 使用全域 toast 系統
    if (window.showToast) {
      window.showToast(message, type);
    }
  },
  
  // 確認編輯的卡號
  async confirmCardNumber() {
    // 移除所有非數字字符
    const cleanNumber = this.editNumber.replace(/\D/g, '');
    
    // 驗證卡號格式
    const validation = this.validateCardNumber(cleanNumber);
    if (!validation.isValid) {
      if (window.showToast) {
        window.showToast(validation.message, 'error');
      }
      return;
    }
    
    if (!this.currentCardId) {
      if (window.showToast) {
        window.showToast('錯誤：無法識別卡片 ID', 'error');
      }
      return;
    }
    
    try {
      // 調用 API 保存卡號
      const response = await fetch(`/users/card/${this.currentCardId}/add-number/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': this.getCSRFToken(),
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          card_number: cleanNumber
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        if (window.showToast) {
          window.showToast('卡號新增成功！', 'success');
        }
        this.showEdit = false;
        this.closeCamera();
        // 延遲重新載入頁面
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      } else {
        if (window.showToast) {
          window.showToast(data.message || '新增失敗', 'error');
        }
      }
    } catch (error) {
      if (window.RewardiaLogger) {
        window.RewardiaLogger.error('儲存卡號錯誤:', error);
      }
      if (window.showToast) {
        window.showToast('新增失敗，請稍後再試', 'error');
      }
    }
  },
  
  // 重置編輯狀態（保留已識別的卡號）
  resetEditState() {
    this.showEdit = false;
    this.editNumber = '';
    this.error = '';
  },
  
  // 完全重置狀態（清空所有識別結果）
  resetAllState() {
    this.showEdit = false;
    this.editNumber = '';
    this.cardNumber = '';
    this.maskedNumber = '';
    this.error = '';
    this.retries = 0;
  },
  
  // 取消編輯
  cancelEdit() {
    this.resetEditState();
  },
  
  // 重新辨識
  retryRecognition() {
    this.resetAllState();
    // 重新開啟攝影機，保持 member_zone 模式
    this.openCamera();
  },
  
  // 格式化卡號顯示（每4位加空格）
  formatCardNumber(cardNumber) {
    if (!cardNumber) return '';
    // 如果已經有空格，直接返回
    if (cardNumber.includes(' ')) return cardNumber;
    // 否則移除非數字字符並每4位加空格
    const cleaned = cardNumber.replace(/\D/g, '');
    return cleaned.replace(/(.{4})/g, '$1 ').trim();
  },

  // 從 OCR 文字中提取最長的數字序列（錯誤回補用）
  extractLongestNumber(text) {
    if (!text) return '';
    
    // 移除所有非數字字符
    const numbersOnly = text.replace(/\D/g, '');
    
    // 尋找所有數字序列（至少8位）
    const numberSequences = numbersOnly.match(/\d{8,}/g);
    
    if (!numberSequences || numberSequences.length === 0) {
      return '';
    }
    
    // 返回最長的數字序列
    return numberSequences.reduce((longest, current) => 
      current.length > longest.length ? current : longest, '');
  },
  
  // 智能格式化卡號輸入（保持游標位置）
  formatCameraCardInput(event) {
    const input = event.target;
    const cursorPosition = input.selectionStart;
    const oldValue = input.value;
    
    // 移除非數字字符
    const cleaned = oldValue.replace(/\D/g, '');
    
    // 限制最多16位數字
    const limited = cleaned.substring(0, 19);
    
    // 每4位加空格
    const formatted = limited.replace(/(.{4})/g, '$1 ').trim();
    
    // 設置新值
    input.value = formatted;
    
    // 計算新的游標位置
    let newCursorPosition = cursorPosition;
    
    // 如果刪除了字符，游標位置需要調整
    if (formatted.length < oldValue.length) {
      // 計算刪除的字符數
      const deletedChars = oldValue.length - formatted.length;
      newCursorPosition = Math.max(0, cursorPosition - deletedChars);
    } else if (formatted.length > oldValue.length) {
      // 如果添加了空格，游標位置需要前移
      const addedChars = formatted.length - oldValue.length;
      newCursorPosition = cursorPosition + addedChars;
    }
    
    // 設置游標位置
    this.$nextTick(() => {
      input.setSelectionRange(newCursorPosition, newCursorPosition);
    });
    
    // 更新 editNumber
    this.editNumber = formatted;
  },
  
  // 獲取 CSRF Token
  getCSRFToken() {
    return this.csrfToken || '';
  },
  
  // 驗證卡號格式
  validateCardNumber(cardNumber) {
    // 檢查長度：12-19 位數字
    if (cardNumber.length < 12 || cardNumber.length > 19) {
      return { 
        isValid: false, 
        message: '卡號長度必須在12-19位之間' 
      };
    }
    
    // 檢查格式：只允許數字
    if (!/^\d+$/.test(cardNumber)) {
      return { 
        isValid: false, 
        message: '卡號只能包含數字' 
      };
    }
    
    return { 
      isValid: true, 
      message: '卡號格式正確' 
    };
  }
});
