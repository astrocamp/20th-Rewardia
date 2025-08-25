# 🔐 認證頁面共用組件使用說明

## 📁 檔案位置
```
templates/components/auth-shared.html
```

## 🎯 組件列表

### 1. 頁面容器 (`page-container`)
```html
{% include 'components/auth-shared.html' with component="page-container" title="登入" %}
  <!-- 這裡放置表單內容 -->
{% include 'components/auth-shared.html' with component="page-container-end" %}
```

### 2. 輸入欄位 (`input-field`)
```html
<!-- 一般輸入欄位 -->
{% include 'components/auth-shared.html' with component="input-field" field_type="email" field_id="email" field_name="email" label_text="電子郵件" placeholder="請輸入您的電子郵件" required=True %}

<!-- 密碼欄位（帶切換按鈕） -->
{% include 'components/auth-shared.html' with component="input-field" field_type="password" field_id="password" field_name="password" label_text="密碼" placeholder="請輸入您的密碼" required=True has_toggle=True alpine_type="passwordVisible ? 'text' : 'password'" toggle_action="togglePassword()" %}

<!-- 確認密碼欄位 -->
{% include 'components/auth-shared.html' with component="input-field" field_type="password" field_id="confirm-password" field_name="password2" label_text="確認密碼" placeholder="請再次輸入您的密碼" required=True has_toggle=True alpine_type="confirmPasswordVisible ? 'text' : 'password'" toggle_action="togglePassword('password_confirm')" %}
```

### 3. 勾選框 (`checkbox`)
```html
<!-- 記住我勾選框 -->
{% include 'components/auth-shared.html' with component="checkbox" checkbox_id="remember-me" checkbox_name="remember-me" label_text="記住我" %}
{% include 'components/auth-shared.html' with component="checkbox-end" %}

<!-- 服務條款勾選框 -->
{% include 'components/auth-shared.html' with component="checkbox" checkbox_id="terms" checkbox_name="terms" required=True %}
我同意網站
<a href="#" id="service-terms" class="register-link">服務條款</a>
及
<a href="#" id="privacy-policy" class="register-link">隱私權政策</a>
{% include 'components/auth-shared.html' with component="checkbox-end" %}
```

### 4. 主要按鈕 (`primary-button`)
```html
{% include 'components/auth-shared.html' with component="primary-button" button_text="登入" %}
{% include 'components/auth-shared.html' with component="primary-button" button_text="建立帳號" %}
```

### 5. 分隔線 (`divider`)
```html
{% include 'components/auth-shared.html' with component="divider" %}
```

### 6. Google 按鈕 (`google-button`)
```html
{% include 'components/auth-shared.html' with component="google-button" action="登入" button_id="google-login" aria_label="使用 Google 帳號登入" %}
{% include 'components/auth-shared.html' with component="google-button" action="註冊" button_id="google-register" aria_label="使用 Google 帳號註冊" %}
```

### 7. 底部連結 (`bottom-link`)
```html
{% include 'components/auth-shared.html' with component="bottom-link" prefix_text="還沒有帳戶？" link_text="立即註冊" link_url="pages:register" %}
{% include 'components/auth-shared.html' with component="bottom-link" prefix_text="已經有帳號？" link_text="登入" link_url="pages:login" suffix_text="去" %}
```

## 📝 完整範例：新的登入頁面

```html
{% extends 'layouts/default.html' %}

{% block title %}登入 - Rewardia{% endblock %}

{% block content %}
{% include 'components/auth-shared.html' with component="page-container" title="登入" %}

<!-- 主要登入表單 -->
<form class="space-y-5" x-data="loginForm" @submit.prevent="submitForm()">
  <!-- 電子郵件欄位 -->
  {% include 'components/auth-shared.html' with component="input-field" field_type="email" field_id="email" field_name="email" label_text="電子郵件" placeholder="請輸入您的電子郵件" required=True %}

  <!-- 密碼欄位 -->
  {% include 'components/auth-shared.html' with component="input-field" field_type="password" field_id="password" field_name="password" label_text="密碼" placeholder="請輸入您的密碼" required=True has_toggle=True alpine_type="passwordVisible ? 'text' : 'password'" toggle_action="togglePassword()" %}

  <!-- 記住我和忘記密碼 -->
  {% include 'components/auth-shared.html' with component="checkbox" checkbox_id="remember-me" checkbox_name="remember-me" label_text="記住我" %}
  {% include 'components/auth-shared.html' with component="checkbox-end" %}

  <!-- 主要登入按鈕 -->
  {% include 'components/auth-shared.html' with component="primary-button" button_text="登入" %}
</form>

<!-- 分隔線 -->
{% include 'components/auth-shared.html' with component="divider" %}

<!-- Google 登入按鈕 -->
{% include 'components/auth-shared.html' with component="google-button" action="登入" button_id="google-login" aria_label="使用 Google 帳號登入" %}

<!-- 註冊連結 -->
{% include 'components/auth-shared.html' with component="bottom-link" prefix_text="還沒有帳戶？" link_text="立即註冊" link_url="pages:register" %}

{% include 'components/auth-shared.html' with component="page-container-end" %}
{% endblock %}
```

