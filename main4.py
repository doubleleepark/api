import json
import os
from fastapi import FastAPI, HTTPException
import uvicorn
from pydantic import BaseModel, HttpUrl
from typing import List
import sys
import random
import pymysql
import logging
from collections import Counter
from fastapi import Query


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mkapi.image_utils import analyze_images_and_cluster, find_signiture_color, exact_match, count_matches, find_matching_images, random_exhibition, find_nearby_exhibitions, leaflet_design
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()


# Define CORS settings
origins = ["*"]  # Allow requests from any origin

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


color_dict = {
    'Cinnabar': ['(231, 47, 39)',
                 '당신은 Cinnabar (231, 47, 39)의 취향을 가진 사람입니다. Cinnabar 색에 끌리는 당신은 강렬하고 열정적인 성격을 가진 사람입니다.'],

    'Black': ['(152, 152, 152)', '당신은 Black (44, 60, 49)의 취향을 가진 사람입니다. Black색에 끌리는 당신은 신비롭고 강렬한 성격을 가진 사람입니다.'],

    'Matterhorn': ['(86, 86, 86)',
                   '당신은 Matterhorn (86, 86, 86)의 취향을 가진 사람입니다. Matterhorn 색에 끌리는 당신은 안정적이고 신뢰할 수 있는 성격을 가진 사람입니다.'],

    'Nobel': ['(152, 152, 152)',
              '당신은 Nobel (152, 152, 152)의 취향을 가진 사람입니다. Nobel 색에 끌리는 당신은 실용적이며 차분한 성격을 가진 사람입니다.'],

    'Very Light Grey': ['(206, 206, 206)',
                        '당신은 Very Light Grey (206, 206, 206)의 취향을 가진 사람입니다. Very Light Grey 색에 끌리는 당신은 섬세하고 정돈된 성격을 가진 사람입니다.'],

    'White Smoke': ['(244, 244, 244)',
                    '당신은 White Smoke (244, 244, 244)의 취향을 가진 사람입니다. White Smoke 색에 끌리는 당신은 순수하고 깨끗한 성격을 가진 사람입니다.'],

    'Paris Daisy': ['(255, 236, 79)',
                    '당신은 Paris Daisy (255, 236, 79)의 취향을 가진 사람입니다. Paris Daisy 색에 끌리는 당신은 밝고 긍정적인 성격을 가진 사람입니다.'],

    'Corn Field': ['(249, 239, 189)',
                   '당신은 Corn Field (249, 239, 189)의 취향을 가진 사람입니다. Corn Field 색에 끌리는 당신은 따뜻하고 부드러운 성격을 가진 사람입니다.'],

    'Bahia': ['(170, 198, 27)',
              '당신은 Bahia (170, 198, 27)의 취향을 가진 사람입니다. Bahia 색에 끌리는 당신은 생기 넘치고 활기찬 성격을 가진 사람입니다.'],

    'Kournikova': ['(255, 203, 88)',
                   '당신은 Kournikova (255, 203, 88)의 취향을 가진 사람입니다. Kournikova 색에 끌리는 당신은 따뜻하고 다정한 성격을 가진 사람입니다.'],

    'Gossip': ['(146, 198, 131)',
               '당신은 Gossip (146, 198, 131)의 취향을 가진 사람입니다. Gossip 색에 끌리는 당신은 친절하고 상냥한 성격을 가진 사람입니다.'],

    'Tangerine Yellow': ['(255, 200, 8)',
                         '당신은 Tangerine Yellow (255, 200, 8)의 취향을 가진 사람입니다. Tangerine Yellow 색에 끌리는 당신은 창의적이고 활발한 성격을 가진 사람입니다.'],

    'Pumpkin': ['(238, 113, 25)',
                '당신은 Pumpkin (238, 113, 25)의 취향을 가진 사람입니다. Pumpkin 색에 끌리는 당신은 열정적이고 적극적인 성격을 가진 사람입니다.'],

    'Harvest Gold': ['(242, 178, 103)',
                     '당신은 Harvest Gold (242, 178, 103)의 취향을 가진 사람입니다. Harvest Gold 색에 끌리는 당신은 따뜻하고 풍부한 성격을 가진 사람입니다.'],

    'Persian Indigo': ['(46, 20, 141)',
                       '당신은 Persian Indigo (46, 20, 141)의 취향을 가진 사람입니다. Persian Indigo 색에 끌리는 당신은 신비롭고 지적인 성격을 가진 사람입니다.'],

    'Cobalt': ['(3, 86, 155)',
               '당신은 Cobalt (3, 86, 155)의 취향을 가진 사람입니다. Cobalt 색에 끌리는 당신은 깊고 진중한 성격을 가진 사람입니다.'],

    'Dark Pastel Green': ['(19, 166, 50)',
                          '당신은 Dark Pastel Green (19, 166, 50)의 취향을 가진 사람입니다. Dark Pastel Green 색에 끌리는 당신은 조용하고 차분한 성격을 가진 사람입니다.'],

    'Shamrock Green': ['(4, 148, 87)',
                       '당신은 Shamrock Green (4, 148, 87)의 취향을 가진 사람입니다. Shamrock Green 색에 끌리는 당신은 희망차고 활기찬 성격을 가진 사람입니다.'],

    'Salem': ['(6, 134, 84)',
              '당신은 Salem (6, 134, 84)의 취향을 가진 사람입니다. Salem 색에 끌리는 당신은 신뢰할 수 있고 안정된 성격을 가진 사람입니다.'],

    'Wistful': ['(170, 165, 199)',
                '당신은 Wistful (170, 165, 199)의 취향을 가진 사람입니다. Wistful 색에 끌리는 당신은 감성적이고 사색적인 성격을 가진 사람입니다.'],

    'Eastern Blue': ['(0, 147, 159)',
                     '당신은 Eastern Blue (0, 147, 159)의 취향을 가진 사람입니다. Eastern Blue 색에 끌리는 당신은 차분하고 논리적인 성격을 가진 사람입니다.'],

    'Brandy Rose': ['(171, 131, 115)',
                    '당신은 Brandy Rose (171, 131, 115)의 취향을 가진 사람입니다. Brandy Rose 색에 끌리는 당신은 우아하고 정교한 성격을 가진 사람입니다.'],

    'Granite Green': ['(144, 135, 96)',
                      '당신은 Granite Green (144, 135, 96)의 취향을 가진 사람입니다. Granite Green 색에 끌리는 당신은 자연스럽고 소박한 성격을 가진 사람입니다.'],

    'Manz': ['(219, 220, 93)',
             '당신은 Manz (219, 220, 93)의 취향을 가진 사람입니다. Manz 색에 끌리는 당신은 밝고 낙천적인 성격을 가진 사람입니다.'],

    'Wild Willow': ['(195, 202, 101)',
                    '당신은 Wild Willow (195, 202, 101)의 취향을 가진 사람입니다. Wild Willow 색에 끌리는 당신은 유연하고 이해심 많은 성격을 가진 사람입니다.'],

    'Cioccolato': ['(88, 60, 50)',
                   '당신은 Cioccolato (88, 60, 50)의 취향을 가진 사람입니다. Cioccolato 색에 끌리는 당신은 깊고 진중한 성격을 가진 사람입니다.'],

    'Cerulean': ['(6, 113, 148)',
                 '당신은 Cerulean (6, 113, 148)의 취향을 가진 사람입니다. Cerulean 색에 끌리는 당신은 차분하고 신뢰할 수 있는 성격을 가진 사람입니다.'],

    'Chelsea Cucumber': ['(141, 188, 90)',
                         '당신은 Chelsea Cucumber (141, 188, 90)의 취향을 가진 사람입니다. Chelsea Cucumber 색에 끌리는 당신은 상쾌하고 자연을 사랑하는 성격을 가진 사람입니다.'],

    'Fun Green': ['(24, 89, 63)',
                  '당신은 Fun Green (24, 89, 63)의 취향을 가진 사람입니다. Fun Green 색에 끌리는 당신은 모험적이고 독창적인 성격을 가진 사람입니다.'],

    'Deep Teal': ['(27, 86, 49)',
                  '당신은 Deep Teal (27, 86, 49)의 취향을 가진 사람입니다. Deep Teal 색에 끌리는 당신은 깊고 사려 깊은 성격을 가진 사람입니다.'],

    'Deep Bronze': ['(75, 63, 45)',
                    '당신은 Deep Bronze (75, 63, 45)의 취향을 가진 사람입니다. Deep Bronze 색에 끌리는 당신은 고전적이고 전통적인 성격을 가진 사람입니다.'],

    'Timber Green': ['(44, 60, 49)',
                     '당신은 Timber Green (44, 60, 49)의 취향을 가진 사람입니다. Timber Green 색에 끌리는 당신은 안정적이고 신뢰할 수 있는 성격을 가진 사람입니다.'],

    'Palm Green': ['(31, 56, 45)',
                   '당신은 Palm Green (31, 56, 45)의 취향을 가진 사람입니다. Palm Green 색에 끌리는 당신은 조용하고 내성적인 성격을 가진 사람입니다.'],

    'Tiber': ['(25, 62, 63)',
              '당신은 Tiber (25, 62, 63)의 취향을 가진 사람입니다. Tiber 색에 끌리는 당신은 신비롭고 깊이 있는 성격을 가진 사람입니다.'],

    'Metallic Copper': ['(111, 61, 56)',
                        '당신은 Metallic Copper (111, 61, 56)의 취향을 가진 사람입니다. Metallic Copper 색에 끌리는 당신은 열정적이고 결단력 있는 성격을 가진 사람입니다.'],

    'Tamarillo': ['(116, 47, 50)',
                  '당신은 Tamarillo (116, 47, 50)의 취향을 가진 사람입니다. Tamarillo 색에 끌리는 당신은 감정적이고 열정적인 성격을 가진 사람입니다.'],

    'Apple Blossom': ['(175, 92, 87)',
                      '당신은 Apple Blossom (175, 92, 87)의 취향을 가진 사람입니다. Apple Blossom 색에 끌리는 당신은 부드럽고 다정한 성격을 가진 사람입니다.'],

    'Surfie Green': ['(3, 130, 122)',
                     '당신은 Surfie Green (3, 130, 122)의 취향을 가진 사람입니다. Surfie Green 색에 끌리는 당신은 진취적이고 활기찬 성격을 가진 사람입니다.'],

    'Feldspar': ['(211, 142, 110)',
                 '당신은 Feldspar (211, 142, 110)의 취향을 가진 사람입니다. Feldspar 색에 끌리는 당신은 따뜻하고 감성적인 성격을 가진 사람입니다.'],

    'Vesuvius': ['(169, 87, 49)',
                 '당신은 Vesuvius (169, 87, 49)의 취향을 가진 사람입니다. Vesuvius 색에 끌리는 당신은 열정적이고 강렬한 성격을 가진 사람입니다.'],

    'Blue Lagoon': ['(8, 87, 107)',
                    '당신은 Blue Lagoon (8, 87, 107)의 취향을 가진 사람입니다. Blue Lagoon 색에 끌리는 당신은 차분하고 지적인 성격을 가진 사람입니다.'],

    'Tonys Pink': ['(233, 163, 144)',
                   '당신은 Tonys Pink (233, 163, 144)의 취향을 가진 사람입니다. Tonys Pink 색에 끌리는 당신은 부드럽고 낭만적인 성격을 가진 사람입니다.'],

    'Wafer': ['(206, 185, 179)',
              '당신은 Wafer (206, 185, 179)의 취향을 가진 사람입니다. Wafer 색에 끌리는 당신은 따뜻하고 세련된 성격을 가진 사람입니다.'],

    'Camarone': ['(20, 114, 48)',
                 '당신은 Camarone (20, 114, 48)의 취향을 가진 사람입니다. Camarone 색에 끌리는 당신은 진취적이고 단호한 성격을 가진 사람입니다.'],

    'Vida Loca': ['(91, 132, 47)',
                  '당신은 Vida Loca (91, 132, 47)의 취향을 가진 사람입니다. Vida Loca 색에 끌리는 당신은 창의적이고 활기찬 성격을 가진 사람입니다.'],

    'Green House': ['(54, 88, 48)',
                    '당신은 Green House (54, 88, 48)의 취향을 가진 사람입니다. Green House 색에 끌리는 당신은 신뢰할 수 있고 자연을 사랑하는 성격을 가진 사람입니다.'],

    'Granny Smith': ['(130, 154, 145)',
                     '당신은 Granny Smith (130, 154, 145)의 취향을 가진 사람입니다. Granny Smith 색에 끌리는 당신은 차분하고 신뢰할 수 있는 성격을 가진 사람입니다.'],

    'Wheat': ['(245, 223, 181)',
              '당신은 Wheat (245, 223, 181)의 취향을 가진 사람입니다. Wheat 색에 끌리는 당신은 따뜻하고 부드러운 성격을 가진 사람입니다.'],

    'Pale Rose': ['(235, 219, 224)',
                  '당신은 Pale Rose (235, 219, 224)의 취향을 가진 사람입니다. Pale Rose 색에 끌리는 당신은 섬세하고 로맨틱한 성격을 가진 사람입니다.'],

    'Oyster Pink': ['(218, 176, 176)',
                    '당신은 Oyster Pink (218, 176, 176)의 취향을 가진 사람입니다. Oyster Pink 색에 끌리는 당신은 감성적이고 다정한 성격을 가진 사람입니다.'],

    'Opal': ['(184, 190, 189)',
             '당신은 Opal (184, 190, 189)의 취향을 가진 사람입니다. Opal 색에 끌리는 당신은 차분하고 신중한 성격을 가진 사람입니다.'],

    'London Hue': ['(178, 137, 166)',
                   '당신은 London Hue (178, 137, 166)의 취향을 가진 사람입니다. London Hue 색에 끌리는 당신은 섬세하고 창의적인 성격을 가진 사람입니다.'],

    'Lemon Ginger': ['(156, 137, 37)',
                     '당신은 Lemon Ginger (156, 137, 37)의 취향을 가진 사람입니다. Lemon Ginger 색에 끌리는 당신은 창의적이고 독창적인 성격을 가진 사람입니다.'],

    'Guardsman Red': ['(172, 36, 48)',
                      '당신은 Guardsman Red (172, 36, 48)의 취향을 가진 사람입니다. Guardsman Red 색에 끌리는 당신은 강렬하고 열정적인 성격을 가진 사람입니다.'],

    'Mandy': ['(204, 63, 92)',
              '당신은 Mandy (204, 63, 92)의 취향을 가진 사람입니다. Mandy 색에 끌리는 당신은 감성적이고 로맨틱한 성격을 가진 사람입니다.'],

    'Costa Del Sol': ['(103, 91, 44)',
                      '당신은 Costa Del Sol (103, 91, 44)의 취향을 가진 사람입니다. Costa Del Sol 색에 끌리는 당신은 고전적이고 우아한 성격을 가진 사람입니다.'],

    'Chetwode Blue': ['(92, 104, 163)',
                      '당신은 Chetwode Blue (92, 104, 163)의 취향을 가진 사람입니다. Chetwode Blue 색에 끌리는 당신은 지적이고 사려 깊은 성격을 가진 사람입니다.'],

    'Aqua Squeeze': ['(209, 234, 211)',
                     '당신은 Aqua Squeeze (209, 234, 211)의 취향을 가진 사람입니다. Aqua Squeeze 색에 끌리는 당신은 차분하고 신중한 성격을 가진 사람입니다.'],

    'Siam': ['(109, 116, 73)',
             '당신은 Siam (109, 116, 73)의 취향을 가진 사람입니다. Siam 색에 끌리는 당신은 안정적이고 실용적인 성격을 가진 사람입니다.'],

    'Sprout': ['(179, 202, 157)',
               '당신은 Sprout (179, 202, 157)의 취향을 가진 사람입니다. Sprout 색에 끌리는 당신은 생기 넘치고 활기찬 성격을 가진 사람입니다.'],

    'Oxley': ['(122, 165, 123)',
              '당신은 Oxley (122, 165, 123)의 취향을 가진 사람입니다. Oxley 색에 끌리는 당신은 자연스럽고 신뢰할 수 있는 성격을 가진 사람입니다.'],

    'Seagull': ['(126, 188, 209)',
                '당신은 Seagull (126, 188, 209)의 취향을 가진 사람입니다. Seagull 색에 끌리는 당신은 상쾌하고 지적인 성격을 가진 사람입니다.'],

    'Gulf Stream': ['(117, 173, 169)',
                    '당신은 Gulf Stream (117, 173, 169)의 취향을 가진 사람입니다. Gulf Stream 색에 끌리는 당신은 차분하고 평온한 성격을 가진 사람입니다.'],

    'Heather': ['(165, 184, 199)',
                '당신은 Heather (165, 184, 199)의 취향을 가진 사람입니다. Heather 색에 끌리는 당신은 부드럽고 차분한 성격을 가진 사람입니다.'],

    'Hawkes Blue': ['(203, 215, 232)',
                    '당신은 Hawkes Blue (203, 215, 232)의 취향을 가진 사람입니다. Hawkes Blue 색에 끌리는 당신은 지적이고 내성적인 성격을 가진 사람입니다.']
}




