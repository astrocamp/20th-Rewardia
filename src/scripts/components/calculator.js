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

// 確保函數可以被全域調用（給 HTML 中的 onclick 和 HTMX 使用）
window.clearForm = clearForm;
window.scrollToResult = scrollToResult;