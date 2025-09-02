// Related HTML: templates/pages/main.html
export default () => ({
  selectedBank: '',
  selectedReward: '',
  displayCards: [],
  allCards: [],
  originalCards: [], 
  loadedCount: 3, 
  loadIncrement: 1, 
  isLoading: true, // Set to true initially for loading data
  isLoadingMore: false, 
  rewardCategoryMap: {},
  rewardCategoriesChoices: [], // New property for reward choices
  banks: [], // New property for banks
  
  // 使用 API 獲取資料進行初始化
  async init() {
    try {
      const response = await fetch('/api/main-data/');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      
      this.originalCards = data.all_cards_data; 
      this.allCards = [...this.originalCards]; 
      this.rewardCategoryMap = data.reward_category_map;
      this.rewardCategoriesChoices = data.reward_categories_choices; // Populate reward choices
      this.banks = data.banks; // Populate banks from API
      
      this.displayRandomCards();
    } catch (error) {
      console.error("Error fetching initial data:", error);
      // Handle error, e.g., display an error message to the user
    } finally {
      this.isLoading = false;
    }
  },
  
  // 顯示初始的隨機卡片
  displayRandomCards() {
    const shuffled = [...this.allCards].sort(() => 0.5 - Math.random());
    this.allCards = shuffled; 
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
      this.allCards = [...this.originalCards];
      this.loadedCount = Math.min(3, this.allCards.length);
      this.updateDisplayCards();
      return;
    }
    
    this.isLoading = true;
    
    setTimeout(() => {
      let filteredCards = [...this.originalCards]; 
      
      // 根據銀行篩選
      if (this.selectedBank) {
        filteredCards = filteredCards.filter(card => 
          card.bank === this.selectedBank
        );
      }
      
      // 根據優惠類型篩選
      if (this.selectedReward) {
        const selectedCategoryDisplay = this.rewardCategoryMap[this.selectedReward];
        filteredCards = filteredCards.filter(card =>
          card.rewards.some(reward =>
            reward.category.includes(selectedCategoryDisplay)
          )
        );
        
        // 將符合條件的優惠排到第一個
        filteredCards = filteredCards.map(card => {
          const matchingRewards = card.rewards.filter(reward =>
            reward.category.includes(selectedCategoryDisplay)
          );
          const otherRewards = card.rewards.filter(reward =>
            !reward.category.includes(selectedCategoryDisplay)
          );
          
          return {
            ...card,
            rewards: [...matchingRewards, ...otherRewards]
          };
        });
      }
      
      // 按照優惠數值排序（數值最高的優先）
      if (this.selectedReward) {
        filteredCards.sort((a, b) => {
          const aMaxRate = this.getMaxRewardRate(a, this.selectedReward);
          const bMaxRate = this.getMaxRewardRate(b, this.selectedReward);
          return bMaxRate - aMaxRate; 
        });
      } else {
        filteredCards.sort(() => 0.5 - Math.random());
      }
      
      this.allCards = filteredCards; 
      this.loadedCount = Math.min(3, filteredCards.length); 
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
    const threshold = 100; 
    
    if (element.scrollTop + element.clientHeight >= element.scrollHeight - threshold) {
      this.loadMoreCards();
    }
  },
  
  // 檢查優惠是否符合搜尋條件
  isMatchingReward(reward) {
    if (!this.selectedReward) return false;
    const selectedCategoryDisplay = this.rewardCategoryMap[this.selectedReward];
    return reward.category.includes(selectedCategoryDisplay);
  },
  
  // 獲取卡片在特定優惠類型下的最高數值
  getMaxRewardRate(card, selectedRewardCode) {
    if (!selectedRewardCode) return 0;
    const selectedCategoryDisplay = this.rewardCategoryMap[selectedRewardCode];
    const matchingRewards = card.rewards.filter(reward =>
      reward.category.includes(selectedCategoryDisplay)
    );
    
    if (matchingRewards.length === 0) return 0;
    
    const rates = matchingRewards.map(reward => {
      const rateStr = reward.rate;
      const percentMatch = rateStr.match(/(\d+\.?\d*)%/);
      if (percentMatch) {
        return parseFloat(percentMatch[1]);
      }
      return 0;
    });
    
    return Math.max(...rates);
  }
});