db_config = {
    'host': 'database-1.c588s0060coo.ap-northeast-2.rds.amazonaws.com',
    'user': 'admin',
    'password': 'restartart',
    'database': 'imci_restartdb'
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



class SignitureImageData(BaseModel):
    user_images_urls: List[str]

class lat_long(BaseModel):
    lat_long_list: List[float] = [
        37.5173319258532,
        127.047377408384
    ]
class lat_long_input(BaseModel):
    lat_input: float = 37.5173319258532
    long_input: float = 127.047377408384

@app.get('/find_near_exhibition/')
async def find_near_exhibition(lat_input: float = Query(...), long_input: float = Query(...)):
    cursor = db_connection.cursor()
    cursor.execute("SELECT name FROM exhibitions")
    exhibition = [row['name'] for row in cursor.fetchall()]
    cursor.execute("SELECT latitude FROM exhibitions")
    exhibition2 = [row['latitude'] for row in cursor.fetchall()]
    cursor.execute("SELECT longitude FROM exhibitions")
    exhibition3 = [row['longitude'] for row in cursor.fetchall()]

    exhibition_info = [
        [exhibition[i], [float(exhibition2[i]), float(exhibition3[i])]]
        for i in range(len(exhibition))
    ]
    
    # 사용자의 위치 정보 설정
    user_location = [lat_input, long_input]
    location_ex = lat_long(lat_long_list=user_location)
    
    # 반경 설정
    radius = 100
    # 가장 가까운 전시회를 찾는 로직
    nearest_exhibition_name = find_nearby_exhibitions(location_ex.lat_long_list, exhibition_info, radius)
    
    # 상세 전시회 정보 가져오기
    cursor.execute("SELECT start_date, end_date, description,exhibition_img FROM exhibitions WHERE name = %s", (nearest_exhibition_name,))
    result = cursor.fetchone()
    detailed_exhibition = {}

    if result:
        detailed_exhibition = {
            'name': nearest_exhibition_name,
            'start_date': result['start_date'],
            'end_date': result['end_date'],
            'description': result['description'],
            "exhibition_img":result["exhibition_img"]
        }

    return detailed_exhibition


@app.post("/leaflet_creating/")
async def leaflet_creating(image_data: ImageData):
    cursor = db_connection.cursor()
    cursor.execute("SELECT url FROM images_exhibition_10")
    row_images = [row['url'] for row in cursor.fetchall()]

    cursor.execute("SELECT color_cluster_ratio FROM images_exhibition_10")
    row_images2 = [row['color_cluster_ratio'] for row in cursor.fetchall()]

    result = {
        'url': [],
        'color_cluster_ratio' : []
    }
    result['url'] = row_images
    result['color_cluster_ratio'] = row_images2

    try:

        find_matching_payload = ImageData(
            user_images_urls=image_data.user_images_urls,
        )
        # 1. 유사도 분석 돌리기

        matching_images_response = find_matching_images(find_matching_payload, result)

        matching_urls = matching_images_response['matching_urls']


        # 2. 스펙트럴 클러스터링 하기
        analysis_result = analyze_images_and_cluster(
            matching_urls,result
        )

        # 3. 취향분석하기
        #max_color = 0
        
        # 3. 취향분석하기
        #max_color = 0
        if matching_urls['url'] != []:
            color_number_one = find_signiture_color(matching_urls['color_cluster_ratio'])
        else:
            color_number_one = find_signiture_color(random.choices(result['color_cluster_ratio'],k=4))
        text_user = {}
        for i in color_dict.keys():
            if i == color_number_one:
                text_user = {"user_color": color_dict[i][1]}
                dominant_color = i
                user_rgb = color_dict[i][0]
                break


        # 4. 작품 추천하기
        cursor.execute("SELECT * FROM images_exhibition_1")
        rrow = cursor.fetchall()

        cursor.execute("SELECT url FROM images_exhibition_1")
        row2 = [row['url'] for row in cursor.fetchall()]
        cursor.execute("SELECT color_cluster_ratio FROM images_exhibition_1")
        row3 = [row['color_cluster_ratio'] for row in cursor.fetchall()]

        new_color_dict = {}
        jj = 0
        for i in row2:
            new_color_dict[i] = json.loads(row3[jj])
            jj+=1

        recommend_picture = None

        mood_dict = {}
        for i in range(len(rrow)):
            mood_dict[rrow[i]['url']] = rrow[i]['emotions']


        max_color = 0
        for key, colors in new_color_dict.items():
            for color in colors:
                if color[0] == dominant_color:
                    if color[2] > max_color:
                        max_color = color[2]
                        recommend_picture = key

        recommend_picture_list = []
        if recommend_picture:
            for i in range(len(new_color_dict)):
                if recommend_picture == rrow[i]['url']:
                    recommend_picture_list.append(rrow[i]['url'])
                    recommend_picture_list.append(rrow[i]['title'])
                    recommend_picture_list.append(rrow[i]['author'])
        else:
            no_no = random.randint(1, len(rrow))
            recommend_picture_list.append(rrow[no_no]['url'])
            recommend_picture_list.append(rrow[no_no]['title'])
            recommend_picture_list.append(rrow[no_no]['author'])
            recommend_picture = rrow[no_no]['url']

        target_mood = mood_dict[recommend_picture]

        del mood_dict[recommend_picture]
        all_three_matches = [k for k, v in mood_dict.items() if exact_match(v, target_mood)]

        if all_three_matches:
            # If there are multiple, choose one randomly
            result = random.choice(all_three_matches)
        else:
            # Find all entries with at least two matching emotions
            two_matches = [k for k, v in mood_dict.items() if count_matches(v, target_mood) == 2]

            if two_matches:
                # If there are multiple, choose one randomly
                result = random.choice(two_matches)
            else:
                # Find all entries with at least one matching emotion
                one_match = [k for k, v in mood_dict.items() if count_matches(v, target_mood) == 1]

                if one_match:
                    # If there are multiple, choose one randomly
                    result = random.choice(one_match)
                else:
                    result = None

        recommend_picture_list2 = []
        for i in range(len(mood_dict)):
            if result == rrow[i]['url']:
                recommend_picture_list2.append(rrow[i]['url'])
                recommend_picture_list2.append(rrow[i]['title'])
                recommend_picture_list2.append(rrow[i]['author'])

        cursor.execute("SELECT * FROM exhibitions")
        exhibition = cursor.fetchall()

        recom_exhibition = random_exhibition(exhibition)
        leaflet_color = leaflet_design(str(dominant_color))
        text_user['leaflet_design'] = leaflet_color
        
        text_user['user_rgb'] = user_rgb
        text_user['recom_picture1'] = recommend_picture_list
        text_user['recom_picture2'] = recommend_picture_list2
        text_user['spectral_key'] = [analysis_result]
        text_user['recom_exhibition'] = recom_exhibition
        return text_user
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)