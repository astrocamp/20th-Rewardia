// Related HTML: templates/admins/scheduler.html
const schedulerControl = () => ({
  // 動態版本路徑
  get versionPath() {
    const pathParts = window.location.pathname.split('/').filter(part => part);
    return pathParts[0];
  },

  // 基本狀態
  schedule: {
    hour: 8,
    minute: 0,
    enabled: false,
    last_run_at: null,
    is_running: false,
    current_task: null,
    celery_worker_active: false,
    celery_beat_active: false
  },
  crawledRecords: [],
  analysisRecords: [],
  isLoading: false,

  // 初始化
  async init() {
    await this.loadScheduleStatus();
    await this.loadCrawledRecords();
    await this.loadAnalysisRecords();

    // 每10秒刷新排程狀態（檢查是否在執行）
    setInterval(() => {
      this.loadScheduleStatus();
    }, 10000);

    // 每30秒刷新記錄數據
    setInterval(() => {
      this.loadCrawledRecords();
      this.loadAnalysisRecords();
    }, 30000);
  },

  // 載入排程狀態
  async loadScheduleStatus() {
    try {
      const data = await this.apiRequest(`/${this.versionPath}/scheduler/api/status/`);
      if (data.success) {
        // 確保 current_task 為 null 時不會出錯
        const schedule = data.schedule;
        if (!schedule.current_task) {
          schedule.current_task = null;
        }
        // 確保 hour 和 minute 是數字類型
        if (schedule.hour !== undefined) {
          schedule.hour = parseInt(schedule.hour);
        }
        if (schedule.minute !== undefined) {
          schedule.minute = parseInt(schedule.minute);
        }
        this.schedule = { ...this.schedule, ...schedule };
      }
    } catch (error) {
      if (window.RewardiaLogger) {
        window.RewardiaLogger.error('載入排程狀態失敗:', error);
      }
    }
  },

  // 更新排程時間
  async updateSchedule() {
    try {
      // 驗證輸入值
      const hour = parseInt(this.schedule.hour);
      const minute = parseInt(this.schedule.minute);

      if (isNaN(hour) || hour < 0 || hour > 23) {
        this.showError('小時必須是 0-23 之間的數字');
        return;
      }

      if (isNaN(minute) || minute < 0 || minute > 59) {
        this.showError('分鐘必須是 0-59 之間的數字');
        return;
      }

      // 確保數值格式正確
      this.schedule.hour = hour;
      this.schedule.minute = minute;

      this.isLoading = true;

      const data = await this.apiRequest(`/${this.versionPath}/scheduler/api/update/`, {
        method: 'POST',
        body: JSON.stringify({
          hour: hour,
          minute: minute
        })
      });

      if (data.success) {
        this.showSuccess(data.message);
      } else {
        this.showError(data.error || '更新排程失敗');
      }

    } catch (error) {
      if (window.RewardiaLogger) {
        window.RewardiaLogger.error('更新排程失敗:', error);
      }
      this.showError('更新排程失敗');
    } finally {
      this.isLoading = false;
    }
  },

  // 切換排程啟用狀態
  async toggleSchedule() {
    try {
      this.isLoading = true;

      const data = await this.apiRequest(`/${this.versionPath}/scheduler/api/toggle/`, {
        method: 'POST'
      });

      if (data.success) {
        this.schedule.enabled = data.enabled;
        this.showSuccess(data.message);
      } else {
        // 如果失敗，恢復原來的狀態
        this.schedule.enabled = !this.schedule.enabled;
        this.showError(data.error || '切換排程狀態失敗');
      }

    } catch (error) {
      if (window.RewardiaLogger) {
        window.RewardiaLogger.error('切換排程狀態失敗:', error);
      }
      this.schedule.enabled = !this.schedule.enabled;
      this.showError('切換排程狀態失敗');
    } finally {
      this.isLoading = false;
    }
  },

  // 立即執行爬蟲
  async runNow() {
    try {
      this.isLoading = true;

      const data = await this.apiRequest(`/${this.versionPath}/scheduler/api/run-now/`, {
        method: 'POST'
      });

      if (data.success) {
        this.showSuccess(data.message);

        // 3秒後刷新記錄
        setTimeout(() => {
          this.loadCrawledRecords();
        }, 3000);

      } else {
        this.showError(data.error || '執行爬蟲失敗');
      }

    } catch (error) {
      if (window.RewardiaLogger) {
        window.RewardiaLogger.error('執行爬蟲失敗:', error);
      }
      this.showError('執行爬蟲失敗');
    } finally {
      this.isLoading = false;
    }
  },

  // 載入爬蟲執行記錄
  async loadCrawledRecords() {
    try {
      const data = await this.apiRequest(`/${this.versionPath}/scheduler/api/crawled-records/`);
      if (data.success) {
        this.crawledRecords = data.records;
      }
    } catch (error) {
      if (window.RewardiaLogger) {
        window.RewardiaLogger.error('載入爬蟲記錄失敗:', error);
      }
    }
  },

  // 載入分析記錄
  async loadAnalysisRecords() {
    try {
      const data = await this.apiRequest(`/${this.versionPath}/scheduler/api/analysis-records/`);
      if (data.success) {
        this.analysisRecords = data.records;
      }
    } catch (error) {
      if (window.RewardiaLogger) {
        window.RewardiaLogger.error('載入分析記錄失敗:', error);
      }
    }
  },

  // API 請求封裝
  async apiRequest(url, options = {}) {
    const defaultOptions = {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': this.getCsrfToken(),
      },
      credentials: 'same-origin',
    };

    const mergedOptions = { ...defaultOptions, ...options };

    const response = await fetch(url, mergedOptions);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  },

  // 獲取 CSRF Token
  getCsrfToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  },

  // 顯示成功消息
  showSuccess(message) {
    // 使用 Alpine 的事件分發來顯示 toast
    this.$dispatch('toast', {
      type: 'success',
      message: message
    });
  },

  // 顯示錯誤消息
  showError(message) {
    // 使用 Alpine 的事件分發來顯示 toast
    this.$dispatch('toast', {
      type: 'error',
      message: message
    });
  }
});


// 導出
export default schedulerControl;