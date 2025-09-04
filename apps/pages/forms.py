from django import forms
from apps.cards.models import CreditCard


class RewardCalculatorForm(forms.Form):
    """回饋計算表單"""

    bank_select = forms.IntegerField(
        required=True, error_messages={"required": "請選擇銀行"}
    )

    card_select = forms.IntegerField(
        required=True, error_messages={"required": "請選擇信用卡"}
    )

    category_select = forms.ChoiceField(
        choices=[("ONLINE", "網購"), ("CVS", "超商"), ("GAS", "加油")],
        required=True,
        error_messages={"required": "請選擇消費類別"},
    )

    scope_select = forms.CharField(
        max_length=50, required=True, error_messages={"required": "請選擇消費種類"}
    )

    amount_input = forms.DecimalField(
        min_value=0.01,
        max_digits=10,
        decimal_places=2,
        required=True,
        error_messages={
            "required": "請輸入消費金額",
            "min_value": "消費金額必須大於0元",
            "invalid": "請輸入有效的金額",
        },
    )

    def clean_card_select(self):
        """驗證信用卡是否存在且有效"""
        card_id = self.cleaned_data["card_select"]
        try:
            card = CreditCard.objects.get(id=card_id, is_active=True)
            return card_id
        except CreditCard.DoesNotExist:
            raise forms.ValidationError("選擇的信用卡不存在或已停用")

    def clean_amount_input(self):
        """額外驗證金額範圍"""
        amount = self.cleaned_data["amount_input"]
        if amount > 1000000:
            raise forms.ValidationError("單筆消費金額不能超過1,000,000元")
        return amount
