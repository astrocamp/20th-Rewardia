import Tesseract from 'tesseract.js';

export default (config = {}) => ({
  // 攝影機相關狀態
  isCameraOpen: false,
  stream: null,
  videoElement: null,
  canvas: null,
  ctx: null,
  
  // OCR 相關狀態
  isProcessing: false,
  recognizedCardNumber: '',
  retryCount: 0,
  maxRetries: 3,
  
  // UI 狀態
  showCameraModal: false,
  showResult: false,
  errorMessage: '',
  
  // 取景框尺寸（百分比）
  cardFrameWidth: 40,
  cardFrameHeight: 40 / 1.586, // 根據 1.586 比例計算
  
  // 初始化
  init() {
    console.log('card_camera init() 被調用');
    console.log('取景框尺寸 - 寬度:', this.cardFrameWidth + '%', '高度:', this.cardFrameHeight + '%');
    this.videoElement = this.$refs.video;
    this.canvas = this.$refs.canvas;
    console.log('videoElement 初始化:', this.videoElement);
    console.log('canvas 初始化:', this.canvas);
    if (this.canvas) {
      this.ctx = this.canvas.getContext('2d');
    }
  },
  
  // 開啟攝影機
  async openCamera() {
    console.log('openCamera 被調用');
    try {
      this.errorMessage = '';
      this.showCameraModal = true;
      console.log('showCameraModal 設為 true:', this.showCameraModal);
      
      // 檢查瀏覽器支援
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        this.errorMessage = '您的瀏覽器不支援攝影機功能';
        console.error('瀏覽器不支援攝影機');
        return;
      }
      
      // 先關閉舊的串流
      if (this.stream) {
        this.stream.getTracks().forEach(track => track.stop());
        this.stream = null;
      }
      
      // 請求攝影機權限
      const constraints = {
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'environment'
        }
      };
      
      console.log('請求攝影機權限，約束條件:', constraints);
      this.stream = await navigator.mediaDevices.getUserMedia(constraints);
      console.log('攝影機串流獲取成功:', this.stream);
      
      // 設定影片來源
      this.videoElement.srcObject = this.stream;
      
      // 確保 iOS Safari 兼容性
      this.videoElement.setAttribute('playsinline', true);
      this.videoElement.setAttribute('autoplay', true);
      this.videoElement.muted = true;
      
      // 等待影片載入
      await new Promise((resolve) => {
        this.videoElement.onloadedmetadata = () => {
          this.videoElement.play();
          resolve();
        };
      });
      
      this.isCameraOpen = true;
      
      // 使用 $nextTick 確保 Alpine.js 完成更新
      this.$nextTick(() => {
        this.showCameraModal = true;
        console.log('攝影機開啟成功，isCameraOpen:', this.isCameraOpen, 'showCameraModal:', this.showCameraModal);
        
        // 檢查 video 元素
        console.log('videoElement:', this.videoElement);
        console.log('videoElement.srcObject:', this.videoElement.srcObject);
        console.log('videoElement.srcObject instanceof MediaStream:', this.videoElement.srcObject instanceof MediaStream);
        
        // 再次使用 $nextTick 確保 DOM 更新
        this.$nextTick(() => {
          console.log('Alpine DOM 更新完成');
          console.log('DOM 中的模態框元素:', document.querySelector('[x-show="showCameraModal"]'));
          console.log('當前 showCameraModal 值:', this.showCameraModal);
          console.log('當前取景框尺寸 - 寬度:', this.cardFrameWidth + '%', '高度:', this.cardFrameHeight + '%');
          
          // 檢查取景框元素
          const frameElements = document.querySelectorAll('[style*="width: ${cardFrameWidth}%"]');
          console.log('找到的取景框元素數量:', frameElements.length);
          
          // 如果模態框仍然隱藏，強制顯示
          const modalElement = document.querySelector('[x-show="showCameraModal"]');
          if (modalElement && modalElement.style.display === 'none') {
            console.log('強制顯示模態框');
            modalElement.style.display = 'block';
            modalElement.style.visibility = 'visible';
          }
        });
      });
      
    } catch (error) {
      console.error('攝影機開啟失敗:', error);
      console.error('錯誤名稱:', error.name);
      console.error('錯誤訊息:', error.message);
      
      if (error.name === 'NotAllowedError') {
        this.errorMessage = '請允許使用攝影機權限，並重新整理頁面';
      } else if (error.name === 'NotFoundError') {
        this.errorMessage = '未搜尋到攝影機，請檢查您的設備';
      } else if (error.name === 'NotReadableError') {
        this.errorMessage = '攝影機正被其他應用程式使用';
      } else if (error.name === 'OverconstrainedError') {
        this.errorMessage = '攝影機設定不支援，嘗試使用前置攝影機';
      } else {
        this.errorMessage = `攝影機開啟失敗: ${error.message}`;
      }
      
      this.showCameraModal = true; // 即使失敗也顯示模態框以顯示錯誤
    }
  },
  
  // 關閉攝影機
  closeCamera() {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }
    
    if (this.videoElement) {
      this.videoElement.srcObject = null;
    }
    
    this.isCameraOpen = false;
    this.showCameraModal = false;
    this.showResult = false;
    this.recognizedCardNumber = '';
    this.retryCount = 0;
    this.errorMessage = '';
  },
  
  // 拍照並進行 OCR 識別
  async captureAndRecognize() {
    console.log('captureAndRecognize 被調用');
    console.log('isCameraOpen:', this.isCameraOpen);
    console.log('isProcessing:', this.isProcessing);
    
    if (!this.isCameraOpen || this.isProcessing) {
      console.log('條件不滿足，退出函數');
      return;
    }
    
    try {
      this.isProcessing = true;
      this.errorMessage = '';
      console.log('開始拍照處理...');
      
      // 設定 canvas 尺寸
      const videoWidth = this.videoElement.videoWidth;
      const videoHeight = this.videoElement.videoHeight;
      this.canvas.width = videoWidth;
      this.canvas.height = videoHeight;
      
      // 計算取景框位置（1.586 比例）
      const cardRatio = 1.586;
      const frameWidth = Math.min(videoWidth * 0.8, videoHeight * 0.8 * cardRatio);
      const frameHeight = frameWidth / cardRatio;
      const frameX = (videoWidth - frameWidth) / 2;
      const frameY = (videoHeight - frameHeight) / 2;
      
      // 裁切並繪製到 canvas
      this.ctx.drawImage(
        this.videoElement,
        frameX, frameY, frameWidth, frameHeight,
        0, 0, frameWidth, frameHeight
      );
      
      // 轉換為 blob
      const blob = await new Promise(resolve => {
        this.canvas.toBlob(resolve, 'image/jpeg', 0.8);
      });
      
      // 進行 OCR 識別
      const result = await this.performOCR(blob);
      
      if (result.success) {
        this.recognizedCardNumber = result.cardNumber;
        this.showResult = true;
        this.closeCamera();
        
        // 將識別結果填入表單
        this.fillCardNumber(result.cardNumber);
      } else {
        this.handleOCRFailure(result.error);
      }
      
    } catch (error) {
      console.error('拍照識別失敗:', error);
      this.handleOCRFailure('拍照處理失敗');
    } finally {
      this.isProcessing = false;
    }
  },
  
  // 執行 OCR 識別
  async performOCR(imageBlob) {
    try {
      console.log('開始 OCR 識別...');
      
      const { data: { text } } = await Tesseract.recognize(imageBlob, 'eng', {
        logger: m => {
          if (m.status === 'recognizing text') {
            console.log(`OCR 進度: ${Math.round(m.progress * 100)}%`);
          }
        }
      });
      
      console.log('OCR 識別結果:', text);
      
      // 提取 16 位數字
      const cardNumber = this.extractCardNumber(text);
      
      if (cardNumber) {
        return {
          success: true,
          cardNumber: cardNumber,
          rawText: text
        };
      } else {
        return {
          success: false,
          error: '無法識別出完整的 16 位卡號',
          rawText: text
        };
      }
      
    } catch (error) {
      console.error('OCR 識別失敗:', error);
      return {
        success: false,
        error: 'OCR 識別過程發生錯誤'
      };
    }
  },
  
  // 從文本中提取 16 位卡號
  extractCardNumber(text) {
    // 移除所有非數字字符
    const numbersOnly = text.replace(/\D/g, '');
    
    // 尋找 16 位連續數字
    const cardNumberMatch = numbersOnly.match(/\d{16}/);
    
    if (cardNumberMatch) {
      const cardNumber = cardNumberMatch[0];
      
      // 基本驗證：檢查是否為有效的信用卡格式
      if (this.isValidCardNumber(cardNumber)) {
        return cardNumber;
      }
    }
    
    // 如果沒有找到 16 位數字，嘗試其他長度
    const allNumbers = numbersOnly.match(/\d+/g);
    if (allNumbers) {
      // 尋找最接近 16 位的數字
      for (const num of allNumbers) {
        if (num.length >= 14 && num.length <= 19) {
          console.log(`找到 ${num.length} 位數字: ${num}`);
          if (num.length === 16) {
            return num;
          }
        }
      }
    }
    
    return null;
  },
  
  // 基本卡號驗證
  isValidCardNumber(cardNumber) {
    // 長度檢查
    if (cardNumber.length !== 16) {
      return false;
    }
    
    // 不能全為相同數字
    if (/^(\d)\1{15}$/.test(cardNumber)) {
      return false;
    }
    
    return true;
  },
  
  // 處理 OCR 失敗
  handleOCRFailure(error) {
    this.retryCount++;
    
    if (this.retryCount >= this.maxRetries) {
      this.errorMessage = `無法識別完整卡號，請重新對準卡片拍照。已嘗試 ${this.maxRetries} 次，建議手動輸入。`;
    } else {
      this.errorMessage = `無法識別完整卡號，請重新對準卡片拍照（${this.retryCount}/${this.maxRetries}）`;
    }
    
    console.error('OCR 失敗:', error);
  },
  
  // 重新拍照
  retryCapture() {
    this.errorMessage = '';
    // 重新拍照會自動增加 retryCount
    this.captureAndRecognize();
  },
  
  // 手動輸入
  openManualInput() {
    this.closeCamera();
    // 這裡可以觸發手動輸入的 UI
    alert('請手動輸入卡號功能尚未實現');
  },
  
  // 將識別結果填入表單
  fillCardNumber(cardNumber) {
    // 格式化卡號顯示（每 4 位加空格）
    const formattedNumber = cardNumber.replace(/(\d{4})(?=\d)/g, '$1 ');
    
    // 這裡需要根據實際的表單結構來填入
    // 假設有一個隱藏的卡號輸入欄位
    const cardNumberInput = document.getElementById('card-number-input');
    if (cardNumberInput) {
      cardNumberInput.value = cardNumber;
    }
    
    console.log('識別到的卡號:', formattedNumber);
    alert(`成功識別卡號: ${formattedNumber}`);
  }
});