## 📝 完整範例：新的註冊頁面

```html
{% extends 'layouts/default.html' %}

{% block title %}註冊 - Rewardia{% endblock %}

{% block content %}
{% include 'components/auth-shared.html' with component="page-container" title="註冊" %}

<!-- 主要註冊表單 -->
<form class="space-y-5" x-data="registerForm" @submit.prevent="submitForm()">
  <!-- 帳號欄位 -->
  {% include 'components/auth-shared.html' with component="input-field" field_type="text" field_id="username" field_name="username" label_text="帳號" placeholder="請輸入您的帳號" required=True %}

  <!-- 電子郵件欄位 -->
  {% include 'components/auth-shared.html' with component="input-field" field_type="email" field_id="email" field_name="email" label_text="電子郵件" placeholder="請輸入您的電子郵件" required=True %}

  <!-- 密碼欄位 -->
  {% include 'components/auth-shared.html' with component="input-field" field_type="password" field_id="password" field_name="password1" label_text="密碼" placeholder="請輸入您的密碼" required=True has_toggle=True alpine_type="passwordVisible ? 'text' : 'password'" toggle_action="togglePassword('password')" %}

  <!-- 確認密碼欄位 -->
  {% include 'components/auth-shared.html' with component="input-field" field_type="password" field_id="confirm-password" field_name="password2" label_text="確認密碼" placeholder="請再次輸入您的密碼" required=True has_toggle=True alpine_type="confirmPasswordVisible ? 'text' : 'password'" toggle_action="togglePassword('password_confirm')" %}

  <!-- 服務條款勾選框 -->
  {% include 'components/auth-shared.html' with component="checkbox" checkbox_id="terms" checkbox_name="terms" required=True %}
  我同意網站
  <a href="#" id="service-terms" class="register-link">服務條款</a>
  及
  <a href="#" id="privacy-policy" class="register-link">隱私權政策</a>
  {% include 'components/auth-shared.html' with component="checkbox-end" %}

  <!-- 主要註冊按鈕 -->
  {% include 'components/auth-shared.html' with component="primary-button" button_text="建立帳號" %}
</form>

<!-- 分隔線 -->
{% include 'components/auth-shared.html' with component="divider" %}

<!-- Google 註冊按鈕 -->
{% include 'components/auth-shared.html' with component="google-button" action="註冊" button_id="google-register" aria_label="使用 Google 帳號註冊" %}

<!-- 登入連結 -->
{% include 'components/auth-shared.html' with component="bottom-link" prefix_text="已經有帳號？" link_text="登入" link_url="pages:login" suffix_text="去" %}

{% include 'components/auth-shared.html' with component="page-container-end" %}
{% endblock %}
```

## ✅ 優勢

1. **統一管理**: 所有認證相關組件集中在一個檔案
2. **易於維護**: 修改一次，所有頁面同步更新
3. **參數化**: 透過參數控制組件的外觀和行為
4. **可擴展**: 輕鬆添加新的認證頁面
5. **一致性**: 確保所有認證頁面的外觀一致

## 📋 參數說明

### 通用參數
- `component`: 組件名稱（必填）
- `title`: 頁面標題
- `button_text`: 按鈕文字
- `label_text`: 標籤文字
- `placeholder`: 輸入框佔位符
- `required`: 是否必填（True/False）

### 輸入欄位參數
- `field_type`: 輸入類型（text, email, password）
- `field_id`: 輸入框 ID
- `field_name`: 輸入框 name 屬性
- `has_toggle`: 是否有切換按鈕
- `alpine_type`: Alpine.js 動態類型
- `toggle_action`: 切換動作函數

### 勾選框參數
- `checkbox_id`: 勾選框 ID
- `checkbox_name`: 勾選框 name 屬性

### Google 按鈕參數
- `action`: 動作文字（登入/註冊）
- `button_id`: 按鈕 ID
- `aria_label`: 無障礙標籤

### 底部連結參數
- `prefix_text`: 前置文字
- `link_text`: 連結文字
- `link_url`: 連結 URL
- `suffix_text`: 後置文字
