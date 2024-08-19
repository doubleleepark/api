import os
from fastapi import FastAPI, HTTPException
from typing import List
import uvicorn
from pydantic import BaseModel, HttpUrl
from typing import List
import sys
import random
import pymysql
import logging
from sqlalchemy import create_engine, text
from collections import Counter, defaultdict
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mkapi.image_utils import analyze_images_and_cluster, find_signiture_color, exact_match, count_matches, find_matching_images, random_exhibition
from sklearn.cluster import SpectralClustering
from scipy.spatial.distance import cdist
import numpy as np


app = FastAPI()


color_dict = {'Cinnabar': ['(207, 46, 49)', '당신은 Cinnabar (207, 46, 49)의 취향을 가진 사람입니다. Cinnabar색에 끌리는 당신은 강렬하고 열정적인 성격을 가진 사람입니다.'], 'Guardsman Red': ['(172, 35, 48)', '당신은 Guardsman Red (172, 35, 48)의 취향을 가진 사람입니다. Guardsman Red색에 끌리는 당신은 감정 표현이 강하고, 자신감 넘치는 사람입니다.'], 'Tonys Pink': ['(233, 163, 144)', '당신은 Tonys Pink (233, 163, 144)의 취향을 가진 사람입니다. Tonys Pink색에 끌리는 당신은 따뜻하고 감성적인 성격을 가진 사람입니다.'], 'Terra Cotta': ['(231, 108, 86)', '당신은 Terra Cotta (231, 108, 86)의 취향을 가진 사람입니다. Terra Cotta색에 끌리는 당신은 자연적이고 차분한 성격을 가진 사람입니다.'], 'Almond': ['(236, 217, 202)', '당신은 Almond (236, 217, 202)의 취향을 가진 사람입니다. Almond색에 끌리는 당신은 따뜻하고 편안한 성격을 가진 사람입니다.'], 'Clam Shell': ['(213, 182, 166)', '당신은 Clam Shell (213, 182, 166)의 취향을 가진 사람입니다. Clam Shell색에 끌리는 당신은 부드럽고 안정적인 성격을 가진 사람입니다.'], 'Feldspar': ['(211, 142, 110)', '당신은 Feldspar (211, 142, 110)의 취향을 가진 사람입니다. Feldspar색에 끌리는 당신은 실용적이고 따뜻한 성격을 가진 사람입니다.'], 'Hemp': ['(171, 131, 115)', '당신은 Hemp (171, 131, 115)의 취향을 가진 사람입니다. Hemp색에 끌리는 당신은 자연적이고 차분한 성격을 가진 사람입니다.'], 'Tuscany': ['(162, 88, 61)', '당신은 Tuscany (162, 88, 61)의 취향을 가진 사람입니다. Tuscany색에 끌리는 당신은 따뜻하고 열정적인 성격을 가진 사람입니다.'], 'Tamarillo': ['(116, 47, 50)', '당신은 Tamarillo (116, 47, 50)의 취향을 가진 사람입니다. Tamarillo색에 끌리는 당신은 강렬하고 감성적인 성격을 가진 사람입니다.'], 'Cioccolato': ['(115, 63, 44)', '당신은 Cioccolato (115, 63, 44)의 취향을 가진 사람입니다. Cioccolato색에 끌리는 당신은 실용적이고 안정적인 성격을 가진 사람입니다.'], 'Pumpkin': ['(238, 113, 25)', '당신은 Pumpkin (238, 113, 25)의 취향을 가진 사람입니다. Pumpkin색에 끌리는 당신은 에너지 넘치고 열정적인 성격을 가진 사람입니다.'], 'Harvest Gold': ['(241, 176, 102)', '당신은 Harvest Gold (241, 176, 102)의 취향을 가진 사람입니다. Harvest Gold색에 끌리는 당신은 따뜻하고 활기찬 성격을 가진 사람입니다.'], 'Yellow': ['(255, 200, 8)', '당신은 Yellow (255, 200, 8)의 취향을 가진 사람입니다. Yellow색에 끌리는 당신은 활기차고 긍정적인 성격을 가진 사람입니다.'], 'Paris Daisy': ['(255, 228, 15)', '당신은 Paris Daisy (255, 228, 15)의 취향을 가진 사람입니다. Paris Daisy색에 끌리는 당신은 밝고 에너지 넘치는 성격을 가진 사람입니다.'], 'Bahia': ['(170, 198, 27)', '당신은 Bahia (170, 198, 27)의 취향을 가진 사람입니다. Bahia색에 끌리는 당신은 자연적이고 생동감 있는 성격을 가진 사람입니다.'], 'Manz': ['(219, 220, 93)', '당신은 Manz (219, 220, 93)의 취향을 가진 사람입니다. Manz색에 끌리는 당신은 신뢰감 있고 차분한 성격을 가진 사람입니다.'], 'Forest Green': ['(19, 166, 50)', '당신은 Forest Green (19, 166, 50)의 취향을 가진 사람입니다. Forest Green색에 끌리는 당신은 자연과의 연결을 중시하며, 차분하고 실용적인 성격을 가진 사람입니다.'], 'Mantis': ['(146, 198, 131)', '당신은 Mantis (146, 198, 131)의 취향을 가진 사람입니다. Mantis색에 끌리는 당신은 신선하고 자연적인 성격을 가진 사람입니다.'], 'Salem': ['(4, 148, 87)', '당신은 Salem (4, 148, 87)의 취향을 가진 사람입니다. Salem색에 끌리는 당신은 차분하고 안정적인 성격을 가진 사람입니다.'], 'Camarone': ['(39, 122, 62)', '당신은 Camarone (39, 122, 62)의 취향을 가진 사람입니다. Camarone색에 끌리는 당신은 자연과의 조화를 중시하며, 실용적이고 차분한 성격을 가진 사람입니다.'], 'Eastern Blue': ['(1, 134, 141)', '당신은 Eastern Blue (1, 134, 141)의 취향을 가진 사람입니다. Eastern Blue색에 끌리는 당신은 신뢰감 있고 차분한 성격을 가진 사람입니다.'], 'Genoa': ['(53, 109, 98)', '당신은 Genoa (53, 109, 98)의 취향을 가진 사람입니다. Genoa색에 끌리는 당신은 차분하고 안정적인 성격을 가진 사람입니다.'], 'Cobalt': ['(3, 86, 155)', '당신은 Cobalt (3, 86, 155)의 취향을 가진 사람입니다. Cobalt색에 끌리는 당신은 강렬하고 에너지 넘치는 성격을 가진 사람입니다.'], 'Cerulean': ['(6, 113, 148)', '당신은 Cerulean (6, 113, 148)의 취향을 가진 사람입니다. Cerulean색에 끌리는 당신은 신선하고 상쾌한 성격을 가진 사람입니다.'], 'Persian Indigo': ['(46, 20, 141)', '당신은 Persian Indigo (46, 20, 141)의 취향을 가진 사람입니다. Persian Indigo색에 끌리는 당신은 강렬하고 신비로운 성격을 가진 사람입니다.'], 'Black': ['(44, 60, 49)', '당신은 Black (44, 60, 49)의 취향을 가진 사람입니다. Black색에 끌리는 당신은 신비롭고 강렬한 성격을 가진 사람입니다.'], 'White Smoke': ['(244, 244, 244)', '당신은 White Smoke (244, 244, 244)의 취향을 가진 사람입니다. White Smoke색에 끌리는 당신은 순수하고 세련된 성격을 가진 사람입니다.'], 'Very Light Grey': ['(206, 206, 206)', '당신은 Very Light Grey (206, 206, 206)의 취향을 가진 사람입니다. Very Light Grey색에 끌리는 당신은 차분하고 세련된 성격을 가진 사람입니다.'], 'Grey': ['(152, 152, 152)', '당신은 Grey (152, 152, 152)의 취향을 가진 사람입니다. Grey색에 끌리는 당신은 차분하고 실용적인 성격을 가진 사람입니다.'], 'Deep Koamaru': ['(40, 47, 103)', '당신은 Deep Koamaru (40, 47, 103)의 취향을 가진 사람입니다. Deep Koamaru색에 끌리는 당신은 신뢰감 있고 차분한 성격을 가진 사람입니다.'], 'Palm Green': ['(34, 62, 51)', '당신은 Palm Green (34, 62, 51)의 취향을 가진 사람입니다. Palm Green색에 끌리는 당신은 자연과의 연결을 중시하며, 실용적이고 안정적인 성격을 가진 사람입니다.'], 'Corn Field': ['(245, 223, 181)', '당신은 Corn Field (245, 223, 181)의 취향을 가진 사람입니다. Corn Field색에 끌리는 당신은 자연과의 조화를 중시하며, 따뜻하고 실용적인 성격을 가진 사람입니다.'], 'Fun Green': ['(24, 89, 63)', '당신은 Fun Green (24, 89, 63)의 취향을 가진 사람입니다. Fun Green색에 끌리는 당신은 생동감 있고 상쾌한 성격을 가진 사람입니다.'], 'Sherpa Blue': ['(8, 87, 107)', '당신은 Sherpa Blue (8, 87, 107)의 취향을 가진 사람입니다. Sherpa Blue색에 끌리는 당신은 차분하고 신뢰감 있는 성격을 가진 사람입니다.'], 'Wistful': ['(197, 188, 213)', '당신은 Wistful (197, 188, 213)의 취향을 가진 사람입니다. Wistful색에 끌리는 당신은 감성적이고 차분한 성격을 가진 사람입니다.'], 'Granny Smith': ['(127, 175, 166)', '당신은 Granny Smith (127, 175, 166)의 취향을 가진 사람입니다. Granny Smith색에 끌리는 당신은 자연과의 조화를 중시하며, 차분하고 실용적인 성격을 가진 사람입니다.'], 'Nepal': ['(147, 184, 213)', '당신은 Nepal (147, 184, 213)의 취향을 가진 사람입니다. Nepal색에 끌리는 당신은 신뢰감 있고 안정적인 성격을 가진 사람입니다.'], 'Rose': ['(218, 176, 176)', '당신은 Rose (218, 176, 176)의 취향을 가진 사람입니다. Rose색에 끌리는 당신은 감성적이고 우아한 성격을 가진 사람입니다.'], 'Granite Green': ['(144, 135, 96)', '당신은 Granite Green (144, 135, 96)의 취향을 가진 사람입니다. Granite Green색에 끌리는 당신은 자연적이고 실용적인 성격을 가진 사람입니다.'], 'Dingley': ['(88, 126, 61)', '당신은 Dingley (88, 126, 61)의 취향을 가진 사람입니다. Dingley색에 끌리는 당신은 신선하고 생동감 있는 성격을 가진 사람입니다.'], 'Costa Del Sol': ['(139, 117, 65)', '당신은 Costa Del Sol (139, 117, 65)의 취향을 가진 사람입니다. Costa Del Sol색에 끌리는 당신은 따뜻하고 실용적인 성격을 가진 사람입니다.'], 'Mandy': ['(204, 63, 92)', '당신은 Mandy (204, 63, 92)의 취향을 가진 사람입니다. Mandy색에 끌리는 당신은 감성적이고 열정적인 성격을 가진 사람입니다.'], 'Pale Sky': ['(92, 104, 106)', '당신은 Pale Sky (92, 104, 106)의 취향을 가진 사람입니다. Pale Sky색에 끌리는 당신은 차분하고 실용적인 성격을 가진 사람입니다.'], 'Au Chico': ['(175, 97, 87)', '당신은 Au Chico (175, 97, 87)의 취향을 가진 사람입니다. Au Chico색에 끌리는 당신은 따뜻하고 열정적인 성격을 가진 사람입니다.'], 'London Hue': ['(178, 137, 166)', '당신은 London Hue (178, 137, 166)의 취향을 가진 사람입니다. London Hue색에 끌리는 당신은 섬세하고 감성적인 성격을 가진 사람입니다.'], 'Cabaret': ['(209, 100, 109)', '당신은 Cabaret (209, 100, 109)의 취향을 가진 사람입니다. Cabaret색에 끌리는 당신은 감정 표현이 강하고, 화려하고 자신감 넘치는 성격의 사람입니다.'], 'Seagull': ['(126, 188, 209)', '당신은 Seagull (126, 188, 209)의 취향을 가진 사람입니다. Seagull색에 끌리는 당신은 차분하고 신뢰할 수 있는 성격을 가진 사람입니다.'], 'Frostee': ['(221, 232, 207)', '당신은 Frostee (221, 232, 207)의 취향을 가진 사람입니다. Frostee색에 끌리는 당신은 차분하고 안정적인 성격을 가진 사람입니다.'], 'Aqua Squeeze': ['(209, 234, 211)', '당신은 Aqua Squeeze (209, 234, 211)의 취향을 가진 사람입니다. Aqua Squeeze색에 끌리는 당신은 신선하고 생동감 있는 성격을 가진 사람입니다.'], 'Pattens Blue': ['(194, 222, 242)', '당신은 Pattens Blue (194, 222, 242)의 취향을 가진 사람입니다. Pattens Blue색에 끌리는 당신은 상쾌하고 차분한 성격을 가진 사람입니다.'], 'Hawkes Blue': ['(203, 215, 232)', '당신은 Hawkes Blue (203, 215, 232)의 취향을 가진 사람입니다. Hawkes Blue색에 끌리는 당신은 신뢰감 있고 차분한 성격을 가진 사람입니다.'], 'Titan White': ['(224, 218, 230)', '당신은 Titan White (224, 218, 230)의 취향을 가진 사람입니다. Titan White색에 끌리는 당신은 순수하고 세련된 성격을 가진 사람입니다.'], 'Pale Rose': ['(235, 219, 224)', '당신은 Pale Rose (235, 219, 224)의 취향을 가진 사람입니다. Pale Rose색에 끌리는 당신은 감성적이고 따뜻한 성격을 가진 사람입니다.'], 'Raffia': ['(218, 196, 148)', '당신은 Raffia (218, 196, 148)의 취향을 가진 사람입니다. Raffia색에 끌리는 당신은 자연적이고 안정적인 성격을 가진 사람입니다.'], 'Red Damask': ['(209, 116, 73)', '당신은 Red Damask (209, 116, 73)의 취향을 가진 사람입니다. Red Damask색에 끌리는 당신은 강렬하고 열정적인 성격을 가진 사람입니다.'], 'Sprout': ['(179, 202, 157)', '당신은 Sprout (179, 202, 157)의 취향을 가진 사람입니다. Sprout색에 끌리는 당신은 자연적이고 신선한 성격을 가진 사람입니다.'], 'Spring Rain': ['(166, 201, 163)', '당신은 Spring Rain (166, 201, 163)의 취향을 가진 사람입니다. Spring Rain색에 끌리는 당신은 차분하고 자연을 중시하는 성격을 가진 사람입니다.'], 'Heather': ['(165, 184, 199)', '당신은 Heather (165, 184, 199)의 취향을 가진 사람입니다. Heather색에 끌리는 당신은 섬세하고 안정적인 성격을 가진 사람입니다.'], 'Wafer': ['(206, 185, 179)', '당신은 Wafer (206, 185, 179)의 취향을 가진 사람입니다. Wafer색에 끌리는 당신은 따뜻하고 실용적인 성격을 가진 사람입니다.'], 'Sage': ['(143, 162, 121)', '당신은 Sage (143, 162, 121)의 취향을 가진 사람입니다. Sage색에 끌리는 당신은 자연적이고 실용적인 성격을 가진 사람입니다.'], 'Oxley': ['(122, 165, 123)', '당신은 Oxley (122, 165, 123)의 취향을 가진 사람입니다. Oxley색에 끌리는 당신은 신선하고 차분한 성격을 가진 사람입니다.'], 'Lemon Ginger': ['(156, 137, 37)', '당신은 Lemon Ginger (156, 137, 37)의 취향을 가진 사람입니다. Lemon Ginger색에 끌리는 당신은 따뜻하고 실용적인 성격을 가진 사람입니다.'], 'Tosca': ['(115, 71, 79)', '당신은 Tosca (115, 71, 79)의 취향을 가진 사람입니다. Tosca색에 끌리는 당신은 강렬하고 감성적인 성격을 가진 사람입니다.'], 'Green House': ['(54, 88, 48)', '당신은 Green House (54, 88, 48)의 취향을 가진 사람입니다. Green House색에 끌리는 당신은 자연과의 연결을 중시하며, 차분하고 실용적인 성격을 가진 사람입니다.']}

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

