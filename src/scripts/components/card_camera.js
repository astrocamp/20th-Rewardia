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
  
  // OCR 調試設定
  debugMode: true,
  minCardNumberLength: 12, // 最少卡號長度
  
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
          width: { min: 1280, ideal: 1920 },
          height: { min: 720, ideal: 1080 },
          facingMode: { ideal: 'environment' }
        },
        audio: false
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
  
  
  // 拍照並進行 OCR 識別（多次拍照投票）
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
      console.log('開始多次拍照投票識別...');
      
      // 多次拍照投票
      const result = await this.burstAndRecognize(3);
      
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
  
  // 多次拍照投票識別
  async burstAndRecognize(n = 3) {
    const results = [];
    const allNumbers = [];
    const allTexts = [];
    
    for (let i = 0; i < n; i++) {
      console.log(`第 ${i + 1} 次拍照...`);
      
      // 等待一小段時間讓畫面穩定
      if (i > 0) {
        await new Promise(r => setTimeout(r, 200));
      }
      
      // 拍照並處理
      const roiCanvas = await this.captureROI();
      if (!roiCanvas) continue;
      
      // 圖像預處理
      this.preprocessCanvas(roiCanvas);
      
      // 轉換為 blob
      const blob = await new Promise(resolve => {
        roiCanvas.toBlob(resolve, 'image/png', 1);
      });
      
      // 進行強化 OCR 識別
      const result = await this.performOCREnhanced(blob);
      
      if (result && result.rawText) {
        allTexts.push(result.rawText);
        const numbers = this.extractAllNumbers(result.rawText);
        console.log(`第 ${i + 1} 次識別結果:`, result.rawText);
        console.log(`第 ${i + 1} 次提取的數字:`, numbers);
        allNumbers.push(...numbers);
        
        if (result.success) {
          results.push(result.cardNumber);
        }
      }
    }
    
    console.log('所有識別結果:', results);
    console.log('所有提取的數字:', allNumbers);
    console.log('所有原始文本:', allTexts);
    
    // 如果有成功的識別結果，投票選擇最常見的
    if (results.length > 0) {
      const tally = results.reduce((m, s) => (m[s] = (m[s] || 0) + 1, m), {});
      const best = Object.entries(tally).sort((a, b) => b[1] - a[1])[0][0];
      console.log('投票結果:', best);
      return { success: true, cardNumber: best };
    }
    
    // 智能去重和拼接
    const uniqueNumbers = [...new Set(allNumbers)];
    console.log('去重後的數字:', uniqueNumbers);
    
    // 嘗試不同的拼接策略
    const strategies = [
      // 策略1：直接拼接所有數字
      allNumbers.join(''),
      // 策略2：拼接去重後的數字
      uniqueNumbers.join(''),
      // 策略3：合併所有原始文本再提取
      this.extractAllNumbers(allTexts.join(' ')).join(''),
      // 策略4：尋找最長的連續數字序列
      this.findLongestNumberSequence(allTexts.join(' '))
    ];
    
    console.log('不同策略的結果:', strategies);
    
    for (const strategy of strategies) {
      if (strategy && strategy.length >= 8) {
        // 限制策略結果最多16位
        const limitedStrategy = strategy.substring(0, 16);
        console.log('限制策略結果:', limitedStrategy);
        
        const cardNumber = this.extractCardNumber(limitedStrategy);
        if (cardNumber) {
          console.log('策略成功找到卡號:', cardNumber);
          return { success: true, cardNumber: cardNumber };
        }
      }
    }
    
    // 如果所有策略都失敗，返回最長的數字序列（最多16位）
    const longestSequence = strategies.reduce((a, b) => (a && a.length > b.length) ? a : b, '');
    if (longestSequence && longestSequence.length >= 8) {
      const limitedSequence = longestSequence.substring(0, 16);
      console.log('返回最長數字序列 (限制16位):', limitedSequence);
      return { success: true, cardNumber: limitedSequence };
    }
    
    return { 
      success: false, 
      error: `多次拍照未找到完整卡號。找到的數字: ${allNumbers.join(', ')}` 
    };
  },
  
  // 拍照並返回 ROI canvas（精確取景框定位）
  async captureROI() {
    try {
      // 讀取 video 的原始尺寸
      const vw = this.$refs.video.videoWidth;
      const vh = this.$refs.video.videoHeight;
      if (!vw || !vh) {
        console.warn('video 尚未就緒');
        return null;
      }
      
      console.log('Video 原始尺寸:', vw, 'x', vh);
      
      // 取得畫面上 video 與 frame 的實際位置（CSS 像素）
      const videoRect = this.$refs.video.getBoundingClientRect();
      const frameRect = this.$refs.frame.getBoundingClientRect();
      
      console.log('Video 畫面位置:', videoRect);
      console.log('Frame 畫面位置:', frameRect);
      
      // 將 CSS 像素換算成 video 原始像素的比例
      const sx = vw / videoRect.width;
      const sy = vh / videoRect.height;
      
      console.log('像素比例:', sx, sy);
      
      // 計算 ROI（以 video 原始像素為單位）
      let rx = Math.max(0, (frameRect.left - videoRect.left) * sx);
      let ry = Math.max(0, (frameRect.top - videoRect.top) * sy);
      let rw = Math.min(vw - rx, frameRect.width * sx);
      let rh = Math.min(vh - ry, frameRect.height * sy);
      
      console.log('計算的 ROI:', { rx, ry, rw, rh });
      
      // 若框太小或異常，回退成置中 80% 寬、按 1.586 比例
      if (rw < vw * 0.2 || rh < vh * 0.1 || ry >= vh) {
        console.log('取景框太小或位置異常，使用回退策略');
        const cardRatio = 1.586;
        const fallbackW = vw * 0.8;
        const fallbackH = fallbackW / cardRatio;
        rw = Math.min(vw, fallbackW);
        rh = Math.min(vh, fallbackH);
        rx = (vw - rw) / 2;
        ry = (vh - rh) / 2;
        console.log('回退 ROI:', { rx, ry, rw, rh });
      }
      
      // 放大取樣，提高清晰度
      const scale = 2;
      const roiW = Math.round(rw * scale);
      const roiH = Math.round(rh * scale);
      
      console.log('放大後的 ROI 尺寸:', roiW, 'x', roiH);
      
      // 準備暫存 canvas 畫 ROI
      const roiCanvas = document.createElement('canvas');
      roiCanvas.width = roiW;
      roiCanvas.height = roiH;
      const rctx = roiCanvas.getContext('2d', { willReadFrequently: true });
      
      // 把 video 的 ROI 畫到暫存 canvas（並放大）
      rctx.imageSmoothingEnabled = false;
      rctx.drawImage(this.$refs.video, rx, ry, rw, rh, 0, 0, roiW, roiH);
      
      console.log('ROI 擷取完成');
      return roiCanvas;
    } catch (error) {
      console.error('拍照失敗:', error);
      return null;
    }
  },
  
  // 圖像預處理（簡化版本）
  preprocessCanvas(canvas) {
    try {
      const ctx = canvas.getContext('2d');
      const { width, height } = canvas;
      const img = ctx.getImageData(0, 0, width, height);
      const d = img.data;

      for (let i = 0; i < d.length; i += 4) {
        const r = d[i], g = d[i+1], b = d[i+2];
        // 灰階
        let v = (0.299*r + 0.587*g + 0.114*b);
        // 提升對比
        v = Math.min(255, Math.max(0, (v - 100) * 1.6 + 100));
        // 二值化（降低閾值提高敏感度）
        const bin = v > 140 ? 255 : 0;
        d[i] = d[i+1] = d[i+2] = bin;
      }
      
      ctx.putImageData(img, 0, 0);
      console.log('圖像預處理完成');
      
      // 調試：保存處理後的圖像（可選）
      if (this.debugMode) {
        const link = document.createElement('a');
        link.download = `processed_${Date.now()}.png`;
        link.href = canvas.toDataURL();
        // link.click(); // 取消註釋可以自動下載
        console.log('處理後圖像已準備好下載');
      }
      
      return canvas;
    } catch (error) {
      console.error('圖像預處理失敗:', error);
    }
  },
  
  // 執行 OCR 識別
  async performOCR(imageBlob) {
    try {
      console.log('開始 OCR 識別...');
      
      const ocrConfig = {
        logger: m => {
          if (m.status === 'recognizing text') {
            console.log(`OCR 進度: ${Math.round(m.progress * 100)}%`);
          }
        },
        tessedit_char_whitelist: '0123456789',
        classify_bln_numeric_mode: 1,
        psm: 6, // 統一文字塊（從單行改為文字塊）
        tessedit_ocr_engine_mode: 1 // 神經網路LSTM引擎
      };
      
      console.log('使用優化 OCR 設定');
      
      const { data: { text } } = await Tesseract.recognize(imageBlob, 'eng', ocrConfig);
      
      console.log('OCR 原始識別結果:', text);
      
      // 提取所有數字
      const allNumbers = this.extractAllNumbers(text);
      console.log('提取到的所有數字:', allNumbers);
      
      // 提取 16 位數字
      const cardNumber = this.extractCardNumber(text);
      console.log('最終卡號:', cardNumber);
      
      if (cardNumber) {
        return {
          success: true,
          cardNumber: cardNumber,
          rawText: text,
          allNumbers: allNumbers
        };
      } else {
        return {
          success: false,
          error: `無法識別出完整的 16 位卡號。找到的數字: ${allNumbers.join(', ')}`,
          rawText: text,
          allNumbers: allNumbers
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
  
  // Luhn 檢查
  luhnCheck(num) {
    let sum = 0, alt = false;
    for (let i = num.length - 1; i >= 0; i--) {
      let n = parseInt(num[i], 10);
      if (alt) { 
        n *= 2; 
        if (n > 9) n -= 9; 
      }
      sum += n;
      alt = !alt;
    }
    return sum % 10 === 0;
  },
  
  // 提取所有數字序列
  extractAllNumbers(text) {
    // 找到所有連續的數字序列
    const numberMatches = text.match(/\d+/g);
    if (!numberMatches) return [];
    
    // 過濾和清理數字
    return numberMatches.filter(num => {
      // 只保留長度在4-16位之間的數字
      return num.length >= 4 && num.length <= 16;
    }).map(num => {
      // 如果數字超過16位，截取前16位
      return num.length > 16 ? num.substring(0, 16) : num;
    });
  },
  
  // 從文本中提取卡號（支持碎片組裝）
  extractCardNumber(text, aggressive = false) {
    console.log('原始文本:', text);
    
    const raw = (text || '').replace(/[^\d\s-]/g, ''); // 保留數字、空白、dash
    console.log('清理後文本:', raw);
    
    // 1) 直接找 15–19 位連號
    const direct = raw.replace(/\D/g, '').match(/\d{15,19}/);
    if (direct) {
      console.log('找到直接匹配:', direct[0]);
      return direct[0];
    }
    
    // 2) 找常見分組（4-4-4-4 / 4-6-5 / 4-4-5 等）
    const grouped =
      raw.match(/\b(\d{4})[ -]?(\d{4})[ -]?(\d{4})[ -]?(\d{3,5})\b/) || // 16~17
      raw.match(/\b(\d{4})[ -]?(\d{6})[ -]?(\d{5})\b/) ||               // 4-6-5
      raw.match(/\b(\d{4})[ -]?(\d{4})[ -]?(\d{4})[ -]?(\d{4})\b/) ||   // 4-4-4-4
      raw.match(/\b(\d{4})[ -]?(\d{6})[ -]?(\d{4})\b/) ||               // 4-6-4
      raw.match(/\b(\d{4})[ -]?(\d{4})[ -]?(\d{4})\b/);                 // 4-4-4 (不完整)
    
    if (grouped) {
      const num = grouped.slice(1).join('');
      if (num.length >= 15 && num.length <= 19) {
        console.log('找到分組匹配:', num);
        return num;
      }
    }
    
    if (!aggressive) return null;
    
    // 3) aggressive：把所有「看起來像卡號分組」的數字按出現順序串起來
    const pieces = raw.match(/\d{3,6}/g) || [];
    console.log('找到的數字片段:', pieces);
    
    // 只收集可能的 4~6 位片段
    const filtered = pieces.filter(p => p.length >= 3 && p.length <= 6);
    console.log('過濾後的片段:', filtered);
    
    if (filtered.length >= 3) {
      const stitched = filtered.join('');
      console.log('拼接結果:', stitched);
      const candidate = stitched.match(/\d{15,19}/);
      if (candidate) {
        console.log('找到拼接候選:', candidate[0]);
        return candidate[0];
      }
    }
    
    console.log('未找到符合條件的卡號');
    return null;
  },
  
  // 檢查卡號格式是否合理
  isValidCardFormat(number) {
    // 檢查是否以常見的卡號開頭
    const prefixes = [
      '4',     // Visa
      '5',     // Mastercard
      '3',     // American Express, Diners Club
      '6'      // Discover
    ];
    
    return prefixes.some(prefix => number.startsWith(prefix));
  },
  
  // 從多個候選中選擇最佳卡號（前端不進行 Luhn 驗證）
  pickBestCardNumber(list) {
    console.log('前端模式：跳過 Luhn 驗證，允許所有假卡號');
    
    // 優先選擇 16 位數字
    for (const n of list) if (n.length === 16) return n;
    // 其次選擇 15-19 位數字
    for (const n of list) if (n.length >= 15 && n.length <= 19) return n;
    // 最後返回最長的數字序列
    return list.sort((a,b)=>b.length-a.length)[0];
  },
  
  // 尋找最長的連續數字序列
  findLongestNumberSequence(text) {
    const allDigits = text.replace(/\D/g, '');
    if (allDigits.length < 8) return '';
    
    // 尋找最長的連續數字序列
    let longest = '';
    for (let i = 0; i < allDigits.length; i++) {
      for (let j = i + 8; j <= allDigits.length; j++) {
        const sequence = allDigits.slice(i, j);
        if (sequence.length > longest.length) {
          longest = sequence;
        }
      }
    }
    
    return longest;
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
  
  // 強化版 OCR 識別（多旋轉、多模式）
  async performOCREnhanced(imageBlob) {
    try {
      console.log('開始強化 OCR 識別...');
      
      // 讀成位圖以便旋轉與多次嘗試
      const baseBitmap = await createImageBitmap(imageBlob);
      
      // 將 bitmap 轉為 png blob 的小工具
      const toBlob = (bitmap) => new Promise((resolve) => {
        const c = document.createElement('canvas');
        c.width = bitmap.width; 
        c.height = bitmap.height;
        const g = c.getContext('2d', { willReadFrequently: true });
        g.drawImage(bitmap, 0, 0);
        c.toBlob(resolve, 'image/png', 1);
      });
      
      // 旋轉工具
      const rotateBitmap = async (bitmap, deg) => {
        if (deg === 0) return bitmap;
        const rad = deg * Math.PI / 180;
        const c = document.createElement('canvas');
        const w = bitmap.width, h = bitmap.height;
        if (deg % 180 === 0) { 
          c.width = w; 
          c.height = h; 
        } else { 
          c.width = h; 
          c.height = w; 
        }
        const g = c.getContext('2d', { willReadFrequently: true });
        g.translate(c.width/2, c.height/2);
        g.rotate(rad);
        g.drawImage(bitmap, -w/2, -h/2);
        return await createImageBitmap(c);
      };
      
      const rotations = [0, 90, 270];
      const psms = [7, 6, 13]; // 7=單行、6=單區塊、13=單行等寬
      const candidates = [];
      
      for (const deg of rotations) {
        console.log(`嘗試旋轉 ${deg} 度`);
        const bmp = await rotateBitmap(baseBitmap, deg);
        const blob = await toBlob(bmp);
        
        for (const psm of psms) {
          console.log(`使用 PSM ${psm}`);
          const { data: { text } } = await Tesseract.recognize(blob, 'eng', {
            // 盡量只看數字
            tessedit_char_whitelist: '0123456789 ',
            classify_bln_numeric_mode: 1,
            psm, // 文字行布局
            logger: m => { 
              if (m.status === 'recognizing text') 
                console.log(`OCR 進度: ${Math.round(m.progress*100)}%`); 
            }
          });
          
          console.log('OCR 原始識別結果:', text);
          const found = this.extractCardNumber(text, true); // aggressive mode
          if (found) {
            console.log('找到候選卡號:', found);
            candidates.push(found);
          }
        }
      }
      
      console.log('所有候選卡號:', candidates);
      
      // 從多個嘗試中挑最可靠者
      const best = this.pickBestCardNumber(candidates);
      if (best) {
        console.log('最佳卡號:', best);
        return { success: true, cardNumber: best, rawText: 'MULTI-TRY' };
      } else {
        return { success: false, error: '無法識別出完整卡號' };
      }
      
    } catch (error) {
      console.error('強化 OCR 識別失敗:', error);
      return { success: false, error: 'OCR 處理失敗' };
    }
  },
  
  // 處理 OCR 失敗
  handleOCRFailure(error) {
    this.retryCount++;
    
    console.log('OCR 失敗詳情:', error);
    
    if (this.retryCount >= this.maxRetries) {
      this.errorMessage = `無法識別完整卡號，請重新對準卡片拍照。已嘗試 ${this.maxRetries} 次，建議手動輸入。`;
      if (error.allNumbers && error.allNumbers.length > 0) {
        this.errorMessage += `\n\n識別到的數字: ${error.allNumbers.join(', ')}`;
      }
    } else {
      this.errorMessage = `無法識別完整卡號，請重新對準卡片拍照（${this.retryCount}/${this.maxRetries}）`;
      if (error.allNumbers && error.allNumbers.length > 0) {
        this.errorMessage += `\n\n識別到的數字: ${error.allNumbers.join(', ')}`;
      }
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
