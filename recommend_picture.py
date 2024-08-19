import os
import logging
import random
from typing import List
from fastapi import FastAPI, HTTPException
import uvicorn
import pymysql
import requests
import cv2
import numpy as np
from io import BytesIO
from PIL import Image
from sklearn.cluster import SpectralClustering
from scipy.spatial.distance import cdist
from pydantic import BaseModel, HttpUrl
from skimage.metrics import structural_similarity as ssim

# FastAPI 애플리케이션 초기화
app = FastAPI()

# 로깅 설정
logging.basicConfig(level=logging.INFO)

# 데이터베이스 설정
db_config = {
    'host': '127.0.0.1',
    'user': 'admin',
    'password': 'restartart',
    'database': 'restartdb',
    'port': 3306
}

def connect_db(config):
    """ 데이터베이스 연결 함수 """
    try:
        connection = pymysql.connect(host=config['host'],
                                     user=config['user'],
                                     password=config['password'],
                                     database=config['database'],
                                     cursorclass=pymysql.cursors.DictCursor)
        logging.info("Database connection successful")
        return connection
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        return None

# 데이터베이스 연결
db_connection = connect_db(db_config)

def get_image_url_list(connection):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT url FROM images")
            result = cursor.fetchall()
            return [row['url'] for row in result]
    except Exception as e:
        logging.error(f"Failed to fetch image URLs: {e}")
        return []

# image_url_list 가져오기
image_url_list = get_image_url_list(db_connection)