// Related HTML: templates/pages/main.html
export default () => ({
  selectedBank: '',
  selectedReward: '',
  selectedMerchant: '',
  searchKeyword: '',
  allCards: [], // 主要卡片資料陣列
  originalCards: [], // 原始資料備份
  loadedCount: 12, // 載入的卡片數量（網格12張）
  gridLoadIncrement: 8, // 網格視圖每次載入8張
  listLoadIncrement: 1, // 列表視圖每次載入1張
  isLoadingMore: false,
  rewardCategoryMap: {},
  rewardCategoriesChoices: [],
  banks: [],
  merchants: [],
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
      this.merchants = data.merchants;
      
      this.initializeView();
    } catch (error) {
      if (window.RewardiaLogger) {
        window.RewardiaLogger.error("Error fetching initial data:", error);
      }
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
    this.loadedCount = Math.min(12, this.allCards.length);
    this.viewMode = 'grid';
  },
  
  // 載入更多卡片（統一邏輯）
  loadMoreCards() {
    if (this.isLoadingMore || this.loadedCount >= this.allCards.length) {
      return;
    }
    
    this.isLoadingMore = true;
    
    setTimeout(() => {
      const increment = this.viewMode === 'grid' ? this.gridLoadIncrement : this.listLoadIncrement;
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
  async onRewardChange() {
    // 當使用下拉選單時，清空關鍵字搜尋欄位
    this.searchKeyword = '';
    
    // 清空店家選擇
    this.selectedMerchant = '';
    
    // 如果選擇了優惠類別，動態載入對應的店家選項
    if (this.selectedReward) {
      await this.loadMerchantsByCategory();
    } else {
      // 如果沒有選擇優惠類別，恢復所有店家選項
      this.restoreAllMerchants();
    }
    
    this.performSearch();
  },

  // 店家選擇變更
  onMerchantChange() {
    // 當使用下拉選單時，清空關鍵字搜尋欄位
    this.searchKeyword = '';
    this.performSearch();
  },
  
  // 執行搜尋
  performSearch() {
    const hasSearchCriteria = this.selectedBank || this.selectedReward || this.selectedMerchant || this.searchKeyword.trim();
    
    if (!hasSearchCriteria) {
      this.resetToGridView();
      return;
    }
    
    this.viewMode = 'list';
    
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

      if (this.selectedMerchant) {
        filteredCards = filteredCards.filter(card =>
          card.rewards.some(reward => reward.scope === this.selectedMerchant)
        );
      }

      if (this.searchKeyword?.trim()) {
        // 當使用關鍵字搜尋時，清空其他選擇器
        this.selectedBank = '';
        this.selectedReward = '';
        this.selectedMerchant = '';
        
        const keyword = this.searchKeyword.trim().toLowerCase();
        
        // 檢查是否為銀行搜尋（包含"銀行"）
        const isBankSearch = keyword.includes('銀行');
        // 檢查是否為保險搜尋（包含"人壽"、"保險"）
        const isInsuranceSearch = keyword.includes('人壽') || keyword.includes('保險');
        
        if (keyword === '富邦') {
          // 富邦搜尋：顯示富邦銀行卡片 + 富邦相關回饋
          filteredCards = filteredCards.filter(card => {
            // 包含富邦銀行的卡片
            const fubonBankMatch = card.bank.toLowerCase().includes('富邦');
            
            // 或者有富邦相關回饋的卡片
            const fubonRewardMatch = card.rewards.some(reward => 
              reward.scope.toLowerCase().includes('富邦')
            );
            
            return fubonBankMatch || fubonRewardMatch;
          });
        } else if (isBankSearch) {
          // 銀行搜尋：只顯示該銀行的卡片
          const bankName = keyword.replace('銀行', '').trim();
          filteredCards = filteredCards.filter(card => 
            card.bank.toLowerCase().includes(bankName)
          );
        } else if (isInsuranceSearch) {
          // 保險搜尋：顯示有該保險公司回饋的卡片
          filteredCards = filteredCards.filter(card => 
            card.rewards.some(reward => 
              reward.scope.toLowerCase().includes(keyword)
            )
          );
        } else {
          // 一般搜尋邏輯
          filteredCards = filteredCards.filter(card => {
            // 搜尋銀行名稱
            const bankMatch = card.bank.toLowerCase().includes(keyword);
            
            // 搜尋卡片名稱
            const cardNameMatch = card.name.toLowerCase().includes(keyword);
            
            // 搜尋回饋分類的 category、scope、reward_type
            const rewardMatch = card.rewards.some(reward => 
              this.isRewardMatchingKeyword(reward, keyword)
            );
            
            // 只要任一項目匹配就回傳 true
            return bankMatch || cardNameMatch || rewardMatch;
          });
        }
      }

        // 重新排列優惠順序（符合條件的排前面）
        if (this.selectedReward) {
          const selectedCategoryDisplay = this.rewardCategoryMap[this.selectedReward];
          filteredCards = filteredCards.map(card => {
            let matchingRewards, otherRewards;
            
            if (this.selectedMerchant) {
              // 如果同時選擇了優惠類別和店家，優先顯示同時符合兩個條件的回饋
              const bothMatchingRewards = card.rewards.filter(reward =>
                reward.category.includes(selectedCategoryDisplay) && reward.scope === this.selectedMerchant
              );
              const categoryOnlyRewards = card.rewards.filter(reward =>
                reward.category.includes(selectedCategoryDisplay) && reward.scope !== this.selectedMerchant
              );
              const otherRewards = card.rewards.filter(reward =>
                !reward.category.includes(selectedCategoryDisplay)
              );
              
              // 對符合條件的回饋進行去重和排序
              const deduplicatedBothMatching = this.deduplicateRewardsByCategory(bothMatchingRewards);
              const deduplicatedCategoryOnly = this.deduplicateRewardsByCategory(categoryOnlyRewards);
              
              return { ...card, rewards: [...deduplicatedBothMatching, ...deduplicatedCategoryOnly, ...otherRewards] };
            } else {
              // 只選擇優惠類別時，按原來的邏輯處理
              matchingRewards = card.rewards.filter(reward =>
                reward.category.includes(selectedCategoryDisplay)
              );
              otherRewards = card.rewards.filter(reward =>
                !reward.category.includes(selectedCategoryDisplay)
              );
              
              // 對符合條件的回饋進行去重和排序
              const deduplicatedMatchingRewards = this.deduplicateRewardsByCategory(matchingRewards);
              
              return { ...card, rewards: [...deduplicatedMatchingRewards, ...otherRewards] };
            }
          });
        
        // 按優惠數值排序（最高到最低）
        if (this.selectedMerchant) {
          // 如果同時選擇了優惠類別和店家，以該店家的回饋率排序
          filteredCards.sort((a, b) => {
            const aMaxRate = this.getMaxRewardRateFromMerchantAndCategory(a, this.selectedMerchant, this.selectedReward);
            const bMaxRate = this.getMaxRewardRateFromMerchantAndCategory(b, this.selectedMerchant, this.selectedReward);
            return bMaxRate - aMaxRate;
          });
        } else {
          // 只選擇優惠類別時，按優惠類別的回饋率排序
          filteredCards.sort((a, b) => {
            const aMaxRate = this.getMaxRewardRate(a, this.selectedReward);
            const bMaxRate = this.getMaxRewardRate(b, this.selectedReward);
            return bMaxRate - aMaxRate;
          });
        }
      } else if (this.selectedMerchant) {
        // 店家搜尋時，對每張卡片的回饋進行去重和排序
        filteredCards = filteredCards.map(card => {
          const deduplicatedRewards = this.deduplicateRewardsByCategory(card.rewards);
          
          // 優先顯示符合搜尋條件的回饋
          const matchingRewards = deduplicatedRewards.filter(reward => 
            reward.scope === this.selectedMerchant
          );
          const otherRewards = deduplicatedRewards.filter(reward => 
            reward.scope !== this.selectedMerchant
          );
          
          return { ...card, rewards: [...matchingRewards, ...otherRewards] };
        });
        
        // 按符合搜尋條件的最高回饋率排序
        filteredCards.sort((a, b) => {
          const aMaxRate = this.getMaxRewardRateFromMerchant(a, this.selectedMerchant);
          const bMaxRate = this.getMaxRewardRateFromMerchant(b, this.selectedMerchant);
          return bMaxRate - aMaxRate;
        });
      } else if (this.searchKeyword?.trim()) {
        // 關鍵字搜尋時，對每張卡片的回饋進行去重和排序
        const keyword = this.searchKeyword.trim().toLowerCase();
        
        // 關鍵字搜尋邏輯
        filteredCards = filteredCards.map(card => {
          const deduplicatedRewards = this.deduplicateRewardsByCategory(card.rewards);
          
          // 優先顯示符合搜尋條件的回饋
          const matchingRewards = deduplicatedRewards.filter(reward => 
            this.isRewardMatchingKeyword(reward, keyword)
          );
          const otherRewards = deduplicatedRewards.filter(reward => 
            !this.isRewardMatchingKeyword(reward, keyword)
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
      this.loadedCount = Math.min(12, filteredCards.length);
    }, 500);
  },
  
  
  // 通用的獲取最高回饋率方法
  getMaxRewardRateFromRewards(rewards) {
    if (!rewards || rewards.length === 0) return 0;
    const rates = rewards.map(reward => this.getRewardRate(reward));
    return Math.max(...rates);
  },

  // 獲取卡片在特定優惠類型下的最高數值
  getMaxRewardRate(card, selectedRewardCode) {
    if (!selectedRewardCode) return 0;
    const selectedCategoryDisplay = this.rewardCategoryMap[selectedRewardCode];
    const matchingRewards = card.rewards.filter(reward =>
      reward.category.includes(selectedCategoryDisplay)
    );
    return this.getMaxRewardRateFromRewards(matchingRewards);
  },
  
  // 獲取卡片符合搜尋條件的回饋中的最高數值
  getMaxRewardRateFromMatchingRewards(card, keyword) {
    const matchingRewards = card.rewards.filter(reward => 
      this.isRewardMatchingKeyword(reward, keyword)
    );
    return this.getMaxRewardRateFromRewards(matchingRewards);
  },

  // 獲取卡片符合店家搜尋條件的回饋中的最高數值
  getMaxRewardRateFromMerchant(card, merchant) {
    const matchingRewards = card.rewards.filter(reward => 
      reward.scope === merchant
    );
    return this.getMaxRewardRateFromRewards(matchingRewards);
  },

  // 獲取卡片符合特定店家且特定優惠類別的回饋中的最高數值
  getMaxRewardRateFromMerchantAndCategory(card, merchant, selectedRewardCode) {
    if (!selectedRewardCode) return 0;
    
    const selectedCategoryDisplay = this.rewardCategoryMap[selectedRewardCode];
    if (!selectedCategoryDisplay) return 0;
    
    const matchingRewards = card.rewards.filter(reward => 
      reward.scope === merchant && reward.category.includes(selectedCategoryDisplay)
    );
    return this.getMaxRewardRateFromRewards(matchingRewards);
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
    
    Object.values(groupedRewards).forEach(categoryRewards => {
      // 直接使用 getMaxRewardRateFromRewards 來獲取最佳回饋
      const bestReward = categoryRewards.reduce((best, current) => {
        return this.getRewardRate(current) > this.getRewardRate(best) ? current : best;
      });
      deduplicatedRewards.push(bestReward);
    });
    
    // 按數值排序（最高到最低）
    deduplicatedRewards.sort((a, b) => {
      return this.getRewardRate(b) - this.getRewardRate(a);
    });
    
    return deduplicatedRewards;
  },
  
  // 檢查回饋是否符合關鍵字搜尋條件
  isRewardMatchingKeyword(reward, keyword) {
    const lowerKeyword = keyword.toLowerCase();
    return reward.category.toLowerCase().includes(lowerKeyword) ||
           reward.scope.toLowerCase().includes(lowerKeyword) ||
           reward.reward_type.toLowerCase().includes(lowerKeyword);
  },

  // 檢查回饋是否符合當前搜尋條件（用於高亮顯示）
  isMatchingReward(reward) {
    if (this.selectedReward) {
      const selectedCategoryDisplay = this.rewardCategoryMap[this.selectedReward];
      return reward.category.includes(selectedCategoryDisplay);
    }
    if (this.selectedMerchant) {
      return reward.scope === this.selectedMerchant;
    }
    if (this.searchKeyword?.trim()) {
      const keyword = this.searchKeyword.trim().toLowerCase();
      return this.isRewardMatchingKeyword(reward, keyword);
    }
    return false;
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
  },

  // 根據優惠類別載入對應的店家選項
  async loadMerchantsByCategory() {
    try {
      const response = await fetch(`/api/merchants-by-category/?category_code=${this.selectedReward}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      
      // 更新店家選項
      this.merchants = data.merchants || [];
    } catch (error) {
      if (window.RewardiaLogger) {
        window.RewardiaLogger.error("Error loading merchants by category:", error);
      }
      // 發生錯誤時恢復所有店家選項
      this.restoreAllMerchants();
    }
  },

  // 恢復所有店家選項
  async restoreAllMerchants() {
    try {
      const response = await fetch('/api/main-data/');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      
      // 恢復所有店家選項
      this.merchants = data.merchants || [];
    } catch (error) {
      if (window.RewardiaLogger) {
        window.RewardiaLogger.error("Error restoring all merchants:", error);
      }
    }
  }
});