// Related HTML: templates/pages/main.html
export default () => ({
  selectedBank: '',
  selectedReward: '',
  displayCards: [],
  allCards: [],
  originalCards: [], // 保存原始完整卡片資料
  loadedCount: 3, // 已載入的卡片數量
  loadIncrement: 1, // 每次滾動載入的數量
  isLoading: false,
  isLoadingMore: false, // 是否正在載入更多
  
  // 初始化假資料
  init() {
    this.loadInitialCards();
  },
  
  // 載入初始隨機卡片
  loadInitialCards() {
    this.originalCards = this.generateMockCards(); // 保存原始資料
    this.allCards = [...this.originalCards]; // 複製一份作為工作資料
    this.displayRandomCards();
  },
  
  // 產生模擬卡片資料
  generateMockCards() {
    return [
      {
        id: 1,
        name: '滙豐銀行 現金回饋御璽卡',
        bank: '滙豐銀行',
        image: '/assets/card_img/尊御卡_MW.png',
        rewards: [
          { category: '國內消費現金回饋', rate: '1.22%', limit: '' },
          { category: '保險消費現金回饋', rate: '3.88%', limit: '' },
          { category: '旅平險', rate: '2,000萬', limit: '' },
          { category: '年費折抵', rate: '首年免年費', limit: '' }
        ]
      },
      {
        id: 2,
        name: '富邦 J卡',
        bank: '富邦銀行',
        image: '/assets/card_img/J卡.gif',
        rewards: [
          { category: '數位通路消費', rate: '3%', limit: '月上限500元' },
          { category: '一般消費', rate: '0.5%', limit: '無上限' },
          { category: '海外消費', rate: '2.5%', limit: '月上限300元' },
          { category: '年費', rate: '永久免年費', limit: '' }
        ]
      },
      {
        id: 3,
        name: '國泰世華 CUBE卡',
        bank: '國泰世華',
        image: '/assets/card_img/VS91.png',
        rewards: [
          { category: '指定通路消費', rate: '3%', limit: '月上限300元' },
          { category: '一般消費', rate: '0.5%', limit: '無上限' },
          { category: '國外消費', rate: '2%', limit: '月上限200元' },
          { category: '年費', rate: '首年免年費', limit: '' }
        ]
      },
      {
        id: 4,
        name: '中國信託 英雄聯盟卡',
        bank: '中國信託',
        image: '/assets/card_img/VST88-1.png',
        rewards: [
          { category: '遊戲消費', rate: '5%', limit: '月上限200元' },
          { category: '數位娛樂', rate: '3%', limit: '月上限300元' },
          { category: '一般消費', rate: '0.5%', limit: '無上限' },
          { category: '年費', rate: '首年免年費', limit: '' }
        ]
      },
      {
        id: 5,
        name: 'LINE Bank 快點卡',
        bank: 'LINE Bank',
        image: '/assets/card_img/VSB98.png',
        rewards: [
          { category: 'LINE相關消費', rate: '5%', limit: '月上限100元' },
          { category: '指定通路', rate: '2%', limit: '月上限500元' },
          { category: '一般消費', rate: '1%', limit: '無上限' },
          { category: '年費', rate: '永久免年費', limit: '' }
        ]
      },
      {
        id: 6,
        name: '上海商銀 簡單卡',
        bank: '上海商銀',
        image: '/assets/card_img/JST59.png',
        rewards: [
          { category: '指定通路消費', rate: '3%', limit: '月上限200元' },
          { category: '海外消費', rate: '2.5%', limit: '無上限' },
          { category: '一般消費', rate: '0.5%', limit: '無上限' },
          { category: '年費', rate: '首年免年費', limit: '' }
        ]
      },
      {
        id: 7,
        name: '台新銀行 @GOGO卡',
        bank: '台新銀行',
        image: '/assets/card_img/數位生活.gif',
        rewards: [
          { category: '指定通路消費', rate: '3.8%', limit: '月上限300元' },
          { category: '數位消費', rate: '2.8%', limit: '月上限200元' },
          { category: '一般消費', rate: '0.5%', limit: '無上限' },
          { category: '年費', rate: '首年免年費', limit: '' }
        ]
      },
      {
        id: 8,
        name: '玉山銀行 U Bear卡',
        bank: '玉山銀行',
        image: '/assets/card_img/ui_flow_chart.png',
        rewards: [
          { category: '網購消費', rate: '5%', limit: '月上限150元' },
          { category: '超商消費', rate: '3%', limit: '月上限200元' },
          { category: '海外消費', rate: '2.2%', limit: '無上限' },
          { category: '年費', rate: '永久免年費', limit: '' }
        ]
      }
    ];
  },
  
  // 顯示隨機3張卡片
  displayRandomCards() {
    const shuffled = [...this.allCards].sort(() => 0.5 - Math.random());
    this.allCards = shuffled; // 更新為隨機排序後的資料
    this.loadedCount = 3;
    this.displayCards = this.allCards.slice(0, this.loadedCount);
  },
  
  // 銀行選擇變更
  onBankChange() {
    console.log('Bank changed:', this.selectedBank);
  },
  
  // 優惠選擇變更
  onRewardChange() {
    console.log('Reward changed:', this.selectedReward);
  },
  
  // 執行搜尋
  performSearch() {
    if (!this.selectedBank && !this.selectedReward) {
      this.displayRandomCards();
      return;
    }
    
    this.isLoading = true;
    
    // 模擬API呼叫延遲
    setTimeout(() => {
      let filteredCards = [...this.originalCards]; // 每次都從原始資料開始篩選
      
      // 根據銀行篩選
      if (this.selectedBank) {
        const bankNames = {
          'fubon': '富邦銀行',
          'ctbc': '中國信託',
          'cathay': '國泰世華',
          'line': 'LINE Bank',
          'shanghai': '上海商銀'
        };
        
        filteredCards = filteredCards.filter(card => 
          card.bank === bankNames[this.selectedBank]
        );
      }
      
      // 根據優惠類型篩選
      if (this.selectedReward) {
        const rewardTypes = {
          'domestic': ['國內消費', '一般消費', '指定通路'],
          'overseas': ['海外消費', '國外消費'],
          'cashback': ['現金回饋', '消費'],
          'points': ['紅利點數', 'POINT']
        };
        
        const searchTerms = rewardTypes[this.selectedReward] || [];
        filteredCards = filteredCards.filter(card =>
          card.rewards.some(reward =>
            searchTerms.some(term => reward.category.includes(term))
          )
        );
        
        // 將符合條件的優惠排到第一個
        filteredCards = filteredCards.map(card => {
          const matchingRewards = card.rewards.filter(reward =>
            searchTerms.some(term => reward.category.includes(term))
          );
          const otherRewards = card.rewards.filter(reward =>
            !searchTerms.some(term => reward.category.includes(term))
          );
          
          return {
            ...card,
            rewards: [...matchingRewards, ...otherRewards]
          };
        });
      }
      
      // 按照相關性排序（這裡簡化為隨機）
      filteredCards.sort(() => 0.5 - Math.random());
      
      this.allCards = filteredCards; // 更新工作資料
      this.loadedCount = Math.min(3, filteredCards.length); // 重置載入數量
      this.updateDisplayCards();
      this.isLoading = false;
    }, 500);
  },
  
  // 更新顯示的卡片
  updateDisplayCards() {
    this.displayCards = this.allCards.slice(0, this.loadedCount);
  },
  
  // 載入更多卡片
  loadMoreCards() {
    if (this.isLoadingMore || this.loadedCount >= this.allCards.length) {
      return;
    }
    
    this.isLoadingMore = true;
    
    // 模擬載入延遲
    setTimeout(() => {
      this.loadedCount = Math.min(this.loadedCount + this.loadIncrement, this.allCards.length);
      this.updateDisplayCards();
      this.isLoadingMore = false;
    }, 300);
  },
  
  // 檢查是否還有更多卡片可載入
  hasMoreCards() {
    return this.loadedCount < this.allCards.length;
  },
  
  // 滾動監聽處理
  handleScroll(event) {
    const element = event.target;
    const threshold = 100; // 距離底部100px時開始載入
    
    if (element.scrollTop + element.clientHeight >= element.scrollHeight - threshold) {
      this.loadMoreCards();
    }
  },
  
  // 檢查優惠是否符合搜尋條件
  isMatchingReward(reward) {
    if (!this.selectedReward) return false;
    
    const rewardTypes = {
      'domestic': ['國內消費', '一般消費', '指定通路'],
      'overseas': ['海外消費', '國外消費'],
      'cashback': ['現金回饋', '消費'],
      'points': ['紅利點數', 'POINT']
    };
    
    const searchTerms = rewardTypes[this.selectedReward] || [];
    return searchTerms.some(term => reward.category.includes(term));
  }
});
