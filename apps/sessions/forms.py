from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError


class UserLoginForm(forms.Form):
    """使用者登入表單"""
    
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': '請輸入您的帳號',
            'id': 'username'
        }),
        label='帳號'
    )
    
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': '請輸入您的密碼',
            'id': 'password'
        }),
        label='密碼'
    )
    
    def clean(self):
        """驗證帳號和密碼"""
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        
        if username and password:
            # 使用 Django 內建的 authenticate 函數驗證
            user = authenticate(username=username, password=password)
            if user is None:
                raise ValidationError('帳號或密碼錯誤，請重新輸入', code='invalid_login')
            elif not user.is_active:
                raise ValidationError('此帳號已被停用，請聯繫管理員', code='inactive_user')
            
            # 將驗證成功的用戶存儲在表單中，供後續使用
            cleaned_data['user'] = user
        
        return cleaned_data
    
    def get_user(self):
        """取得驗證成功的用戶"""
        return self.cleaned_data.get('user')