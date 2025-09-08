// Related HTML: templates/pages/main.html
export default () => ({
  selectedBank: '',
  selectedReward: '',
  searchKeyword: '',
  allCards: [], // 主要卡片資料陣列
  originalCards: [], // 原始資料備份
  loadedCount: 9, // 載入的卡片數量（網格9張，列表3張）
  loadIncrement: 6, // 網格視圖每次載入6張，列表視圖每次載入1張
  isLoading: true,
  isLoadingMore: false,
  rewardCategoryMap: {},
  rewardCategoriesChoices: [],
  banks: [],
  viewMode: 'grid', // 'grid' for card view (畫面b), 'list' for search results (畫面a)
  
  // 使用 API 獲取資料進行初始化
  async init() {
    try {
      const response = await fetch('/api/main-data/');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      
      this.originalCards = data.all_cards_data;
      this.rewardCategoryMap = data.reward_category_map;
      this.rewardCategoriesChoices = data.reward_categories_choices;
      this.banks = data.banks;
      
      this.initializeView();
    } catch (error) {
      console.error("Error fetching initial data:", error);
    } finally {
      this.isLoading = false;
    }
  },
  
  // 初始化視圖（統一的初始化邏輯）
  initializeView() {
    this.resetToGridView();
  },
  
  // 重置到網格視圖
  resetToGridView() {
    const shuffled = [...this.originalCards].sort(() => 0.5 - Math.random());
    this.allCards = shuffled;
    this.loadedCount = Math.min(9, this.allCards.length);
    this.viewMode = 'grid';
  },
  
  // 載入更多卡片（統一邏輯）
  loadMoreCards() {
    if (this.isLoadingMore || this.loadedCount >= this.allCards.length) {
      return;
    }
    
    this.isLoadingMore = true;
    
    setTimeout(() => {
      const increment = this.viewMode === 'grid' ? 6 : 1;
      this.loadedCount = Math.min(this.loadedCount + increment, this.allCards.length);
      this.isLoadingMore = false;
    }, 300);
  },
  
  // 檢查是否還有更多卡片（統一邏輯）
  hasMoreCards() {
    return this.loadedCount < this.allCards.length;
  },
  
  // 滾動監聽處理（統一邏輯）
  handleScroll(event) {
    const element = event.target;
    const threshold = 100;
    
    if (element.scrollTop + element.clientHeight >= element.scrollHeight - threshold) {
      this.loadMoreCards();
    }
  },
  
  // 銀行選擇變更
  onBankChange() {
    // 當使用下拉選單時，清空關鍵字搜尋欄位
    this.searchKeyword = '';
    this.performSearch();
  },
  
  // 優惠選擇變更
  onRewardChange() {
    // 當使用下拉選單時，清空關鍵字搜尋欄位
    this.searchKeyword = '';
    this.performSearch();
  },
  
  // 執行搜尋
  performSearch() {
    const hasSearchCriteria = this.selectedBank || this.selectedReward || this.searchKeyword.trim();
    
    if (!hasSearchCriteria) {
      this.resetToGridView();
      return;
    }
    
    this.viewMode = 'list';
    this.isLoading = true;
    
    setTimeout(() => {
      let filteredCards = [...this.originalCards];
      
      // 依序套用篩選條件
      if (this.selectedBank) {
        filteredCards = filteredCards.filter(card => card.bank === this.selectedBank);
      }
      
      if (this.selectedReward) {
        const selectedCategoryDisplay = this.rewardCategoryMap[this.selectedReward];
        filteredCards = filteredCards.filter(card =>
          card.rewards.some(reward => reward.category.includes(selectedCategoryDisplay))
        );
      }

      if (this.searchKeyword?.trim()) {
        // 當使用關鍵字搜尋時，清空其他選擇器
        this.selectedBank = '';
        this.selectedReward = '';
        
        const keyword = this.searchKeyword.trim().toLowerCase();
        filteredCards = filteredCards.filter(card => {
          // 搜尋銀行名稱
          const bankMatch = card.bank.toLowerCase().includes(keyword);
          
          // 搜尋卡片名稱
          const cardNameMatch = card.name.toLowerCase().includes(keyword);
          
          // 搜尋回饋分類的 category、scope、reward_type
          const rewardMatch = card.rewards.some(reward => 
            reward.category.toLowerCase().includes(keyword) ||
            reward.scope.toLowerCase().includes(keyword) ||
            reward.reward_type.toLowerCase().includes(keyword)
          );
          
          // 只要任一項目匹配就回傳 true
          return bankMatch || cardNameMatch || rewardMatch;
        });
      }

      // 重新排列優惠順序（符合條件的排前面）
      if (this.selectedReward) {
        const selectedCategoryDisplay = this.rewardCategoryMap[this.selectedReward];
        filteredCards = filteredCards.map(card => {
          const matchingRewards = card.rewards.filter(reward =>
            reward.category.includes(selectedCategoryDisplay)
          );
          const otherRewards = card.rewards.filter(reward =>
            !reward.category.includes(selectedCategoryDisplay)
          );
          
          // 對符合條件的回饋進行去重和排序
          const deduplicatedMatchingRewards = this.deduplicateRewardsByCategory(matchingRewards);
          
          return { ...card, rewards: [...deduplicatedMatchingRewards, ...otherRewards] };
        });
        
        // 按優惠數值排序（最高到最低）
        filteredCards.sort((a, b) => {
          const aMaxRate = this.getMaxRewardRate(a, this.selectedReward);
          const bMaxRate = this.getMaxRewardRate(b, this.selectedReward);
          return bMaxRate - aMaxRate;
        });
      } else if (this.searchKeyword?.trim()) {
        // 關鍵字搜尋時，對每張卡片的回饋進行去重和排序
        const keyword = this.searchKeyword.trim().toLowerCase();
        filteredCards = filteredCards.map(card => {
          const deduplicatedRewards = this.deduplicateRewardsByCategory(card.rewards);
          
          // 優先顯示符合搜尋條件的回饋
          const matchingRewards = deduplicatedRewards.filter(reward => 
            reward.category.toLowerCase().includes(keyword) ||
            reward.scope.toLowerCase().includes(keyword) ||
            reward.reward_type.toLowerCase().includes(keyword)
          );
          const otherRewards = deduplicatedRewards.filter(reward => 
            !reward.category.toLowerCase().includes(keyword) &&
            !reward.scope.toLowerCase().includes(keyword) &&
            !reward.reward_type.toLowerCase().includes(keyword)
          );
          
          return { ...card, rewards: [...matchingRewards, ...otherRewards] };
        });
        
        // 按符合搜尋條件的最高回饋率排序
        filteredCards.sort((a, b) => {
          const aMaxRate = this.getMaxRewardRateFromMatchingRewards(a, keyword);
          const bMaxRate = this.getMaxRewardRateFromMatchingRewards(b, keyword);
          return bMaxRate - aMaxRate;
        });
      } else {
        // 沒有篩選條件時，對每張卡片的回饋進行去重和排序
        filteredCards = filteredCards.map(card => {
          const deduplicatedRewards = this.deduplicateRewardsByCategory(card.rewards);
          return { ...card, rewards: deduplicatedRewards };
        });
        
        // 隨機排列
        filteredCards.sort(() => 0.5 - Math.random());
      }
      
      this.allCards = filteredCards;
      this.loadedCount = Math.min(3, filteredCards.length);
      this.isLoading = false;
    }, 500);
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
      // 處理區間格式 "1.5%-3.0%" 或單一格式 "2.0%"
      const rangeMatch = rateStr.match(/(\d+\.?\d*)%-(\d+\.?\d*)%/);
      const singleMatch = rateStr.match(/(\d+\.?\d*)%/);
      
      if (rangeMatch) {
        // 取區間的最大值
        return Math.max(parseFloat(rangeMatch[1]), parseFloat(rangeMatch[2]));
      } else if (singleMatch) {
        return parseFloat(singleMatch[1]);
      }
      return 0;
    });
    
    return Math.max(...rates);
  },
  
  // 獲取卡片所有回饋中的最高數值（用於關鍵字搜尋排序）
  getMaxRewardRateFromAllRewards(card) {
    if (!card.rewards || card.rewards.length === 0) return 0;
    
    const rates = card.rewards.map(reward => {
      const rateStr = reward.rate;
      // 處理區間格式 "1.5%-3.0%" 或單一格式 "2.0%"
      const rangeMatch = rateStr.match(/(\d+\.?\d*)%-(\d+\.?\d*)%/);
      const singleMatch = rateStr.match(/(\d+\.?\d*)%/);
      
      if (rangeMatch) {
        // 取區間的最大值
        return Math.max(parseFloat(rangeMatch[1]), parseFloat(rangeMatch[2]));
      } else if (singleMatch) {
        return parseFloat(singleMatch[1]);
      }
      return 0;
    });
    
    return Math.max(...rates);
  },
  
  // 獲取卡片符合搜尋條件的回饋中的最高數值
  getMaxRewardRateFromMatchingRewards(card, keyword) {
    if (!card.rewards || card.rewards.length === 0) return 0;
    
    const matchingRewards = card.rewards.filter(reward => 
      reward.category.toLowerCase().includes(keyword) ||
      reward.scope.toLowerCase().includes(keyword) ||
      reward.reward_type.toLowerCase().includes(keyword)
    );
    
    if (matchingRewards.length === 0) return 0;
    
    const rates = matchingRewards.map(reward => {
      const rateStr = reward.rate;
      const rangeMatch = rateStr.match(/(\d+\.?\d*)%-(\d+\.?\d*)%/);
      const singleMatch = rateStr.match(/(\d+\.?\d*)%/);
      
      if (rangeMatch) {
        return Math.max(parseFloat(rangeMatch[1]), parseFloat(rangeMatch[2]));
      } else if (singleMatch) {
        return parseFloat(singleMatch[1]);
      }
      return 0;
    });
    
    return Math.max(...rates);
  },
  
  // 根據類別+範圍去重回饋項目，保留數值最高的
  deduplicateRewardsByCategory(rewards) {
    if (!rewards || rewards.length === 0) return [];
    
    // 按類別+範圍組合分組
    const groupedRewards = {};
    
    rewards.forEach(reward => {
      const key = `${reward.category}-${reward.scope}`;
      if (!groupedRewards[key]) {
        groupedRewards[key] = [];
      }
      groupedRewards[key].push(reward);
    });
    
    // 對每個類別+範圍組合，保留數值最高的回饋
    const deduplicatedRewards = [];
    
    Object.keys(groupedRewards).forEach(key => {
      const categoryRewards = groupedRewards[key];
      
      // 計算每個回饋的數值
      const rewardsWithRates = categoryRewards.map(reward => {
        const rateStr = reward.rate;
        const rangeMatch = rateStr.match(/(\d+\.?\d*)-(\d+\.?\d*)%/);
        const singleMatch = rateStr.match(/(\d+\.?\d*)%/);
        
        let rate = 0;
        if (rangeMatch) {
          // 取區間的最大值
          rate = Math.max(parseFloat(rangeMatch[1]), parseFloat(rangeMatch[2]));
        } else if (singleMatch) {
          rate = parseFloat(singleMatch[1]);
        }
        
        return { ...reward, calculatedRate: rate };
      });
      
      // 按數值排序，取最高的
      rewardsWithRates.sort((a, b) => b.calculatedRate - a.calculatedRate);
      const bestReward = rewardsWithRates[0];
      
      // 移除 calculatedRate 屬性
      delete bestReward.calculatedRate;
      deduplicatedRewards.push(bestReward);
    });
    
    // 按數值排序（最高到最低）
    deduplicatedRewards.sort((a, b) => {
      const aRate = this.getRewardRate(a);
      const bRate = this.getRewardRate(b);
      return bRate - aRate;
    });
    
    return deduplicatedRewards;
  },
  
  // 獲取單一回饋的數值
  getRewardRate(reward) {
    const rateStr = reward.rate;
    const rangeMatch = rateStr.match(/(\d+\.?\d*)%-(\d+\.?\d*)%/);
    const singleMatch = rateStr.match(/(\d+\.?\d*)%/);
    
    if (rangeMatch) {
      // 取區間的最大值
      return Math.max(parseFloat(rangeMatch[1]), parseFloat(rangeMatch[2]));
    } else if (singleMatch) {
      return parseFloat(singleMatch[1]);
    }
    return 0;
  }
});