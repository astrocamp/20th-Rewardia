# SVG 圖示組件庫

## 概述
此資料夾包含所有獨立的 SVG 圖示組件，每個圖示都是獨立的 HTML 檔案，可以單獨引用或通過統一的 `icon.html` 組件使用。

## 檔案結構
```
templates/components/
├── icon.html                    # 統一圖示組件 (路由到各個 SVG)
├── svgs/                        # SVG 圖示資料夾
│   ├── eye.html                 # 眼睛圖示 (密碼可見)
│   ├── eye-off.html             # 眼睛圖示 (密碼隱藏)
│   ├── google.html              # Google 圖示
│   ├── smart-recommend.html     # 智慧推薦系統
│   ├── real-time-offer.html     # 即時優惠提醒
│   ├── consumption-analysis.html # 消費分析報告
│   └── chevron-down.html        # 向下箭頭圖示
└── icon-backup.html             # 原始 icon.html 備份
```

## 使用方式

### 方式一：通過統一組件 (推薦)
```html
<!-- 使用統一組件 -->
{% include 'components/icon.html' with name="eye" class="w-6 h-6" %}
{% include 'components/icon.html' with name="google" size="w-8 h-8" %}
```

### 方式二：直接引用 SVG 檔案
```html
<!-- 直接引用特定 SVG -->
{% include 'components/svgs/eye.html' with class="w-6 h-6" %}
{% include 'components/svgs/google.html' with size="w-8 h-8" %}
```

## 支援的參數
所有圖示都支援以下參數：
- `class`: 自定義 CSS 類別
- `size`: 圖示大小 (預設值因圖示而異)

## 圖示清單
| 圖示名稱 | 檔案名 | 描述 | 預設大小 |
|---------|--------|------|----------|
| eye | eye.html | 密碼可見圖示 | w-6 h-6 |
| eye-off | eye-off.html | 密碼隱藏圖示 | w-6 h-6 |
| google | google.html | Google 登入圖示 | w-6 h-6 |
| smart-recommend | smart-recommend.html | 智慧推薦系統 | w-6 h-6 |
| real-time-offer | real-time-offer.html | 即時優惠提醒 | w-6 h-6 |
| consumption-analysis | consumption-analysis.html | 消費分析報告 | w-6 h-6 |
| chevron-down | chevron-down.html | 向下箭頭 | w-5 h-5 |

## 新增圖示
1. 在 `svgs/` 資料夾中創建新的 `.html` 檔案
2. 在 `icon.html` 中添加對應的條件判斷
3. 更新此 README 文件

## 備份
原始 `icon.html` 已備份為 `icon-backup.html`，如有問題可以恢復。
