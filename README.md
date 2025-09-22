# Rewardia - 智能信用卡回饋比較平台

[![React](https://img.shields.io/badge/React-18.2-blue.svg)](https://reactjs.org/)
[![Alpine.js](https://img.shields.io/badge/Alpine.js-3.13-8BC0D0.svg)](https://alpinejs.dev/)
[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7.0-red.svg)](https://redis.io/)
[![Celery](https://img.shields.io/badge/Celery-5.3-green.svg)](https://celeryproject.org/)
[![AI Powered](https://img.shields.io/badge/AI-Gemini-orange)](https://gemini.google.com)
[![spaCy](https://img.shields.io/badge/spaCy-3.8-09A3D5.svg)](https://spacy.io/)
[![Google Cloud](https://img.shields.io/badge/Google_Cloud-Vision-4285F4.svg)](https://cloud.google.com/vision)
[![Selenium](https://img.shields.io/badge/Selenium-4.35-43B02A.svg)](https://selenium.dev/)
[![Chrome Extension](https://img.shields.io/badge/Chrome-Extension-4285F4.svg)](https://developer.chrome.com/docs/extensions/)

# Rewardia 專案簡介

**Rewardia 是一個智能信用卡回饋比較平台，解決用戶在面對複雜信用卡回饋規則時的困惑。透過 Chrome Extension 與自動化爬蟲，為用戶提供即時、準確的信用卡回饋比較服務。**

- **身為「刷卡的人」**：外送、超商、網購，總是不確定要刷哪張才最划算？
- **面對「門檻與上限」**：滿額加碼、通路限定，看半天還是霧煞煞？
- **每次都在猶豫** ：「現在刷這張，會不會錯過更高回饋？」

![Rewardia專案介紹](https://rewardia-web-pic.s3.ap-southeast-2.amazonaws.com/web-pic/readme_0920.jpg)

---

## 環境需求

- **Python 3.13+**
- **Node.js 18+**
- **PostgreSQL 16**
- **Redis 7**
- **Docker & Docker Compose**

---

## 技術架構

### 前端技術

- **Build Tools** : Rollup.js
- **Core Web Languages** : HTML + CSS + JavaScript
- **UI Frameworks & Libraries** : React + Tailwind CSS
- **Lightweight Interaction Frameworks** : HTMX + Alpine.js

### 後端技術

- **Programming Language** : Python 3.13
- **Framework** : Django 5.2
- **API Layer** : Django REST Framework (DRF)

### 爬蟲技術

- **Automation Tools** : Selenium
- **Task Scheduling** : Celery, Redis

### AI 與 NLP 技術

- **AI Services** : Google Gemini API
- **Natural Language Processing (NLP)** : spaCy
- **Image Recognition** : Google Cloud Vision API

### 資料庫與快取

- **Primary Database** : PostgreSQL 16

### 部署

- **Containerization** : Docker, Docker Compose
- **Hosting Platforms** : Cloudflare, Vultr
- **Networking** : NetBird
- **Container Management** : Portainer
- **Reverse Proxy** : Nginx Proxy Manager
- **Cloud Storage** : AWS S3

### 版本控制

- **Version Control System** : Git
- **Repository Hosting** : GitHub

---

## 專案成員

| 成員名稱 | GitHub | 負責內容 |
|----------|--------|----------|
| 莊于申 Ethan | [YSzEthan](https://github.com/YSzEthan/) | 後台排程控制系統、資料清洗與 NLP 分析、網站部署、資料庫設計與架構 |
| 朱怡潔 Yichieh | [yichieh10002](https://github.com/yichieh10002/) | 後台回饋審核系統、前端架構設計、個人卡片功能系統、試算系統、React 前端 for Chrome Extension |
| 張聖晞 Samuel | [legosthes](https://github.com/legosthes/) | 後台卡片控制系統、爬蟲資料擷取功能、Chrome Extension 後端與專用 API、資料庫設計與架構 |
| 游志平 Brad | [ZhiPingYou](https://github.com/ZhiPingYou/) | 會員註冊與登入、首頁搜尋、後台圖片管理系統、前端架構規劃、AI 助理、第三方認證整合、影像辨識 |

---

## Rewardia 使用方式

### 透過 [Rewardia](https://rewardia.net/)，你只需要：

1. **註冊帳號**
2. **選消費場景與金額**
3. **Rewardia 即時計算並排序最佳卡**
4. **一鍵加入持卡清單**
5. **結帳前快速查詢**

## Rewardia 提供

### 核心功能

- **AI 智能助理** ：基於 Google Gemini 的自然語言查詢與個人化推薦
- **即時試算** ：透過「金額 × 通路 × 門檻/上限」公式，一秒看懂回饋
- **精準比對** ：清晰呈現各銀行規則與加碼條件的差異
- **Chrome Extension** ：購物時即時顯示最佳回饋卡片
- **個人化管理** ：收藏卡片、追蹤回饋使用情況

### 解決的痛點

- **回饋規則複雜** ：面對「滿額加碼」、「通路限定」等門檻與上限規則時感到困惑
- **選擇困難** ：外送、超商、網購等消費場景，不確定哪張信用卡最划算
- **錯失優惠** ：每次刷卡時猶豫是否會錯過更高的回饋

---

## Chrome Extension 介紹

### 功能特色

**Rewardia Chrome Extension 是我們的核心產品，讓用戶在購物時獲得即時的回饋建議：**

#### 支援的購物網站

- **電商平台** : momo 購物網、PChome 24h 購物
- **生活服務** : 誠品網路書店、Klook 旅遊平台
- **自動檢測** : 智能識別購物車頁面，自動顯示建議（目前僅適用 momo 購物網）

#### 智能推薦邏輯

- **消費類別分析** : 自動識別商品類別（3C、服飾、書籍等）
- **金額計算** : 即時計算最佳回饋卡片
- **門檻提醒** : 顯示滿額加碼條件與上限
- **個人化建議** : 根據用戶收藏的卡片提供建議

### 安裝與使用

#### 安裝方式

1. **前往 [Chrome Web Store](https://chrome.google.com/webstore)**
2. **搜尋「Rewardia」**
3. **點擊「加到 Chrome」**
4. **開始購物時自動獲得回饋建議！**

#### 使用流程

1. **註冊帳號** : 在 Rewardia 網站註冊並登入
2. **收藏卡片** : 在網站上收藏你擁有的信用卡
3. **開始購物** : 在支援的網站購物
4. **查看建議** : 結帳頁面自動顯示最佳回饋卡片
5. **一鍵應用** : 快速切換到推薦的信用卡

### Rewardia ｜讓你通路、門檻一次搞定，回饋不遺漏。

---