# Create your views here.
from rest_framework.response import Response
from apps.ext_api.serializers import (
    RewardSerializer,
    UserCardSerializer,
    CardSerializer,
)
from apps.rewards.models import RewardCategory
from apps.cards.models import CreditCard
from apps.users.models import UserCard
from rest_framework.decorators import (
    api_view,
    authentication_classes,
)
from django.db.models.functions import Coalesce
from rest_framework.authentication import TokenAuthentication
from django.utils import timezone
from rest_framework import status
import json
import os
import cv2
import numpy as np
import base64
import logging
import re
import requests

os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"
# 設定無頭模式
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# 設定日誌記錄器
logger = logging.getLogger(__name__)


@api_view(["GET"])
def get_card_rewards(request, id):
    card_rewards = (
        RewardCategory.objects.select_related("card")
        .filter(card__id=id)
        .order_by("-max_rate")
    )

    serializer = RewardSerializer(card_rewards, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def get_category_rate(request, bank_name, card_id, category_name):
    reward_category = (
        RewardCategory.objects.select_related("card")
        .filter(
            card__bank=bank_name,
            card__id=card_id,
            category=category_name,
            is_active=True,
        )
        .order_by("-max_rate")
    )
    serializer = RewardSerializer(reward_category, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def get_merchant_rate(request, bank_name, card_id, category_name, scope_name):
    reward_category = (
        RewardCategory.objects.select_related("card")
        .filter(
            card__bank=bank_name,
            card__id=card_id,
            category=category_name,
            scope=scope_name,
            is_active=True,
        )
        .order_by("-max_rate")
    )
    serializer = RewardSerializer(reward_category, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def get_merchant_rewards(request, scope):
    reward_merchant = (
        RewardCategory.objects.select_related("card")
        .filter(scope=scope, is_active=True, card__is_active=True)
        .annotate(rate=Coalesce("max_rate", "min_rate"))
        .order_by("-rate")[:10]
    )
    serializer = RewardSerializer(reward_merchant, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def get_banks(request):
    banks = CreditCard.objects.distinct("bank")
    serializer = CardSerializer(banks, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def get_cards(request, bank):
    cards = CreditCard.objects.filter(bank=bank).order_by("-updated_at")
    serializer = CardSerializer(cards, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
def get_user_cards(request, id):
    if request.user.id != id:
        return Response(status=403)
    user_cards = (
        UserCard.objects.select_related("card").filter(user=id).order_by("-added_date")
    )
    serializer = UserCardSerializer(user_cards, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
def new_user_card(request, id):
    try:
        card = CreditCard.objects.get(id=id)
        user_card = UserCard.objects.update_or_create(
            user=request.user, card=card, defaults={"added_date": timezone.now()}
        )

        return Response(status=201)
    except CreditCard.DoesNotExist:
        return Response(status=404)


@api_view(["DELETE"])
@authentication_classes([TokenAuthentication])
def delete_user_card(request, id):
    try:
        user_card = UserCard.objects.get(user=request.user, card__id=id)
        user_card.delete()

        return Response(status=204)
    except UserCard.DoesNotExist:
        return Response(status=404)


@api_view(["POST"])
def ocr_with_vision(request):
    """
    信用卡卡號 OCR 識別 API
    接收：已裁切的影像文件（前端已處理 ROI）
    回傳：{success, masked, card_number, luhn_valid, full_text}
    """
    try:
        # 檢查是否有影像文件
        if "image" not in request.FILES:
            return Response(
                {"success": False, "error": "缺少影像文件"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 獲取影像文件
        image_file = request.FILES["image"]

        # 處理影像
        result = process_card_image(image_file)

        return Response(result)

    except Exception as e:
        logger.error(f"OCR API 錯誤: {str(e)}", exc_info=True)
        return Response(
            {"success": False, "error": f"處理失敗: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def process_card_image(image_file):
    """
    處理信用卡影像：影像前處理 + OCR
    前端已裁切 ROI，後端直接處理
    """
    try:
        # 1. 讀取影像
        image_bytes = image_file.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError("無法讀取影像")

        # 2. 影像前處理
        processed_image = preprocess_image(image)

        # 3. OCR 識別
        ocr_result = perform_ocr(processed_image)
        if ocr_result is None:
            return {"success": False, "error": "OCR 處理失敗"}

        card_number = ocr_result.get("card_number")
        full_text = ocr_result.get("full_text", "")

        # 4. 格式化卡號
        formatted_card_number = format_card_number(card_number) if card_number else None

        # 檢查卡號格式化是否成功
        if formatted_card_number is None and card_number:
            return {"success": False, "error": "卡號長度不足，請重新拍照"}

        return {
            "success": True,
            "masked": "",
            "card_number": formatted_card_number,
            "luhn_valid": None,
            "full_text": full_text,  # 新增：用於錯誤回補
        }

    except Exception as e:
        logger.error(f"影像處理錯誤: {str(e)}", exc_info=True)
        raise


def preprocess_image(image):
    """
    影像前處理：CLAHE、去噪、銳化、傾斜校正、二值化
    """
    try:
        # 轉換為灰階
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # 1. CLAHE 對比度限制自適應直方圖均衡化
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # 2. 去噪
        denoised = cv2.fastNlMeansDenoising(enhanced, None, 10, 7, 21)

        # 3. 銳化
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        sharpened = cv2.filter2D(denoised, -1, kernel)

        # 4. 傾斜校正（簡單版本）
        corrected = correct_skew(sharpened)

        # 5. 二值化
        _, binary = cv2.threshold(
            corrected, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        logger.info("影像前處理完成")
        return binary

    except Exception as e:
        logger.error(f"影像前處理錯誤: {str(e)}", exc_info=True)
        # 如果前處理失敗，返回原始灰階影像
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image


def correct_skew(image):
    """
    簡單的傾斜校正
    """
    try:
        # 使用霍夫變換檢測直線
        edges = cv2.Canny(image, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)

        if lines is not None:
            angles = []
            for line in lines:
                rho, theta = line[0]
                angle = theta * 180 / np.pi
                if 45 < angle < 135:  # 接近水平的線
                    angles.append(angle - 90)

            if angles:
                # 計算平均角度
                avg_angle = np.mean(angles)
                if abs(avg_angle) > 0.5:  # 只校正角度大於 0.5 度的
                    # 旋轉影像
                    center = (image.shape[1] // 2, image.shape[0] // 2)
                    rotation_matrix = cv2.getRotationMatrix2D(center, avg_angle, 1.0)
                    corrected = cv2.warpAffine(
                        image, rotation_matrix, (image.shape[1], image.shape[0])
                    )
                    return corrected

        return image

    except Exception as e:
        logger.error(f"傾斜校正錯誤: {str(e)}", exc_info=True)
        return image


def perform_ocr(image):
    """
    使用 Google Cloud Vision API 進行 OCR
    """
    try:
        from django.conf import settings

        # 檢查是否有 API Key
        if (
            not hasattr(settings, "GOOGLE_CLOUD_VISION_API_KEY")
            or not settings.GOOGLE_CLOUD_VISION_API_KEY
        ):
            logger.error("Google Cloud Vision API Key 未設定")
            return None

        # 將 OpenCV 影像轉換為 base64
        _, buffer = cv2.imencode(".jpg", image)
        image_bytes = buffer.tobytes()
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        # 使用 REST API 呼叫 Google Cloud Vision
        url = f"https://vision.googleapis.com/v1/images:annotate?key={settings.GOOGLE_CLOUD_VISION_API_KEY}"

        payload = {
            "requests": [
                {
                    "image": {"content": image_base64},
                    "features": [{"type": "TEXT_DETECTION", "maxResults": 1}],
                    "imageContext": {
                        "languageHints": ["en"]  # 建議 A：有助數字/英文字分割
                    },
                }
            ]
        }

        headers = {"Content-Type": "application/json"}

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            logger.error(f"Vision API 請求失敗: {response.status_code}")
            logger.error(f"錯誤回應: {response.text}")
            return None

        result = response.json()

        if "responses" not in result or not result["responses"]:
            logger.error("Vision API 回應格式錯誤")
            return None

        text_annotations = result["responses"][0].get("textAnnotations", [])

        if not text_annotations:
            logger.warning("未檢測到任何文字")
            return None

        # 提取所有檢測到的文字（使用第一個 text_annotation 的 description）
        full_text = text_annotations[0].get("description", "")
        logger.info(f"OCR 檢測到的文字: {full_text}")

        # 提取卡號（使用建議 B 的簡化邏輯）
        card_number = extract_card_number_simplified(full_text)

        return {"card_number": card_number, "full_text": full_text}

    except Exception as e:
        logger.error(f"OCR 處理錯誤: {str(e)}", exc_info=True)
        return None


def extract_card_number_simplified(text):
    """
    簡化的卡號提取邏輯（建議 B）：
    用正規式抓出 14-19 位的數字片段，優先 16 位
    """
    if not text:
        return None

    # 移除所有非數字字符
    numbers_only = re.sub(r"\D", "", text)

    # 按照建議 B：尋找 14-19 位數字片段，優先 16 位
    card_patterns = [
        r"\b\d{16}\b",  # 優先：16位數字
        r"\b\d{15}\b",  # 15位數字
        r"\b\d{14}\b",  # 14位數字
        r"\b\d{17}\b",  # 17位數字
        r"\b\d{18}\b",  # 18位數字
        r"\b\d{19}\b",  # 19位數字
    ]

    # 按優先順序尋找
    for pattern in card_patterns:
        matches = re.findall(pattern, numbers_only)
        if matches:
            # 返回第一個匹配的（通常是最準確的）
            return matches[0]

    # 如果沒有找到標準格式，嘗試從長數字序列中提取
    long_numbers = re.findall(r"\d{13,}", numbers_only)
    if long_numbers:
        return long_numbers[0]

    return None


def format_card_number(card_number):
    """
    格式化信用卡號碼：
    1. 12位以上：顯示實際辨識數字
    2. 11位以下：返回 None（表示失敗）
    3. 超過16碼：保留前16碼
    4. 每4個數字之間加空格
    """
    if not card_number:
        return None

    # 移除所有非數字字符
    numbers_only = re.sub(r"\D", "", card_number)

    if len(numbers_only) < 12:
        # 11位以下：返回 None 表示失敗
        logger.warning(f"卡號長度不足（{len(numbers_only)}位），辨識失敗")
        return None
    elif len(numbers_only) > 16:
        # 超過16碼：保留前16碼
        formatted = numbers_only[:16]
        logger.info(f"卡號超過16碼，截取前16碼: {formatted}")
    else:
        # 12-16碼：顯示實際辨識數字
        formatted = numbers_only
        logger.info(f"卡號長度{len(numbers_only)}位，使用實際辨識數字: {formatted}")

    # 每4個數字之間加空格
    formatted_with_spaces = " ".join(
        [formatted[i : i + 4] for i in range(0, len(formatted), 4)]
    )

    logger.info(f"格式化後的卡號: {formatted_with_spaces}")
    return formatted_with_spaces
