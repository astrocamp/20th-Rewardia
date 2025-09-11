from django.contrib import admin
from django.utils.html import format_html
from .models import CreditCard

@admin.register(CreditCard)
class CreditCardAdmin(admin.ModelAdmin):
    list_display = ['bank', 'name', 'image_preview', 'is_active', 'created_at']
    list_filter = ['bank', 'is_active', 'created_at']
    search_fields = ['name', 'bank']
    list_editable = ['is_active']
    readonly_fields = ['image_preview', 'created_at', 'updated_at']
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('name', 'bank', 'is_active')
        }),
        ('圖片', {
            'fields': ('image', 'image_preview'),
            'description': '上傳信用卡圖片，支援 JPG、PNG、WebP 格式'
        }),
        ('時間記錄', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def image_preview(self, obj):
        """顯示圖片預覽"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 120px; border-radius: 8px;" />',
                obj.image.url
            )
        return "無圖片"
    
    image_preview.short_description = "圖片預覽"
    
    def save_model(self, request, obj, form, change):
        """儲存模型時自動處理圖片"""
        super().save_model(request, obj, form, change)
