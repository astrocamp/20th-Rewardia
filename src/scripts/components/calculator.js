// 清空表單函數
function clearForm() {

    document.getElementById('calc_form').reset();


    const cardSelect = document.getElementById('card_select');
    cardSelect.innerHTML = '<option value="" selected disabled>請先選擇銀行，再選擇卡片</option>';

    const categorySelect = document.getElementById('category_select');
    categorySelect.innerHTML = '<option value="" selected disabled>請先選擇卡片</option>';

    const scopeSelect = document.getElementById('scope_select');
    scopeSelect.innerHTML = '<option value="" selected disabled>請先選擇消費類別</option>';


    document.getElementById('result_value').innerHTML = '請選擇欄位進行計算';
}


function scrollToResult() {
    const resultCard = document.querySelector('.result-card');
    if (resultCard) {
        resultCard.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        });
    }
}

// 自動計算函數
function autoCalculate() {
    const form = document.getElementById('calc_form');
    const bankSelect = document.getElementById('bank_select');
    const cardSelect = document.getElementById('card_select');
    const categorySelect = document.getElementById('category_select');
    const scopeSelect = document.getElementById('scope_select');
    const amountInput = document.getElementById('amount_input');

    // 檢查所有必填欄位是否都已填寫
    if (bankSelect && bankSelect.value &&
        cardSelect && cardSelect.value &&
        categorySelect && categorySelect.value &&
        scopeSelect && scopeSelect.value &&
        amountInput && amountInput.value &&
        form && form.checkValidity()) {

        console.log('Auto calculate triggered');

        // 獲取 CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        // 收集表單資料
        const formData = new FormData(form);

        // 使用 fetch API 發送請求
        fetch('/calculate-reward/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
            },
            body: formData
        })
        .then(response => response.text())
        .then(data => {
            // 更新結果顯示
            const resultElement = document.getElementById('result_value');
            if (resultElement) {
                resultElement.innerHTML = data;
            }
        })
        .catch(error => {
            console.error('計算錯誤:', error);
        });
    }
}

// HTMX 支援函數
function triggerCalculation() {
    // 檢查所有必填欄位是否都有值
    const form = document.getElementById('calc_form');
    const amountInput = document.getElementById('amount_input');

    if (form && form.checkValidity() && amountInput && amountInput.value) {
        // 手動觸發 amount_input 的 HTMX 請求
        if (typeof htmx !== 'undefined') {
            htmx.trigger(amountInput, 'input');
        }
    }
}

// 將函數綁定到全域供 HTMX 使用
window.triggerCalculation = triggerCalculation;
window.clearForm = clearForm;
window.scrollToResult = scrollToResult;