class ImageData(BaseModel):
    user_images_urls: List[HttpUrl] = [
        "https://ifh.cc/g/oY2K9B.jpg",
        "https://ifh.cc/g/zwxOAA.jpg",
        "https://ifh.cc/g/XSAScb.jpg",
        "https://ifh.cc/g/DgrlJL.jpg"]


@app.post("/analyze-most-common-rgb/")
async def analyze_rgb(image_data: ImageData):
    rgb_counts = Counter()
    cursor = db_connection.cursor()

    for url in image_data.user_images_urls:
        cursor.execute("SELECT cluster_rgb, cluster_count FROM images WHERE url = %s", (url,))
        result = cursor.fetchone()

        if result:
            cluster_rgb, cluster_count = result['cluster_rgb'], result['cluster_count']
            # cluster_rgb 예시: "(59,130,157),(44,77,143)"
            # cluster_count 예시: "1,2"
            rgbs = cluster_rgb.strip("()").split("),(")
            counts = cluster_count.split(",")

            for rgb, count in zip(rgbs, counts):
                rgb_counts[rgb] += int(count)
        else:
            raise HTTPException(status_code=404, detail="Image not found in the database")

    if not rgb_counts:
        raise HTTPException(status_code=404, detail="No RGB data found for provided URLs")

    most_common_rgb, _ = rgb_counts.most_common(1)[0]
    most_common_rgb = tuple(int(num) for num in most_common_rgb.strip('()').split(','))

    # Find the matching color name and description
    for color_name, (rgb, description) in color_dict.items():
        rgb = tuple(int(num) for num in rgb.strip('()').split(','))
        if rgb == most_common_rgb:
            return {
                "user_rgb": most_common_rgb,
                "user_color": color_name,
                "user_text": description
            }

    # If no exact match is found
    return {
        "user_rgb": most_common_rgb,
        "user_color": "Unknown",
        "user_text": "No exact color match found in our database."
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
