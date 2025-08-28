import Alpine from 'alpinejs';
import 'htmx.org';

import faq from './components/faq.js';
import login from './components/login.js';
import register from './components/register.js';
import subscribe from './components/subscribe.js';

window.Alpine = Alpine;

Alpine.data('faq_accordion', faq);
Alpine.data('login_form', login);
Alpine.data('register_form', register);
Alpine.data('subscribe_form', subscribe);

// 🎯 卡片表單的 Alpine.js 功能 - 修正版本
Alpine.data('card_form', (config = {}) => ({
  // 📝 資料狀態
  selectedBank: config.initialBankId || '',     // 目前選擇的銀行
  selectedCard: config.initialCardId || '',     // 目前選擇的卡片
  allCards: config.allCards || [],              // 所有卡片資料（從 Django 傳入）
  availableCards: [],                           // 可選的卡片（根據銀行篩選）
  
  // 🚀 初始化：頁面載入時執行
  init() {
    console.log('🎯 卡片表單初始化');
    console.log('📊 接收到的設定:', { allCards: this.allCards, initialBankId: this.selectedBank, initialCardId: this.selectedCard });
    
    // 🔍 檢查卡片資料是否正確
    if (this.allCards.length === 0) {
      console.error('❌ 沒有卡片資料！請檢查 Django 模板是否正確傳遞 cards');
      return;
    }
    
    console.log('✅ 卡片資料載入成功，共', this.allCards.length, '張卡片');
    
    // 如果有初始銀行（編輯模式），立即篩選卡片
    if (this.selectedBank) {
      console.log('📝 編輯模式 - 初始銀行ID:', this.selectedBank);
      this.filterCardsByBank(this.selectedBank);
    } else {
      console.log('➕ 新增模式 - 等待用戶選擇銀行');
    }
  },
  
  // 🏦 當銀行選擇改變時（重要！）
  onBankChange() {
    console.log('🏦 銀行選擇改變事件觸發');
    console.log('🏦 新選擇的銀行ID:', this.selectedBank);
    
    if (this.selectedBank) {
      console.log('✅ 有選擇銀行，開始篩選卡片');
      // 🔄 重要：先清除之前選擇的卡片
      this.selectedCard = '';
      // 有選擇銀行：篩選該銀行的卡片
      this.filterCardsByBank(this.selectedBank);
    } else {
      console.log('❌ 沒有選擇銀行，清空卡片選項');
      // 沒有選擇銀行：清空卡片選項
      this.availableCards = [];
      this.selectedCard = '';
    }
  },
  
  // 🔍 篩選指定銀行的卡片（核心邏輯）
  filterCardsByBank(bankId) {
    console.log('🔍 開始篩選 - 銀行ID:', bankId);
    console.log('🔍 可用的所有卡片:', this.allCards);
    
    // 📋 詳細檢查每張卡片
    console.log('🔍 檢查每張卡片的銀行ID:');
    this.allCards.forEach(card => {
      console.log(`  - 卡片「${card.name}」bankId: ${card.bankId} (型別: ${typeof card.bankId})`);
    });
    
    console.log('🔍 要篩選的銀行ID:', bankId, '(型別:', typeof bankId, ')');
    
    // 📋 從所有卡片中篩選出屬於該銀行的卡片
    this.availableCards = this.allCards.filter(card => {
      const match = card.bankId.toString() === bankId.toString();
      console.log(`  ✓ 卡片「${card.name}」是否符合: ${match}`);
      return match;
    });
    
    console.log('✅ 最終篩選結果:', this.availableCards);
    console.log('✅ 篩選出', this.availableCards.length, '張卡片');
  }
}));

Alpine.start();
