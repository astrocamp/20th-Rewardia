from django.db import models
from django.core.validators import FileExtensionValidator
from PIL import Image
import re


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
        upload_to='',
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
        try:
            has_new_image = self.image and hasattr(self.image, 'file') and self.image.file
        except (FileNotFoundError, OSError):
            # 如果檔案不存在（如 S3 檔案），則不處理圖片
            has_new_image = False

        # 如果有新圖片，先在記憶體中處理，再一次性儲存
        if has_new_image:
            self.process_image_before_save()

        # 執行父類的 save 方法（只儲存一次）
        super().save(*args, **kwargs)

    def format_bank_name(self, bank_name):
        """格式化銀行名稱"""
        bank_patterns = {
            "一銀": "第一",
            "美國": "美國運通",
            "富邦": "富邦"
        }

        for pattern, formatted_name in bank_patterns.items():
            if re.search(pattern, bank_name):
                return formatted_name

        return bank_name if bank_name in CreditCard.Bank.values else "無"

    def process_image_before_save(self):
        """在儲存前處理圖片（記憶體中處理，避免重複儲存）"""
        if self.image:
            try:
                # 檢查是否為 S3 檔案或已存在的檔案
                if not hasattr(self.image, 'file'):
                    return
                from PIL import Image
                from io import BytesIO
                from django.core.files.base import ContentFile

                # 從上傳的檔案讀取圖片
                self.image.seek(0)
                image_data = self.image.read()
                img = Image.open(BytesIO(image_data))

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

                # 處理後的圖片儲存到記憶體
                output = BytesIO()
                img.save(output, 'WEBP', quality=85, optimize=True)
                output.seek(0)

                # 保持原檔案名稱，但更換副檔名為 .webp
                original_name = self.image.name
                if '.' in original_name:
                    name_without_ext = original_name.rsplit('.', 1)[0]
                    new_name = f"{name_without_ext}.webp"
                else:
                    new_name = f"{original_name}.webp"

                # 用處理後的內容替換原檔案
                self.image = ContentFile(output.getvalue(), name=new_name)

            except (FileNotFoundError, OSError, Exception) as e:
                # 如果圖片處理失敗（包括 S3 檔案存取錯誤），保持原檔案
                print(f"圖片處理失敗: {e}")
                pass

