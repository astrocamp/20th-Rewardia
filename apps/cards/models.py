from django.db import models
from django.core.validators import FileExtensionValidator
from PIL import Image
import re
import os


class CreditCard(models.Model):
    # 信用卡資訊

    class Bank(models.TextChoices):
        滙豐 = "滙豐"
        中國 = "中國信託"
        國泰 = "國泰"
        玉山 = "玉山"
        台新 = "台新"
        富邦 = "富邦"
        第一 = "第一"
        合庫 = "合庫"
        兆豐 = "兆豐"
        永豐 = "永豐"
        遠東 = "遠東"
        凱基 = "凱基"
        聯邦 = "聯邦"
        星展 = "星展"
        樂天 = "樂天"
        彰化 = "彰化"
        華南 = "華南"
        新光 = "新光"
        上海 = "上海商銀"
        美國 = "美國運通"
        渣打 = "渣打"
        陽信 = "陽信"
        LineBank = "Line Bank"
        將來 = "將來"
        元大 = "元大"
        台中 = "台中"
        王道 = "王道"
        無 = "無"

    name = models.CharField("信用卡名稱", max_length=50)
    bank = models.CharField("銀行名稱", max_length=15)
    image = models.ImageField(
        "信用卡圖片", 
        upload_to='credit_cards/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])]
    )
    is_active = models.BooleanField("Is Active", default=True)
    created_at = models.DateTimeField("Created At", auto_now_add=True)
    updated_at = models.DateTimeField("Updated At", auto_now=True)

    class Meta:
        db_table = "credit_cards"
        verbose_name = "Credit Card"
        verbose_name_plural = "Credit Cards"
        indexes = [
            models.Index(fields=["bank", "is_active"], name="cards_bank_active_idx")
        ]

    def __str__(self):
        return f"{self.bank} {self.name}"

    def save(self, *args, **kwargs):
        self.bank = self.format_bank_name(self.bank)
        
        # 檢查是否有新圖片上傳
        has_new_image = self.image and hasattr(self.image, 'file')
        
        # 先執行父類的 save 方法
        super().save(*args, **kwargs)
        
        # 只有在有新圖片時才進行處理
        if has_new_image:
            # 圖片處理：調整大小、格式轉換、壓縮
            self.resize_image()

    def format_bank_name(self, bank_name):
        if re.search("一銀", bank_name):
            return "第一"
        if re.search("美國", bank_name):

            return "美國運通"
        if bank_name not in CreditCard.Bank.values:
            return "無"
        return bank_name

    def resize_image(self):
        """圖片處理：調整大小、格式轉換、壓縮"""
        if self.image:
            try:
                from django.conf import settings
                if getattr(settings, 'USE_S3', False):
                    # 使用 S3 時，從 BytesIO 讀取
                    from io import BytesIO
                    self.image.seek(0)
                    image_data = self.image.read()
                    img = Image.open(BytesIO(image_data))
                else:
                    # 本地儲存時，使用檔案路徑
                    img = Image.open(self.image.path)
                
                # 設定目標尺寸
                target_width = 300
                target_height = 180
                
                # 保持比例調整大小
                img.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
                
                # 轉換為 RGB 模式
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 儲存處理後的圖片
                if getattr(settings, 'USE_S3', False):
                    # S3 儲存
                    from io import BytesIO
                    from django.core.files.base import ContentFile
                    output = BytesIO()
                    img.save(output, 'JPEG', quality=85, optimize=True)
                    output.seek(0)
                    content = ContentFile(output.getvalue())
                    self.image.save(
                        self.image.name,
                        content,
                        save=False
                    )
                else:
                    # 本地儲存
                    img.save(
                        self.image.path, 
                        'JPEG', 
                        quality=85,
                        optimize=True
                    )
                
                    
            except Exception as e:
                print(f"圖片處理錯誤: {e}")
