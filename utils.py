import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from skimage.color import rgb2hsv
import os
from PIL import Image
import requests
from io import BytesIO
import cv2
from pydantic import BaseModel, HttpUrl
from typing import List
from fastapi import HTTPException

class ImageData(BaseModel):
    user_images_urls: List[HttpUrl] = [
        "https://ifh.cc/g/oY2K9B.jpg",
    ]
class text_explain(BaseModel):
    text: str = "원하는 분위기의 그림 혹은 인테리어의 감성을 입력"

# 1. 이미지 데이터 처리
def load_image_from_url_with_requests(url):
    """
    주어진 URL에서 이미지를 로드합니다.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # HTTP 에러 처리
        img = Image.open(BytesIO(response.content)).convert("RGB")
        return np.array(img)
    except Exception as e:
        print(f"Error loading image from {url}: {e}")
        return None


def process_image(data: ImageData):
    """
    주어진 이미지 데이터에서 RGB 및 HSV 평균값을 계산합니다.
    """
    if not data.user_images_urls:
        raise HTTPException(status_code=400, detail="The user images URL list is empty.")
    
    all_rgb = []
    all_hsv = []

    for url in data.user_images_urls:
        # Load and validate image
        image = load_image_from_url_with_requests(str(url))
        if image is None:
            print(f"Skipping invalid image from URL: {url}")
            continue

        # Calculate mean RGB
        mean_rgb = image.mean(axis=(0, 1))  # (height, width, channels)

        # Convert to HSV
        hsv_image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV) / 255.0
        mean_hue = hsv_image[:, :, 0].mean()
        mean_saturation = hsv_image[:, :, 1].mean()
        mean_value = hsv_image[:, :, 2].mean()

        all_rgb.append(mean_rgb)
        all_hsv.append([mean_hue, mean_saturation, mean_value])

    if not all_rgb or not all_hsv:
        print("No valid images were processed.")
        raise HTTPException(status_code=400, detail="No valid images were processed.")

    # 평균 계산
    avg_rgb = np.mean(all_rgb, axis=0)
    avg_hsv = np.mean(all_hsv, axis=0)

    # 2차원 배열로 변환
    return np.concatenate((avg_rgb, avg_hsv)).reshape(1, -1)



def process_text(data: text_explain):
    """
    주어진 텍스트 데이터를 TF-IDF 벡터로 변환합니다.
    """
    if not data.text.strip():
        raise HTTPException(status_code=400, detail="The input text is empty.")
    
    # TF-IDF Vectorizer 초기화
    vectorizer = TfidfVectorizer(max_features=5)  # 상위 5개 특징값만 추출
    # 텍스트를 리스트 형태로 전달
    tfidf_matrix = vectorizer.fit_transform([data.text]).toarray()
    return tfidf_matrix

# 3. 타겟 값 인코딩
def encode_targets(targets):
    """타겟 값을 숫자로 인코딩"""
    label_encoder = LabelEncoder()
    encoded_targets = label_encoder.fit_transform(targets)
    return encoded_targets, label_encoder.classes_