export default (config = {}) => ({
  // 攝影機相關狀態
  cameraOpen: false,
  stream: null,
  video: null,
  canvas: null,
  ctx: null,
  
  // API 呼叫狀態
  processing: false,
  cardNumber: '',
  maskedNumber: '',
  luhnValid: false,
  retries: 0,
  maxRetries: 3,
  
  // UI 狀態
  showModal: false,
  error: '',
  showEdit: false,
  editNumber: '',
  
  // Toast 訊息狀態
  toast: {
    show: false,
    message: '',
    type: 'info'
  },
  
  // 初始化
  init() {
    console.log('card_camera init() 被調用');
    this.video = this.$refs.video;
    this.canvas = this.$refs.canvas;
    
    // 預先獲取 CSRF Token
    this.csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    
    console.log('video 初始化:', this.video);
    console.log('canvas 初始化:', this.canvas);
    console.log('CSRF Token 初始化:', this.csrfToken ? '已獲取' : '未找到');
    
    if (this.canvas) {
      this.ctx = this.canvas.getContext('2d', { willReadFrequently: true });
    }
  },
  
  // 開啟攝影機
  async openCamera() {
    console.log('openCamera 被調用');
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
      
      console.log('攝影機開啟成功');
    } catch (error) {
      console.error('開啟攝影機失敗:', error);
      this.error = '無法開啟攝影機，請檢查權限設定';
      this.cameraOpen = false;
    }
  },
  
  // 關閉攝影機
  closeCamera() {
    console.log('closeCamera 被調用');
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
  
  // 計算 ROI 百分比座標
  calculateROI() {
    if (!this.$refs.frame) {
      console.error('找不到取景框元素');
      return null;
    }
    
    const frame = this.$refs.frame;
    const video = this.$refs.video;
    
    if (!video || !frame) {
      console.error('找不到 video 或 frame 元素');
      return null;
    }
    
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
    
    console.log('計算的 ROI 百分比:', roi);
    return roi;
  },
  
  // 拍照並呼叫後端 OCR API
  async captureAndRecognize() {
    console.log('captureAndRecognize 被調用');
    if (!this.cameraOpen || this.processing) {
      console.log('攝影機未開啟或正在處理中');
      return;
    }
    
    this.processing = true;
    this.error = '';
    
    try {
      // 計算 ROI 座標
      const roi = this.calculateROI();
      if (!roi) {
        throw new Error('無法計算取景框座標');
      }
      
      // 拍攝完整影像（不裁切）
      const imageBlob = await this.captureFullImage();
      if (!imageBlob) {
        throw new Error('拍照失敗');
      }
      
      // 呼叫後端 API
      await this.callOCRAPI(imageBlob, roi);
      
    } catch (error) {
      console.error('拍照識別失敗:', error);
      this.error = error.message || '拍照識別失敗，請重試';
      this.retries++;
    } finally {
      this.processing = false;
    }
  },
  
  // 拍攝完整影像
  async captureFullImage() {
    if (!this.video || !this.canvas || !this.ctx) {
      throw new Error('攝影機或畫布未初始化');
    }
    
    const video = this.video;
    const canvas = this.canvas;
    const ctx = this.ctx;
    
    // 設定畫布尺寸為影片實際尺寸
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // 繪製完整影片畫面
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // 轉換為 Blob
    return new Promise((resolve, reject) => {
      canvas.toBlob((blob) => {
        if (blob) {
          console.log('完整影像拍攝成功，大小:', blob.size, 'bytes');
          resolve(blob);
        } else {
          reject(new Error('影像轉換失敗'));
        }
      }, 'image/jpeg', 0.9);
    });
  },
  
  // 呼叫後端 OCR API
  async callOCRAPI(imageBlob, roi) {
    const formData = new FormData();
    formData.append('image', imageBlob, 'card_image.jpg');
    formData.append('roi', JSON.stringify(roi));
    
    console.log('發送 OCR API 請求...');
    console.log('ROI:', roi);
    console.log('影像大小:', imageBlob.size, 'bytes');
    
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
      console.log('OCR API 回應:', result);
      
      if (result.success) {
        this.maskedNumber = result.masked || '';
        this.cardNumber = result.card_number || '';
        this.luhnValid = result.luhn_valid || false;
        
        // 檢查是否成功識別到16位卡號
        const cardNumberDigits = this.cardNumber ? this.cardNumber.replace(/\D/g, '') : '';
        
        if (cardNumberDigits.length === 16) {
          // 識別成功：顯示成功訊息並開啟編輯模式
          this.showMessage('卡號辨識成功，請確認掃描結果', 'success');
          this.showEdit = true;
          this.editNumber = this.cardNumber;
          this.closeCamera();
        } else {
          // 識別失敗：顯示失敗訊息並重新拍照
          this.showMessage('卡號辨識失敗，請重新拍照', 'error');
          this.retries++;
          // 延遲1秒後重新開啟攝影機
          setTimeout(() => {
            this.openCamera();
          }, 1000);
        }
      } else {
        throw new Error(result.error || 'OCR 識別失敗');
      }
      
    } catch (error) {
      console.error('OCR API 呼叫失敗:', error);
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
  
  // 顯示訊息（統一處理成功/錯誤）
  showMessage(message, type = 'info') {
    if (type === 'error') {
      this.error = message;
    } else {
      this.error = '';
    }
    
    // 使用 Alpine.js 狀態管理 Toast
    this.toast.show = true;
    this.toast.message = message;
    this.toast.type = type;
    
    // 自動隱藏 Toast
    setTimeout(() => {
      this.toast.show = false;
    }, 3000);
  },
  
  // 確認編輯的卡號
  confirmCardNumber() {
    if (this.editNumber.length >= 12) {
      this.cardNumber = this.editNumber;
      this.showEdit = false;
      console.log('確認的卡號:', this.cardNumber);
    } else {
      alert('請輸入完整的卡號（至少12位數字）');
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
    // 重新開啟攝影機
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
  
  // 智能格式化卡號輸入（保持游標位置）
  formatCardInput(event) {
    const input = event.target;
    const cursorPosition = input.selectionStart;
    const oldValue = input.value;
    
    // 移除非數字字符
    const cleaned = oldValue.replace(/\D/g, '');
    
    // 限制最多16位數字
    const limited = cleaned.substring(0, 16);
    
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
  }
});