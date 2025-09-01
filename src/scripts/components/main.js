// Related HTML: templates/pages/main.html
export default () => ({
  selectedBank: '',
  selectedReward: '',
  displayCards: [],
  allCards: [],
  currentPage: 1,
  itemsPerPage: 3,
  totalPages: 1,
  isLoading: false,
  
  // 初始化假資料
  init() {
    this.loadInitialCards();
  },
  
  // 載入初始隨機卡片
  loadInitialCards() {
    this.allCards = this.generateMockCards();
    this.displayRandomCards();
  },
  
  // 產生模擬卡片資料
  generateMockCards() {
    return [
      {
        id: 1,
        name: '滙豐銀行 現金回饋御璽卡',
        bank: '滙豐銀行',
        image: 'https://via.placeholder.com/320x200/2060B9/FFFFFF?text=HSBC',
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
        image: 'https://via.placeholder.com/320x200/FF6B6B/FFFFFF?text=FUBON',
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
        image: 'https://via.placeholder.com/320x200/4ECDC4/FFFFFF?text=CATHAY',
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
        image: 'https://via.placeholder.com/320x200/45B7D1/FFFFFF?text=CTBC',
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
        image: 'https://via.placeholder.com/320x200/00C851/FFFFFF?text=LINE',
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
        image: 'https://via.placeholder.com/320x200/FF9500/FFFFFF?text=SCS',
        rewards: [
          { category: '指定通路消費', rate: '3%', limit: '月上限200元' },
          { category: '海外消費', rate: '2.5%', limit: '無上限' },
          { category: '一般消費', rate: '0.5%', limit: '無上限' },
          { category: '年費', rate: '首年免年費', limit: '' }
        ]
      }
    ];
  },
  
  // 顯示隨機3張卡片
  displayRandomCards() {
    const shuffled = [...this.allCards].sort(() => 0.5 - Math.random());
    this.displayCards = shuffled.slice(0, 3);
    this.updatePagination();
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
      let filteredCards = [...this.allCards];
      
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
      
      this.allCards = filteredCards;
      this.currentPage = 1;
      this.updateDisplayCards();
      this.isLoading = false;
    }, 500);
  },
  
  // 更新顯示的卡片
  updateDisplayCards() {
    const startIndex = (this.currentPage - 1) * this.itemsPerPage;
    const endIndex = startIndex + this.itemsPerPage;
    this.displayCards = this.allCards.slice(startIndex, endIndex);
    this.updatePagination();
  },
  
  // 更新分頁資訊
  updatePagination() {
    this.totalPages = Math.ceil(this.allCards.length / this.itemsPerPage);
  },
  
  // 上一頁
  prevPage() {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.updateDisplayCards();
    }
  },
  
  // 下一頁
  nextPage() {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
      this.updateDisplayCards();
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
