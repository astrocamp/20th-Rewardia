# 🎨 圖示組件庫使用說明

## 📁 檔案位置
```
templates/components/icons/icon.html
```

## 🚀 使用方法

### 基本語法
```html
{% include 'components/icons/icon.html' with name="圖示名稱" %}
```

### 完整參數
```html
{% include 'components/icons/icon.html' with 
  name="圖示名稱"
  size="尺寸大小"
  class="額外CSS類別"
  color="顏色樣式"
%}
```

## 🎯 支援的圖示

### 1. 眼睛圖示 (Password Visibility)
```html
<!-- 密碼可見 -->
{% include 'components/icons/icon.html' with name="eye" %}

<!-- 密碼隱藏 -->
{% include 'components/icons/icon.html' with name="eye-off" %}
```

### 2. 功能特色圖示
```html
<!-- 智慧推薦系統 -->
{% include 'components/icons/icon.html' with name="lightbulb" size="w-8 h-8" class="text-blue-600" %}

<!-- 即時優惠提醒 -->
{% include 'components/icons/icon.html' with name="clock" size="w-8 h-8" class="text-green-600" %}
```

### 3. 導航圖示
```html
<!-- FAQ展開箭頭 -->
{% include 'components/icons/icon.html' with name="arrow-down" class="faq-arrow-icon" %}

<!-- FAQ收合箭頭 -->
{% include 'components/icons/icon.html' with name="arrow-up" class="faq-arrow-icon" %}
```

### 4. 社交媒體圖示
```html
<!-- Google登入 -->
{% include 'components/icons/icon.html' with name="google" %}
```

## 📏 尺寸參數

### 預設尺寸
- 預設: `w-6 h-6` (24x24px)

### 常用尺寸
```html
<!-- 小圖示 -->
{% include 'components/icons/icon.html' with name="eye" size="w-4 h-4" %}

<!-- 中圖示 (預設) -->
{% include 'components/icons/icon.html' with name="eye" size="w-6 h-6" %}

<!-- 大圖示 -->
{% include 'components/icons/icon.html' with name="eye" size="w-8 h-8" %}

<!-- 超大圖示 -->
{% include 'components/icons/icon.html' with name="eye" size="w-12 h-12" %}
```

## 🎨 樣式參數

### 顏色樣式
```html
<!-- 使用 currentColor (預設) -->
{% include 'components/icons/icon.html' with name="eye" %}

<!-- 自定義顏色 -->
{% include 'components/icons/icon.html' with name="lightbulb" class="text-blue-600" %}

<!-- 懸停效果 -->
{% include 'components/icons/icon.html' with name="eye" class="text-gray-600 hover:text-blue-600" %}
```

### 額外樣式
```html
<!-- 添加邊框 -->
{% include 'components/icons/icon.html' with name="eye" class="border border-gray-300 rounded p-1" %}

<!-- 背景色 -->
{% include 'components/icons/icon.html' with name="lightbulb" class="bg-blue-100 p-2 rounded-full" %}

<!-- 動畫效果 -->
{% include 'components/icons/icon.html' with name="arrow-down" class="transition-transform duration-200" %}
```

## 🔄 替換範例

### 原本的SVG
```html
<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
</svg>
```

### 替換後
```html
{% include 'components/icons/icon.html' with name="eye" %}
```

## 📋 圖示清單

| 圖示名稱 | 功能描述 | 使用位置 | 預設樣式 |
|---------|---------|---------|---------|
| `eye` | 密碼可見 | 登入/註冊頁面 | `w-6 h-6`, `stroke="currentColor"` |
| `eye-off` | 密碼隱藏 | 登入/註冊頁面 | `w-6 h-6`, `stroke="currentColor"` |
| `lightbulb` | 智慧推薦 | 下載頁面 | `w-6 h-6`, `stroke="currentColor"` |
| `clock` | 即時提醒 | 下載頁面 | `w-6 h-6`, `stroke="currentColor"` |
| `arrow-down` | 向下箭頭 | FAQ組件 | `w-6 h-6`, `stroke="currentColor"` |
| `arrow-up` | 向上箭頭 | FAQ組件 | `w-6 h-6`, `stroke="currentColor"` |
| `google` | Google圖示 | 認證組件 | `w-6 h-6`, 多色填充 |

## ⚠️ 注意事項

1. **圖示名稱**: 必須完全匹配，區分大小寫
2. **尺寸參數**: 使用 Tailwind CSS 的尺寸類別
3. **樣式參數**: 可以組合多個 CSS 類別
4. **預設值**: 如果參數未提供，會使用預設值
5. **錯誤處理**: 未知圖示名稱會顯示預設佔位符

## 🆕 添加新圖示

要添加新圖示，請在 `icon.html` 檔案中添加新的 `elif` 條件：

```html
{% elif name == "new-icon" %}
  <svg class="icon {{ size|default:'w-6 h-6' }} {{ class|default:'' }}" 
       viewBox="0 0 24 24" 
       fill="none" 
       stroke="currentColor">
    <!-- SVG 路徑 -->
  </svg>
```
