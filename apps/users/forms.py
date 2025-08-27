from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re


class UserRegistrationForm(forms.Form):
    """使用者註冊表單"""
    
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': '請輸入帳號',
            'id': 'username'
        }),
        label='帳號'
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': '請輸入電子信箱',
            'id': 'email'
        }),
        label='電子信箱'
    )
    
    password = forms.CharField(
        min_length=8,
        max_length=20,
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': '請輸入密碼',
            'id': 'password'
        }),
        label='密碼'
    )
    
    confirm_password = forms.CharField(
        min_length=8,
        max_length=20,
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': '請再次輸入密碼',
            'id': 'confirm_password'
        }),
        label='確認密碼'
    )
    
    agree_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'checkbox checkbox-primary',
            'id': 'agree_terms'
        }),
        label='我同意網站服務條款'
    )
    
    def clean_username(self):
        """驗證帳號格式"""
        username = self.cleaned_data.get('username')
        
        if not username:
            raise ValidationError('帳號為必填項目')
        
        # 檢查是否只包含數字和英文大小寫，不能有空格
        if not re.match(r'^[a-zA-Z0-9]+$', username):
            raise ValidationError('帳號只能包含英文字母和數字，不能有空格或特殊字元')
        
        # 檢查帳號是否已存在
        if User.objects.filter(username=username).exists():
            raise ValidationError('此帳號已被使用，請選擇其他帳號')
        
        return username
    
    def clean_email(self):
        """驗證電子信箱格式和唯一性"""
        email = self.cleaned_data.get('email')
        
        if not email:
            raise ValidationError('電子信箱為必填項目')
        
        # Django EmailField 已經處理基本格式驗證
        # 檢查信箱是否已存在
        if User.objects.filter(email=email).exists():
            raise ValidationError('此電子信箱已被使用，請使用其他信箱')
        
        return email
    
    def clean_password(self):
        """驗證密碼格式"""
        password = self.cleaned_data.get('password')
        
        if not password:
            raise ValidationError('密碼為必填項目')
        
        # 檢查密碼長度
        if len(password) < 8 or len(password) > 20:
            raise ValidationError('密碼長度必須在 8-20 個字元之間')
        
        # 檢查是否只包含數字和英文大小寫，不能有空格
        if not re.match(r'^[a-zA-Z0-9]+$', password):
            raise ValidationError('密碼只能包含英文字母和數字，不能有空格或特殊字元')
        
        # 檢查是否包含至少一個大寫字母
        if not re.search(r'[A-Z]', password):
            raise ValidationError('密碼必須包含至少一個英文大寫字母')
        
        # 檢查是否包含至少一個小寫字母
        if not re.search(r'[a-z]', password):
            raise ValidationError('密碼必須包含至少一個英文小寫字母')
        
        return password
    
    def clean(self):
        """驗證整個表單，特別是密碼確認"""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        # 檢查密碼確認是否一致
        if password and confirm_password:
            if password != confirm_password:
                raise ValidationError('兩次輸入的密碼不一致，請重新確認')
        
        return cleaned_data
