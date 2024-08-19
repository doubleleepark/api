# image_utils.py
from fastapi import HTTPException
from typing import List
import requests
import cv2
import numpy as np
from io import BytesIO
from PIL import Image
from skimage.metrics import structural_similarity as ssim
from collections import defaultdict
from sklearn.cluster import SpectralClustering, KMeans
from scipy.spatial.distance import cdist
from pydantic import BaseModel, HttpUrl
import random
import json
import math

RestArt_color = {
        ((231, 47, 39), (207, 46, 49)): "Cinnabar",
        ((38, 38, 38), (10, 10, 10)): "Black",
        ((86, 86, 86), (60, 60, 60)): "Matterhorn",
        ((152, 152, 152), (126, 126, 126)): "Nobel",
        ((206, 206, 206), (180, 180, 180)): "Very Light Grey",
        ((244, 244, 244), (236, 236, 236)): "White Smoke",
        ((255, 228, 15), (255, 236, 79)): "Paris Daisy",
        ((249, 239, 189), (228, 235, 191)): "Corn Field",
        ((170, 198, 27), (169, 199, 35)): "Bahia",
        ((155, 196, 113), (255, 203, 88)): "Kournikova",
        ((146, 198, 131), (140, 195, 110)): "Gossip",
        ((255, 200, 8), (227, 189, 28)): "Tangerine Yellow",
        ((238, 113, 25), (226, 132, 45)): "Pumpkin",
        ((241, 176, 102), (242, 178, 103)): "Harvest Gold",
        ((46, 20, 141), (58, 55, 119)): "Persian Indigo",
        ((3, 86, 155), (44, 77, 143)): "Cobalt",
        ((19, 166, 50), (18, 154, 47)): "Dark Pastel Green",
        ((4, 148, 87), (43, 151, 89)): "Shamrock Green",
        ((6, 134, 84), (39, 122, 62)): "Salem",
        ((197, 188, 213), (170, 165, 199)): "Wistful",
        ((1, 134, 141), (0, 147, 159)): "Eastern Blue",
        ((171, 131, 115), (158, 128, 110)): "Brandy Rose",
        ((148, 133, 105), (144, 135, 96)): "Granite Green",
        ((219, 220, 93), (233, 227, 143)): "Manz",
        ((162, 179, 36), (195, 202, 101)): "Wild Willow",
        ((79, 46, 43), (88, 60, 50)): "Cioccolato",
        ((6, 113, 148), (59, 130, 157)): "Cerulean",
        ((88, 171, 45), (141, 188, 90)): "Chelsea Cucumber",
        ((24, 89, 63), (20, 88, 60)): "Fun Green",
        ((27, 86, 49), (18, 83, 65)): "Deep Teal",
        ((75, 63, 45), (53, 52, 48)): "Deep Bronze",
        ((44, 60, 49), (34, 62, 51)): "Timber Green",
        ((31, 56, 45), (29, 60, 47)): "Palm Green",
        ((25, 62, 63), (34, 54, 68)): "Tiber",
        ((85, 55, 43), (111, 61, 56)): "Metallic Copper",
        ((116, 47, 50), (115, 71, 79)): "Tamarillo",
        ((175, 92, 87), (162, 88, 61)): "Apple Blossom",
        ((3, 130, 122), (53, 109, 98)): "Surfie Green",
        ((211, 142, 110), (215, 145, 96)): "Feldspar",
        ((167, 100, 67), (169, 87, 49)): "Vesuvius",
        ((8, 87, 107), (16, 76, 84)): "Blue Lagoon",
        ((231, 108, 86), (233, 163, 144)): "Tonys Pink",
        ((213, 182, 166), (206, 185, 179)): "Wafer",
        ((20, 114, 48), (30, 98, 50)): "Camarone",
        ((88, 126, 61), (91, 132, 47)): "Vida Loca",
        ((54, 88, 48), (23, 106, 43)): "Green House",
        ((130, 154, 145), (133, 154, 153)): "Granny Smith",
        ((245, 223, 181), (218, 196, 148)): "Wheat",
        ((236, 217, 202), (235, 219, 224)): "Pale Rose",
        ((218, 176, 176), (205, 154, 149)): "Oyster Pink",
        ((184, 190, 189), (151, 150, 139)): "Opal",
        ((178, 137, 166), (224, 218, 230)): "London Hue",
        ((139, 117, 65), (156, 137, 37)): "Lemon Ginger",
        ((172, 36, 48), (115, 63, 44)): "Guardsman Red",
        ((204, 63, 92), (209, 100, 109)): "Mandy",
        ((160, 147, 131), (103, 91, 44)): "Costa Del Sol",
        ((92, 104, 163), (40, 57, 103)): "Chetwode Blue",
        ((221, 232, 207), (209, 234, 211)): "Aqua Squeeze",
        ((209, 116, 73), (109, 116, 73)): "Siam",
        ((179, 202, 157), (143, 162, 121)): "Sprout",
        ((166, 201, 163), (122, 165, 123)): "Oxley",
        ((126, 188, 209), (194, 222, 242)): "Seagull",
        ((127, 175, 166), (117, 173, 169)): "Gulf Stream",
        ((165, 184, 199), (138, 166, 187)): "Heather",
        ((147, 184, 213), (203, 215, 232)): "Hawkes Blue"
    }

# image_url_list = [
#     ["https://ifh.cc/g/KtVo8L.jpg", "소풍 가는 날", "강두형", "그림 속에는 다양한 색상의 꽃과 나무가 어우러진 자연 풍경이 펼쳐져 있으며, 소풍을 떠나는 세 명의 인물이 작은 크기로 묘사되어 있습니다. 전체적으로 밝고 활기찬 분위기를 통해 자연 속에서의 평화롭고 즐거운 시간을 표현하고 있습니다.", ["기쁨", "행복", "호기심"], [['Cerulean', (59, 130, 157), 0.197, 1], ['Grey', (126, 126, 126), 0.165, 1], ['Hemp', (160, 147, 131), 0.135, 1], ['Wafer', (206, 185, 179), 0.117, 1], ['Feldspar', (215, 145, 96), 0.098, 1], ['Nepal', (138, 166, 187), 0.092, 1], ['Costa Del Sol', (139, 117, 65), 0.085, 1], ['Persian Indigo', (58, 55, 119), 0.043, 1], ['Cioccolato', (88, 60, 50), 0.04, 1], ['Terra Cotta', (231, 108, 86), 0.027, 1]]],
#     ["https://ifh.cc/g/V7NpL0.jpg", "계단이 있는 풍경(10)", "강명규", "복잡하고 다채로운 구성이 특징인 작품입니다. 다양한 요소들이 계단을 중심으로 복잡하게 얽혀 있으며, 자연과 인공 구조물이 혼합된 독특한 풍경을 그려내고 있습니다. 세밀한 묘사와 다채로운 색채가 어우러져 보는 이로 하여금 깊은 관찰을 유도합니다.", ["호기심", "혼란", "감각적"], [['White Smoke', (244, 244, 244), 0.375, 1], ['Cioccolato', (75, 63, 45), 0.201, 2], ['Grey', (86, 86, 86), 0.191, 3], ['Black', (38, 38, 38), 0.102, 1], ['Costa Del Sol', (103, 91, 44), 0.057, 1], ['Very Light Grey', (206, 206, 206), 0.047, 1], ['Pumpkin', (226, 132, 45), 0.028, 1]]],
#     ["https://ifh.cc/g/B98zDj.jpg", "코봉이", "작가 미상", "그림 속에는 작고 귀여운 상자 안에 앉아 있는 흰 고양이가 묘사되어 있습니다. 고양이의 한쪽 눈 옆에 검은 반점이 있어 독특한 외모를 자랑합니다. 전체적으로 차분한 초록색 배경이 고양이의 밝은 색을 돋보이게 하며, 평화롭고 귀여운 분위기를 자아냅니다.", ["호기심", "행복", "사랑"], [['Grey', (86, 86, 86), 0.33, 3], ['Green House', (54, 88, 48), 0.317, 1], ['Genoa', (53, 109, 98), 0.216, 1], ['Pale Rose', (235, 219, 224), 0.045, 1], ['Very Light Grey', (206, 206, 206), 0.039, 1], ['Hemp', (158, 128, 110), 0.02, 1], ['Cioccolato', (115, 63, 44), 0.02, 1], ['Black', (38, 38, 38), 0.012, 1]]],
#     ["https://ifh.cc/g/BO4lV4.jpg", "ILLUSION", "강미리", "이 작품은 다양한 색상이 어우러진 추상적인 그림입니다. 녹색, 노란색, 보라색의 물감이 흘러내리는 듯한 느낌으로 표현되어 있으며, 복잡하고 미묘한 분위기를 자아냅니다. 전체적으로 감각적이고 미스테리한 느낌을 주어 보는 이로 하여금 다양한 해석을 불러일으킵니다.", ["감각적", "호기심", "혼란"], [['Black', (10, 10, 10), 0.433, 2], ['Deep Koamaru', (34, 54, 68), 0.091, 1], ['Dingley', (88, 126, 61), 0.088, 1], ['Cioccolato', (79, 46, 43), 0.087, 1], ['Sherpa Blue', (16, 76, 84), 0.084, 1], ['Costa Del Sol', (139, 117, 65), 0.068, 1], ['Paris Daisy', (255, 236, 79), 0.058, 1], ['Yellow', (155, 196, 113), 0.054, 1], ['Corn Field', (245, 223, 181), 0.038, 1]]],
#     ["https://ifh.cc/g/HHbymY.jpg", "NY-Empire State Building", "강병섭", "이 작품은 뉴욕의 상징적인 엠파이어 스테이트 빌딩을 다채로운 색상으로 표현한 그림입니다. 빌딩과 주변 건물들은 밝고 다양한 색으로 채색되어 있으며, 배경의 파스텔 톤이 도시의 활기찬 분위기를 돋보이게 합니다. 전체적으로 도시의 에너지와 현대적인 미감을 잘 나타내고 있습니다.", ["세련됨", "감각적", "기쁨"], [['Pale Rose', (235, 219, 224), 0.266, 1], ['Hawkes Blue', (203, 215, 232), 0.166, 1], ['Feldspar', (211, 142, 110), 0.135, 1], ['Corn Field', (245, 223, 181), 0.127, 1], ['Seagull', (126, 188, 209), 0.11, 1], ['Yellow', (255, 203, 88), 0.072, 1], ['Eastern Blue', (0, 147, 159), 0.062, 2], ['Very Light Grey', (180, 180, 180), 0.047, 1], ['Mantis', (141, 188, 90), 0.015, 1]]],
#     ["https://ifh.cc/g/Onvzhn.jpg", "축적산수 1-04", "강보경", "이 작품은 강렬한 붉은색과 검은색이 어우러진 추상적인 그림입니다. 거친 붓질과 색감이 강한 대조를 이루며, 감정의 격동을 표현하는 듯한 인상을 줍니다. 전체적으로 혼란스럽고 격정적인 분위기를 자아내어 보는 이로 하여금 강한 감정을 느끼게 합니다.", ["혼란", "노여움", "공포"], [['Grey', (86, 86, 86), 0.315, 3], ['Black', (60, 60, 60), 0.174, 1], ['Tosca', (115, 71, 79), 0.172, 2], ['Pale Sky', (92, 104, 106), 0.141, 1], ['Cabaret', (209, 100, 109), 0.104, 1], ['Au Chico', (175, 97, 87), 0.083, 1], ['Titan White', (224, 218, 230), 0.01, 1]]],
#     ["https://ifh.cc/g/N5XrYw.jpg", "빛과 생명의 어머니", "강상중", "이 작품은 밝고 다채로운 색상으로 구성된 기하학적 패턴과 자연 요소가 어우러진 그림입니다. 중심에 있는 태양 모양의 문양이 주목을 끌며, 주변에는 식물과 동물이 조화롭게 배치되어 있습니다. 전체적으로 활기차고 생명력이 넘치는 분위기를 전달하며, 자연의 아름다움과 신비를 표현하고 있습니다.", ["행복", "기쁨", "호기심"], [['Yellow', (227, 189, 28), 0.335, 1], ['Bahia', (195, 202, 101), 0.145, 1], ['Very Light Grey', (180, 180, 180), 0.1, 1], ['Mantis', (140, 195, 110), 0.086, 1], ['Rose', (218, 176, 176), 0.07, 1], ['Feldspar', (211, 142, 110), 0.064, 1], ['Granny Smith', (133, 154, 153), 0.062, 1], ['Pumpkin', (226, 132, 45), 0.053, 1], ['Terra Cotta', (231, 108, 86), 0.052, 1], ['Tosca', (115, 71, 79), 0.033, 1]]],
#     ["https://ifh.cc/g/BV6vbw.jpg", "빛을 쫓는 사람", "강상중", "이 작품은 다양한 색상과 기하학적 형태를 통해 사람의 형상을 추상적으로 표현하고 있습니다. 중심에는 원형과 인물들이 배치되어 있으며, 선명한 색상들이 어우러져 역동적이고 에너지 넘치는 분위기를 자아냅니다. 전체적으로 사람의 움직임과 빛을 쫓는 동작을 통해 삶의 활력과 희망을 상징적으로 보여줍니다.", ["호기심", "기쁨", "세련됨"], [['Rose', (218, 176, 176), 0.227, 1], ['London Hue', (178, 137, 166), 0.168, 1], ['Cerulean', (59, 130, 157), 0.128, 1], ['Seagull', (126, 188, 209), 0.125, 1], ['Bahia', (195, 202, 101), 0.108, 1], ['Spring Rain', (166, 201, 163), 0.071, 1], ['Genoa', (53, 109, 98), 0.06, 1], ['Oxley', (122, 165, 123), 0.057, 1], ['Frostee', (221, 232, 207), 0.046, 1], ['Guardsman Red', (172, 35, 48), 0.01, 1]]],
#     ["https://ifh.cc/g/fBHnxF.jpg", "후리지아가 있는 찻잔", "강석태", "이 작품은 찻잔 안에 담긴 후리지아 꽃들과 노란 하트 모양이 눈에 띄는 그림입니다. 다양한 색상의 꽃들이 배경과 찻잔 주위에 가득 채워져 있으며, 밝고 활기찬 분위기를 자아냅니다. 전체적으로 사랑스럽고 따뜻한 느낌을 주며, 행복과 기쁨을 느끼게 합니다.", ["행복", "기쁨", "사랑"], [['Black', (38, 38, 38), 0.204, 1], ['Granny Smith', (130, 154, 145), 0.147, 1], ['Heather', (165, 184, 199), 0.13, 1], ['Grey', (86, 86, 86), 0.118, 1], ['Eastern Blue', (117, 173, 169), 0.116, 2], ['London Hue', (178, 137, 166), 0.085, 1], ['Yellow', (227, 189, 28), 0.08, 1], ['Cabaret', (209, 100, 109), 0.072, 1], ['Forest Green', (18, 154, 47), 0.047, 1]]],
#     ["https://ifh.cc/g/3BfzBc.jpg", "Dream of Memories Ⅴ", "강양순", "이 작품은 초록색 배경 위에 세 마리의 말이 생동감 있게 달리는 모습을 묘사하고 있습니다. 각 말은 다양한 패턴과 색상으로 표현되어 있으며, 배경의 꽃과 나무들이 조화롭게 어우러져 있습니다. 전체적으로 자연의 활기와 자유로움을 표현하며, 역동적이고 감각적인 분위기를 자아냅니다.", ["기쁨", "세련됨", "호기심"], [['Cerulean', (59, 130, 157), 0.224, 2], ['Salem', (43, 151, 89), 0.137, 1], ['White Smoke', (236, 236, 236), 0.136, 1], ['Mantis', (140, 195, 110), 0.131, 1], ['Eastern Blue', (117, 173, 169), 0.091, 1], ['Very Light Grey', (184, 190, 189), 0.089, 1], ['Black', (38, 38, 38), 0.07, 1], ['Genoa', (53, 109, 98), 0.068, 1], ['Granny Smith', (133, 154, 153), 0.054, 1]]],
#     ["https://ifh.cc/g/KTPW4h.jpg", "In Paradise - Freedom of Ego Ⅲ", "강양순", "이 작품은 다양한 패턴과 색상으로 장식된 말과 꽃들이 조화롭게 어우러진 모습을 담고 있습니다. 노란 배경에 화려한 장식들이 더해져 생동감 있고 화려한 분위기를 자아냅니다. 전체적으로 개성과 자유를 상징하며, 작품 속 요소들이 어우러져 감각적이고 세련된 느낌을 줍니다.", ["세련됨", "감각적", "호기심"], [['Black', (38, 38, 38), 0.282, 2], ['Corn Field', (233, 227, 143), 0.248, 1], ['Grey', (86, 86, 86), 0.199, 3], ['Wistful', (197, 188, 213), 0.117, 1], ['Clam Shell', (213, 182, 166), 0.076, 1], ['Pale Rose', (235, 219, 224), 0.049, 1], ['Cerulean', (59, 130, 157), 0.03, 1]]],
#     ["https://ifh.cc/g/m7Kr0V.jpg", "In Paradise - Harmony Ⅰ", "강양순", "이 작품은 노란 장미와 말이 어우러진 장면을 담고 있습니다. 배경의 화사한 노란색과 꽃들은 밝고 행복한 분위기를 자아내며, 말들은 평화롭게 표현되어 있습니다. 전체적으로 자연의 아름다움과 조화로움을 나타내며, 생동감과 기쁨을 전달합니다.", ["기쁨", "행복", "사랑"], [['Yellow', (227, 189, 28), 0.202, 1], ['Costa Del Sol', (103, 91, 44), 0.151, 1], ['Lemon Ginger', (156, 137, 37), 0.098, 1], ['Cioccolato', (75, 63, 45), 0.094, 1], ['Manz', (219, 220, 93), 0.089, 1], ['Very Light Grey', (180, 180, 180), 0.089, 1], ['Titan White', (224, 218, 230), 0.087, 1], ['Hemp', (160, 147, 131), 0.078, 1], ['Granite Green', (109, 116, 73), 0.059, 1], ['Black', (38, 38, 38), 0.052, 1]]],
#     ["https://ifh.cc/g/TdZo4p.jpg", "시간과 공간 - Summer Scent Ⅰ", "강양순", "이 작품은 거대한 해바라기와 이를 감상하는 여인의 모습을 담고 있습니다. 여인은 해바라기와 함께 자연 속에서 여유를 즐기며 평화로운 분위기를 자아냅니다. 화사한 색감과 생동감 넘치는 묘사를 통해 여름의 따뜻함과 자연의 아름다움을 표현하고 있습니다.", ["행복", "기쁨", "사랑"], [['Frostee', (221, 232, 207), 0.167, 1], ['Yellow', (227, 189, 28), 0.124, 1], ['Fun Green', (27, 86, 49), 0.115, 1], ['Manz', (219, 220, 93), 0.108, 1], ['Tuscany', (169, 87, 49), 0.093, 1], ['Granite Green', (144, 135, 96), 0.091, 1], ['Costa Del Sol', (103, 91, 44), 0.086, 1], ['Spring Rain', (166, 201, 163), 0.077, 1], ['Camarone', (39, 122, 62), 0.072, 1], ['Oxley', (122, 165, 123), 0.068, 1]]],
#     ["https://ifh.cc/g/Pkdahy.jpg", "고요한 풍경", "강정희", "이 작품은 푸르른 나무와 그 주변의 잔잔한 풍경을 담고 있습니다. 섬세한 붓질과 부드러운 색채가 어우러져 평화롭고 고요한 분위기를 자아냅니다. 전체적으로 자연의 조화와 아름다움을 표현하며, 보는 이에게 차분한 감정을 전달합니다.", ["평화", "행복", "사랑"], [['Very Light Grey', (184, 190, 189), 0.581, 3], ['Granny Smith', (130, 154, 145), 0.09, 1], ['Dingley', (88, 126, 61), 0.07, 1], ['Oxley', (122, 165, 123), 0.07, 1], ['Sprout', (179, 202, 157), 0.066, 1], ['Green House', (54, 88, 48), 0.054, 1], ['Mantis', (141, 188, 90), 0.04, 1], ['Palm Green', (31, 56, 45), 0.027, 1]]],
#     ["https://ifh.cc/g/JfftWD.jpg", "눈부신 행복", "강정희", "이 작품은 밝은 노란색 나무가 중심을 이루고 있으며, 나무는 풍성한 잎으로 가득 차 있습니다. 따뜻한 색감과 부드러운 배경이 조화를 이루며, 전체적으로 평화롭고 행복한 분위기를 자아냅니다. 자연의 아름다움과 생동감을 표현하며, 보는 이로 하여금 행복을 느끼게 합니다.", ["행복", "기쁨", "사랑"], [['Yellow', (227, 189, 28), 0.365, 3], ['Very Light Grey', (206, 206, 206), 0.254, 1], ['Pumpkin', (238, 113, 25), 0.171, 2], ['Bahia', (195, 202, 101), 0.075, 1], ['Raffia', (218, 196, 148), 0.061, 1], ['Clam Shell', (213, 182, 166), 0.059, 1], ['Tuscany', (169, 87, 49), 0.015, 1]]],
#     ["https://ifh.cc/g/rfCMcL.jpg", "똑같이 행복하게", "강정희", "이 작품은 가을의 숲을 배경으로 하며, 밝은 노란색과 붉은색이 어우러진 나무들이 일렬로 서 있습니다. 따뜻한 색조와 조화로운 구성이 숲의 아름다움을 강조하며, 전체적으로 밝고 행복한 분위기를 자아냅니다. 자연 속에서의 평화로운 순간을 표현하고 있습니다.", ["행복", "기쁨", "평화"], [['Yellow', (255, 203, 88), 0.205, 2], ['Pumpkin', (226, 132, 45), 0.197, 2], ['Terra Cotta', (231, 108, 86), 0.148, 1], ['Feldspar', (215, 145, 96), 0.13, 1], ['Raffia', (218, 196, 148), 0.126, 1], ['Corn Field', (249, 239, 189), 0.102, 1], ['Cinnabar', (231, 47, 39), 0.07, 1], ['Cioccolato', (115, 63, 44), 0.022, 1]]],
#     ["https://ifh.cc/g/APHqQs.jpg", "반영된 즐거움", "강정희", "이 작품은 푸른 하늘 아래 밝게 빛나는 노란 나무를 중심으로 합니다. 나무는 풍성한 잎으로 가득 차 있으며, 밝고 따뜻한 색감이 자연의 생동감을 잘 나타내고 있습니다. 전체적으로 즐겁고 긍정적인 분위기를 통해 자연 속에서의 기쁨을 표현하고 있습니다.", ["행복", "기쁨", "사랑"], [['Yellow', (227, 189, 28), 0.441, 2], ['Cerulean', (59, 130, 157), 0.177, 2], ['Corn Field', (233, 227, 143), 0.113, 1], ['Bahia', (162, 179, 36), 0.095, 1], ['Forest Green', (88, 171, 45), 0.065, 1], ['Dingley', (91, 132, 47), 0.044, 1], ['Spring Rain', (166, 201, 163), 0.04, 1], ['Tuscany', (169, 87, 49), 0.025, 1]]],
#     ["https://ifh.cc/g/oY2K9B.jpg", "청산에...", "강정희", "이 작품은 푸른 산과 물이 어우러진 고요한 자연 풍경을 담고 있습니다. 짙은 초록색의 나무와 푸른 산이 대조를 이루며, 물은 맑고 투명하게 표현되었습니다. 전체적으로 평화롭고 차분한 분위기를 통해 자연의 고요함과 아름다움을 강조하고 있습니다.", ["평화", "경외심", "감각적"], [['Cerulean', (59, 130, 157), 0.364, 4], ['Salem', (6, 134, 84), 0.234, 2], ['Seagull', (126, 188, 209), 0.166, 2], ['Hawkes Blue', (203, 215, 232), 0.159, 1], ['Fun Green', (18, 83, 65), 0.077, 1]]],
#     ["https://ifh.cc/g/YA047K.jpg", "평화로운 숲속 길", "강정희", "이 작품은 노란색으로 물든 나무들이 가득한 숲속 길을 담고 있습니다. 나무들이 일렬로 서 있으며, 부드러운 색채와 함께 고요하고 평화로운 분위기를 자아냅니다. 전체적으로 자연 속에서의 평화와 안정을 느끼게 하며, 숲의 따뜻함과 아름다움을 강조하고 있습니다.", ["평화", "행복", "사랑"], [['Bahia', (195, 202, 101), 0.312, 3], ['Yellow', (227, 189, 28), 0.304, 2], ['Pumpkin', (226, 132, 45), 0.107, 1], ['Sprout', (179, 202, 157), 0.093, 1], ['Very Light Grey', (184, 190, 189), 0.078, 1], ['Feldspar', (215, 145, 96), 0.072, 1], ['Lemon Ginger', (156, 137, 37), 0.033, 1]]],
#     ["https://ifh.cc/g/HHQsh1.jpg", "하늘빛 좋은 날 - 푸른 솔 3", "강정희", "이 작품은 맑은 하늘 아래 푸른 소나무가 한가롭게 서 있는 모습을 담고 있습니다. 소나무는 푸른 바다와 조화롭게 어우러져 고요하고 평화로운 분위기를 자아냅니다. 전체적으로 자연의 고요함과 아름다움을 강조하며, 소나무의 강인한 생명력을 느끼게 합니다.", ["평화", "경외심", "감각적"], [['Nepal', (147, 184, 213), 0.279, 2], ['Seagull', (126, 188, 209), 0.273, 1], ['Hawkes Blue', (203, 215, 232), 0.181, 1], ['White Smoke', (236, 236, 236), 0.099, 1], ['Eastern Blue', (117, 173, 169), 0.045, 1], ['Genoa', (53, 109, 98), 0.04, 1], ['Fun Green', (24, 89, 63), 0.04, 1], ['Granny Smith', (127, 175, 166), 0.026, 1], ['Palm Green', (31, 56, 45), 0.018, 1]]],
#     ["https://ifh.cc/g/Dz3Dyq.jpg", "행복한 시간 2", "강정희", "이 작품은 푸른 나무들이 모여 있는 풍경을 담고 있습니다. 나무들은 선명한 푸른색으로 표현되어 차분하면서도 신비로운 분위기를 자아냅니다. 전체적으로 평화롭고 고요한 자연의 아름다움을 강조하며, 행복하고 안정된 감정을 전달합니다.", ["평화", "행복", "경외심"], [['Cerulean', (59, 130, 157), 0.32, 3], ['Nepal', (147, 184, 213), 0.168, 2], ['White Smoke', (236, 236, 236), 0.144, 1], ['Pattens Blue', (194, 222, 242), 0.128, 1], ['Seagull', (126, 188, 209), 0.101, 1], ['Eastern Blue', (117, 173, 169), 0.073, 1], ['Cobalt', (3, 86, 155), 0.067, 1]]],
#     ["https://ifh.cc/g/2dfknt.jpg", "an invisible thing", "강지연", "이 작품은 사막 한가운데 있는 나무를 중심으로 다양한 상자와 물건들이 어우러진 풍경을 담고 있습니다. 나무 위에는 여우와 고양이가 앉아 있으며, 하늘에는 여러 가지 상징적인 요소들이 떠다니고 있습니다. 전체적으로 신비롭고 몽환적인 분위기를 자아내며, 상상력과 호기심을 자극합니다.", ["호기심", "신비로움", "감각적"], [['Very Light Grey', (206, 206, 206), 0.277, 1], ['White Smoke', (236, 236, 236), 0.169, 1], ['Harvest Gold', (242, 178, 103), 0.156, 1], ['Wafer', (206, 185, 179), 0.123, 1], ['Corn Field', (245, 223, 181), 0.071, 1], ['Feldspar', (215, 145, 96), 0.067, 1], ['Dingley', (91, 132, 47), 0.044, 1], ['Forest Green', (88, 171, 45), 0.036, 1], ['Tuscany', (167, 100, 67), 0.034, 1], ['Granny Smith', (133, 154, 153), 0.022, 1]]],
#     ["https://ifh.cc/g/DgrlJL.jpg", "deep down in the heart", "강지연", "이 작품은 커다란 나무와 그 아래 위치한 집을 중심으로 한 풍경을 담고 있습니다. 나무는 무성한 잎과 열매로 가득 차 있으며, 주변에는 사람들이 다양한 활동을 하고 있습니다. 전체적으로 따뜻하고 평화로운 분위기를 자아내며, 자연과 인간의 조화로운 삶을 표현하고 있습니다.", ["평화", "행복", "사랑"], [['White Smoke', (244, 244, 244), 0.278, 1], ['Corn Field', (245, 223, 181), 0.172, 1], ['Frostee', (221, 232, 207), 0.171, 1], ['Raffia', (218, 196, 148), 0.124, 1], ['Bahia', (195, 202, 101), 0.082, 1], ['Mantis', (141, 188, 90), 0.064, 1], ['Hemp', (171, 131, 115), 0.038, 1], ['Costa Del Sol', (139, 117, 65), 0.036, 1], ['Cioccolato', (79, 46, 43), 0.025, 1], ['Tuscany', (169, 87, 49), 0.01, 1]]],
#     ["https://ifh.cc/g/Xk9cJ0.jpg", "without my knowledge", "강지연", "이 작품은 나무 아래와 주위에 다양한 물건들이 어우러진 풍경을 담고 있습니다. 나무 위에는 토끼 인형이 놓여 있으며, 주변에는 카드, 책, 상자 등 다양한 요소들이 날아다니고 있습니다. 전체적으로 신비롭고 몽환적인 분위기를 자아내며, 상상력과 호기심을 자극합니다.", ["호기심", "신비로움", "감각적"], [['White Smoke', (244, 244, 244), 0.171, 1], ['Rose', (205, 154, 149), 0.15, 1], ['Hawkes Blue', (203, 215, 232), 0.144, 1], ['Raffia', (218, 196, 148), 0.137, 1], ['Dingley', (88, 126, 61), 0.107, 1], ['Mantis', (141, 188, 90), 0.074, 1], ['Granny Smith', (127, 175, 166), 0.07, 1], ['Tuscany', (167, 100, 67), 0.067, 1], ['Green House', (54, 88, 48), 0.046, 1], ['Cobalt', (44, 77, 143), 0.034, 1]]],
#     ["https://ifh.cc/g/vlSONA.jpg", "고민하는 사람들을 위한 밤", "강지연", "이 작품은 밤하늘 아래 다채로운 물건들이 모여 있는 장면을 묘사하고 있습니다. 다양한 음식을 비롯한 여러 가지 요소들이 어우러져 몽환적이고 신비로운 분위기를 자아냅니다. 전체적으로 따뜻한 색감과 복잡한 구성이 어우러져 상상력과 호기심을 자극합니다.", ["호기심", "신비로움", "감각적"], [['Black', (10, 10, 10), 0.382, 3], ['Very Light Grey', (206, 206, 206), 0.224, 2], ['White Smoke', (236, 236, 236), 0.187, 1], ['Raffia', (218, 196, 148), 0.07, 1], ['Feldspar', (211, 142, 110), 0.057, 1], ['Grey', (126, 126, 126), 0.052, 1], ['Tuscany', (162, 88, 61), 0.028, 1]]],
#     ["https://ifh.cc/g/bsx2AQ.jpg", "찬장", "강지혜", "이 작품은 전통적인 찬장 속에 가지런히 정리된 그릇과 컵들을 묘사하고 있습니다. 나무 질감의 찬장은 따뜻하고 고요한 분위기를 자아내며, 각종 식기들은 정돈된 느낌을 줍니다. 전체적으로 차분하고 평화로운 분위기를 통해 일상의 소소한 아름다움을 표현하고 있습니다.", ["평화", "감각적", "행복"], [['Cioccolato', (115, 63, 44), 0.294, 2], ['Black', (38, 38, 38), 0.268, 2], ['Tamarillo', (116, 47, 50), 0.255, 1], ['Grey', (152, 152, 152), 0.062, 2], ['Very Light Grey', (206, 206, 206), 0.044, 1], ['Tuscany', (162, 88, 61), 0.042, 1], ['Hemp', (148, 133, 105), 0.034, 1]]],
#     ["https://ifh.cc/g/vwR6Qb.jpg", "춘하추동 #4.겨울", "강현정", "이 작품은 겨울의 풍경을 추상적으로 표현하고 있습니다. 그림 중앙에는 다양한 자연 요소들이 어우러져 있으며, 검은색과 푸른색이 대조를 이루어 차가운 겨울의 분위기를 자아냅니다. 전체적으로 신비롭고 감각적인 느낌을 주며, 겨울의 정취를 표현하고 있습니다.", ["감각적", "경외심", "신비로움"], [['White Smoke', (244, 244, 244), 0.53, 1], ['Black', (60, 60, 60), 0.142, 2], ['Hawkes Blue', (203, 215, 232), 0.107, 1], ['Very Light Grey', (184, 190, 189), 0.075, 1], ['Pale Sky', (92, 104, 106), 0.061, 1], ['Granny Smith', (130, 154, 145), 0.057, 1], ['Cerulean', (59, 130, 157), 0.015, 1], ['Cinnabar', (207, 46, 49), 0.006, 1], ['Bahia', (195, 202, 101), 0.006, 1]]],
#     ["https://ifh.cc/g/WBz2R2.jpg", "무제-2020RW", "강혜원", "이 작품은 강렬한 색채와 복잡한 선들이 어우러진 추상화입니다. 빨강, 주황, 노랑 등의 색상이 혼합되어 역동적이고 에너지 넘치는 분위기를 자아냅니다. 전체적으로 혼란스럽고 격정적인 감정을 표현하며, 강렬한 시각적 인상을 줍니다.", ["혼란", "감각적", "노여움"], [['Cinnabar', (207, 46, 49), 0.197, 1], ['Black', (10, 10, 10), 0.152, 1], ['Heather', (165, 184, 199), 0.139, 1], ['Guardsman Red', (172, 35, 48), 0.125, 1], ['Cioccolato', (79, 46, 43), 0.118, 1], ['Feldspar', (215, 145, 96), 0.074, 1], ['Yellow', (227, 189, 28), 0.064, 1], ['Costa Del Sol', (139, 117, 65), 0.058, 1], ['Bahia', (195, 202, 101), 0.048, 1], ['Grey', (126, 126, 126), 0.024, 1]]],
#     ["https://ifh.cc/g/wh8Okj.jpg", "Communion 02", "강호연", "이 작품은 밝은 노란색 배경에 추상적인 형태들이 어우러진 그림입니다. 파란색, 검은색, 빨간색 등의 형태들이 조화롭게 배치되어 있으며, 작품 전체에 역동적이고 에너지 넘치는 느낌을 줍니다. 단순한 선과 색감의 조화가 돋보이며, 감각적이고 현대적인 분위기를 자아냅니다.", ["감각적", "호기심", "세련됨"], [['White Smoke', (244, 244, 244), 0.453, 1], ['Paris Daisy', (255, 236, 79), 0.357, 1], ['Sherpa Blue', (8, 87, 107), 0.083, 1], ['Black', (10, 10, 10), 0.035, 1], ['Yellow', (255, 203, 88), 0.031, 1], ['Cinnabar', (207, 46, 49), 0.011, 1], ['Corn Field', (245, 223, 181), 0.011, 1], ['Green House', (54, 88, 48), 0.009, 1], ['Cerulean', (59, 130, 157), 0.005, 1], ['Feldspar', (215, 145, 96), 0.005, 1]]],
#     ["https://ifh.cc/g/vYzjwJ.jpg", "Communion 03", "강호연", "이 작품은 추상적인 형태와 색상이 어우러진 그림으로, 노란색과 파란색 배경 위에 다양한 형태들이 조화를 이루고 있습니다. 검은색과 초록색 등의 형태들이 배치되어 있으며, 간결한 선과 색감이 돋보입니다. 전체적으로 현대적이고 세련된 분위기를 자아내며, 감각적이고 조화로운 느낌을 줍니다.", ["세련됨", "감각적", "호기심"], [['White Smoke', (236, 236, 236), 0.601, 2], ['Titan White', (224, 218, 230), 0.153, 1], ['Manz', (219, 220, 93), 0.148, 1], ['Cobalt', (44, 77, 143), 0.041, 1], ['Black', (60, 60, 60), 0.022, 1], ['Genoa', (53, 109, 98), 0.011, 1], ['Bahia', (162, 179, 36), 0.009, 1], ['Corn Field', (233, 227, 143), 0.008, 1], ['Nepal', (138, 166, 187), 0.007, 1]]],
#     ["https://ifh.cc/g/HvbApA.jpg", "peony", "강희주", "이 작품은 다양한 색상과 패턴이 어우러진 화려한 작약 꽃을 중심으로 한 그림입니다. 섬세한 디테일과 다채로운 색감이 돋보이며, 배경의 꽃무늬와 조화롭게 어우러져 있습니다. 전체적으로 생동감 넘치는 분위기를 자아내며, 자연의 아름다움을 화려하게 표현하고 있습니다.", ["감각적", "세련됨", "기쁨"], [['Very Light Grey', (184, 190, 189), 0.379, 2], ['Nepal', (138, 166, 187), 0.138, 1], ['Rose', (205, 154, 149), 0.103, 1], ['Hemp', (158, 128, 110), 0.09, 1], ['Costa Del Sol', (139, 117, 65), 0.077, 1], ['Grey', (126, 126, 126), 0.064, 1], ['Genoa', (53, 109, 98), 0.06, 1], ['Black', (38, 38, 38), 0.049, 1], ['Cioccolato', (88, 60, 50), 0.041, 1]]],
#     ["https://ifh.cc/g/LfvBKX.jpg", "Rose", "강희주", "이 작품은 다채로운 색상과 패턴으로 장식된 장미를 중심으로 한 그림입니다. 화려한 디테일과 풍부한 색감이 돋보이며, 배경의 꽃무늬와 조화를 이루고 있습니다. 전체적으로 우아하고 화려한 분위기를 자아내며, 자연의 아름다움을 세련되게 표현하고 있습니다.", ["세련됨", "감각적", "기쁨"], [['Grey', (152, 152, 152), 0.567, 3], ['Nepal', (138, 166, 187), 0.087, 1], ['Pale Sky', (92, 104, 106), 0.076, 1], ['Cerulean', (59, 130, 157), 0.073, 1], ['Persian Indigo', (58, 55, 119), 0.066, 1], ['Black', (38, 38, 38), 0.055, 1], ['Hemp', (158, 128, 110), 0.054, 1], ['Tamarillo', (111, 61, 56), 0.023, 1]]],
#     ["https://ifh.cc/g/VdTgBm.jpg", "WHITE DEER-PROTECTIVE COLORING_Decalcomanie", "고원태", "이 작품은 검은색과 흰색 배경으로 나뉜 사슴의 모습을 담고 있습니다. 사슴의 뿔은 나뭇가지 형태로 표현되었으며, 대조적인 배경이 인상적입니다. 전체적으로 신비롭고 감각적인 분위기를 자아내며, 자연과 동물의 조화로움을 표현하고 있습니다.", ["감각적", "호기심", "신비로움"], [['White Smoke', (244, 244, 244), 0.404, 1], ['Cioccolato', (75, 63, 45), 0.322, 2], ['Grey', (86, 86, 86), 0.191, 3], ['Very Light Grey', (206, 206, 206), 0.034, 2], ['Titan White', (224, 218, 230), 0.028, 1], ['Black', (38, 38, 38), 0.02, 1]]],
#     ["https://ifh.cc/g/sys5mz.jpg", "WHITE DEER-PROTECTIVE COLORING_Gold rain", "고원태", "이 작품은 황금빛 비가 내리는 장면 속에 서 있는 사슴을 묘사하고 있습니다. 사슴의 뿔은 나뭇가지처럼 그려져 있으며, 황금빛 배경이 따뜻하고 화려한 분위기를 자아냅니다. 전체적으로 자연의 아름다움과 신비로움을 표현하며, 감각적이고 우아한 느낌을 줍니다.", ["신비로움", "감각적", "우아함"], [['Titan White', (224, 218, 230), 0.477, 2], ['White Smoke', (236, 236, 236), 0.339, 1], ['Very Light Grey', (206, 206, 206), 0.116, 2], ['Almond', (236, 217, 202), 0.036, 1], ['Grey', (152, 152, 152), 0.014, 1], ['Raffia', (218, 196, 148), 0.01, 1], ['Pale Sky', (92, 104, 106), 0.006, 1], ['Black', (38, 38, 38), 0.003, 1]]],
#     ["https://ifh.cc/g/zwxOAA.jpg", "WHITE DEER-첫눈이 내리고", "고원태", "이 작품은 첫눈이 내린 숲속에 서 있는 나무들을 묘사하고 있습니다. 눈 덮인 풍경은 차분하고 평화로운 분위기를 자아내며, 겨울의 고요함을 잘 표현하고 있습니다. 전체적으로 차분하고 고요한 느낌을 주며, 자연의 아름다움을 강조합니다.", ["평화", "고요함", "감각적"], [['Almond', (236, 217, 202), 0.346, 2], ['White Smoke', (236, 236, 236), 0.338, 2], ['Black', (10, 10, 10), 0.101, 2], ['Very Light Grey', (206, 206, 206), 0.097, 1], ['Heather', (165, 184, 199), 0.083, 1], ['Grey', (152, 152, 152), 0.02, 1], ['Pale Sky', (92, 104, 106), 0.015, 1]]],
#     ["https://ifh.cc/g/2oVOCj.jpg", "그리운 날에", "고재군", "이 작품은 일렬로 서 있는 키 큰 나무들과 그 사이로 달리는 버스를 묘사하고 있습니다. 푸른 나무들과 넓은 하늘이 어우러져 평화롭고 고요한 분위기를 자아내며, 버스는 이동과 여정을 상징합니다. 전체적으로 고요한 자연의 아름다움과 그리움을 표현하고 있습니다.", ["평화", "경외심", "고요함"], [['Hawkes Blue', (203, 215, 232), 0.23, 1], ['Black', (10, 10, 10), 0.217, 2], ['Wistful', (197, 188, 213), 0.143, 1], ['Very Light Grey', (180, 180, 180), 0.116, 1], ['Deep Koamaru', (34, 54, 68), 0.068, 1], ['Granny Smith', (130, 154, 145), 0.067, 1], ['Grey', (152, 152, 152), 0.062, 1], ['Genoa', (53, 109, 98), 0.054, 1], ['Pale Sky', (92, 104, 106), 0.043, 1]]],
#     ["https://ifh.cc/g/nkyBd0.jpg", "그리운 날에01", "고재군", "이 작품은 푸른 들판과 두 그루의 나무, 그리고 그 사이로 달리는 버스를 담고 있습니다. 넓은 들판과 하늘이 어우러져 광활한 풍경을 자아내며, 버스는 이동과 여행의 상징으로 나타나 있습니다. 전체적으로 평온하고 고요한 분위기를 통해 자연의 웅장함과 아름다움을 강조하고 있습니다.", ["평화", "경외심", "고요함"], [['Titan White', (224, 218, 230), 0.473, 2], ['Very Light Grey', (206, 206, 206), 0.309, 2], ['Black', (44, 60, 49), 0.12, 2], ['Palm Green', (31, 56, 45), 0.059, 1], ['Green House', (54, 88, 48), 0.035, 1], ['Grey', (152, 152, 152), 0.003, 1], ['Pale Sky', (92, 104, 106), 0.002, 1]]],
#     ["https://ifh.cc/g/Dw00OP.jpg", "그리운 날에05", "고재군", "이 작품은 빨간 꽃나무와 그 앞에 서 있는 버스를 묘사하고 있습니다. 강렬한 빨간색이 인상적이며, 나무와 버스가 대조를 이루어 독특한 분위기를 자아냅니다. 전체적으로 색감의 대조와 자연의 아름다움을 강조하며, 경외심과 감탄을 불러일으킵니다.", ["경외심", "감각적", "호기심"], [['White Smoke', (244, 244, 244), 0.159, 1], ['Cioccolato', (88, 60, 50), 0.155, 2], ['Mandy', (204, 63, 92), 0.141, 1], ['Guardsman Red', (172, 35, 48), 0.134, 1], ['Tamarillo', (116, 47, 50), 0.106, 1], ['Tosca', (115, 71, 79), 0.104, 1], ['Cabaret', (209, 100, 109), 0.07, 1], ['Black', (38, 38, 38), 0.07, 1], ['Hemp', (171, 131, 115), 0.061, 1]]],
#     ["https://ifh.cc/g/j8HF0B.jpg", "그리운 날에12", "고재군", "이 작품은 밤하늘 아래 푸른 들판과 그 사이로 달리는 버스를 담고 있습니다. 어둠 속에서도 버스는 희미한 빛을 내며, 전체적으로 고요하고 신비로운 분위기를 자아냅니다. 자연 속에서의 평온함과 경외심을 느끼게 하는 작품입니다.", ["평화", "신비로움", "경외심"], [['Seagull', (126, 188, 209), 0.829, 4], ['Black', (38, 38, 38), 0.066, 1], ['Genoa', (53, 109, 98), 0.039, 1], ['Deep Koamaru', (34, 54, 68), 0.033, 1], ['Cobalt', (44, 77, 143), 0.017, 1], ['Cerulean', (59, 130, 157), 0.012, 1], ['Grey', (126, 126, 126), 0.004, 1]]],
#     ["https://ifh.cc/g/LQSJrX.jpg", "그리운 날에16", "고재군", "이 작품은 커다란 해바라기와 그 아래 서 있는 버스를 묘사하고 있습니다. 밝고 생동감 넘치는 해바라기의 색감이 인상적이며, 전체적으로 활기차고 밝은 분위기를 자아냅니다. 자연의 생동감과 아름다움을 통해 기쁨과 행복을 전달합니다.", ["기쁨", "행복", "감각적"], [['Manz', (219, 220, 93), 0.325, 1], ['Yellow', (227, 189, 28), 0.26, 2], ['Pumpkin', (226, 132, 45), 0.126, 1], ['Paris Daisy', (255, 236, 79), 0.12, 1], ['Cioccolato', (115, 63, 44), 0.048, 1], ['Tuscany', (169, 87, 49), 0.047, 1], ['Costa Del Sol', (139, 117, 65), 0.028, 1], ['Feldspar', (215, 145, 96), 0.025, 1], ['Black', (53, 52, 48), 0.021, 1]]],
#     ["https://ifh.cc/g/Phoc87.jpg", "그리운 날에32", "고재군", "이 작품은 노란 들판과 그 사이로 달리는 버스를 묘사하고 있습니다. 노란색이 가득한 배경이 따뜻하고 밝은 분위기를 자아내며, 버스는 이동과 여정을 상징합니다. 전체적으로 밝고 따뜻한 느낌을 주며, 행복과 기쁨을 표현하고 있습니다.", ["행복", "기쁨", "감각적"], [['Yellow', (227, 189, 28), 0.638, 4], ['Very Light Grey', (206, 206, 206), 0.147, 1], ['Paris Daisy', (255, 236, 79), 0.108, 1], ['Lemon Ginger', (156, 137, 37), 0.056, 1], ['Costa Del Sol', (139, 117, 65), 0.026, 1], ['Raffia', (218, 196, 148), 0.017, 1], ['Cioccolato', (75, 63, 45), 0.01, 1]]],
#     ["https://ifh.cc/g/TZ3ov9.jpg", "그리운 날에35", "고재군", "이 작품은 노란 꽃나무와 그 아래 서 있는 버스를 묘사하고 있습니다. 따뜻한 노란색이 가득한 배경이 밝고 활기찬 분위기를 자아내며, 버스는 이동과 여정을 상징합니다. 전체적으로 밝고 생동감 넘치는 분위기를 통해 자연의 아름다움을 강조하고 있습니다.", ["행복", "기쁨", "감각적"], [['Manz', (219, 220, 93), 0.431, 2], ['Yellow', (227, 189, 28), 0.358, 2], ['Bahia', (162, 179, 36), 0.158, 3], ['Lemon Ginger', (156, 137, 37), 0.029, 1], ['Costa Del Sol', (103, 91, 44), 0.014, 1], ['Black', (53, 52, 48), 0.01, 1]]],
#     ["https://ifh.cc/g/o71Fkx.jpg", "사유의 흔적 2018-10", "고진오", "이 작품은 다양한 색채와 추상적인 형태들이 어우러진 풍경을 담고 있습니다. 다채로운 색감과 조화로운 구성이 돋보이며, 전체적으로 에너지 넘치고 활기찬 분위기를 자아냅니다. 추상적인 형태와 색감이 어우러져 보는 이로 하여금 감각적이고 혼란스러운 느낌을 줍니다.", ["혼란", "감각적", "에너지"], [['Pumpkin', (226, 132, 45), 0.306, 2], ['Tuscany', (169, 87, 49), 0.267, 2], ['Lemon Ginger', (156, 137, 37), 0.127, 1], ['Bahia', (195, 202, 101), 0.112, 1], ['Raffia', (218, 196, 148), 0.075, 1], ['Corn Field', (228, 235, 191), 0.043, 1], ['Cioccolato', (75, 63, 45), 0.037, 1], ['Granite Green', (144, 135, 96), 0.034, 1]]],
#     ["https://ifh.cc/g/XSAScb.jpg", "사유의 흔적 2018-20", "고진오", "이 작품은 추상적인 색채와 형태로 이루어진 풍경을 담고 있습니다. 선명한 색감과 다양한 형태가 조화를 이루며, 전체적으로 활기차고 생동감 넘치는 분위기를 자아냅니다. 색채와 형태의 조화가 감각적이고 에너지 넘치는 느낌을 줍니다.", ["감각적", "에너지", "혼란"], [['Rose', (218, 176, 176), 0.223, 1], ['Tuscany', (169, 87, 49), 0.191, 1], ['Red Damask', (209, 116, 73), 0.127, 1], ['Nepal', (138, 166, 187), 0.105, 1], ['Sprout', (179, 202, 157), 0.081, 1], ['Sage', (143, 162, 121), 0.077, 1], ['Almond', (236, 217, 202), 0.07, 1], ['Grey', (126, 126, 126), 0.067, 1], ['Costa Del Sol', (139, 117, 65), 0.045, 1], ['Black', (38, 38, 38), 0.014, 1]]],
#     ["https://ifh.cc/g/O70SJa.jpg", "Noon", "고진이", "이 작품은 푸른색과 노란색이 조화를 이루는 추상적인 풍경을 담고 있습니다. 선명한 색감과 부드러운 색채의 조화가 평화롭고 차분한 분위기를 자아냅니다. 전체적으로 평온하고 고요한 느낌을 주며, 자연의 아름다움을 감각적으로 표현하고 있습니다.", ["평화", "감각적", "고요함"], [['Cerulean', (6, 113, 148), 0.336, 3], ['Seagull', (126, 188, 209), 0.298, 3], ['Corn Field', (228, 235, 191), 0.127, 1], ['Raffia', (218, 196, 148), 0.106, 1], ['Cobalt', (3, 86, 155), 0.081, 1], ['Spring Rain', (166, 201, 163), 0.053, 1]]]
# ]

class ImageData(BaseModel):
    user_images_urls: List[HttpUrl] = [
        "https://ifh.cc/g/oY2K9B.jpg",
        "https://ifh.cc/g/zwxOAA.jpg",
        "https://ifh.cc/g/XSAScb.jpg",
        "https://ifh.cc/g/DgrlJL.jpg"
    ]
    similarity_threshold: float = 0.70

def random_exhibition(exhibition):
    recom_exhibition = {}
    recom_exhibition1 = random.choices(exhibition, k=1)
    recom_exhibition['name'] = recom_exhibition1[0]['name']
    recom_exhibition['start_date'] = recom_exhibition1[0]['start_date']
    recom_exhibition['end_date'] = recom_exhibition1[0]['end_date']
    return recom_exhibition

def find_matching_images(data: ImageData, image_url_list2):
    if not data.user_images_urls:
        raise HTTPException(status_code=400, detail="The user images URL list is empty.")
    
    matching_urls = find_best_matching_images(data.user_images_urls, image_url_list2)
    
    return {"matching_urls": matching_urls}

def exact_match(emotions, target):
    return set(emotions) == set(target)

# Helper function to count the number of matches
def count_matches(emotions, target):
    return sum(1 for e in emotions if e in target)


similarity_threshold=0.7
kernel = np.array([[0, -1, 0],
                   [-1, 5, -1],
                   [0, -1, 0]])

def load_image_from_url_with_requests(url):
    try:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        img = np.array(img)
        if img.shape[2] == 4:  # PNG with alpha channel
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
        else:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        return img
    except Exception as e:
        print(f"Error loading image from {url}: {e}")
        return None


def restore_image(images):
    restored_images = []
    for filename, img in images:
        restored_img = cv2.filter2D(img, -1, kernel)
        restored_images.append((filename, restored_img))
    return restored_images

def compare_images(img1, img2):
    # Resize images to the same size
    img1 = cv2.resize(img1, (300, 300))
    img2 = cv2.resize(img2, (300, 300))

    # Convert images to grayscale
    img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    img2_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    # Compute SSIM between two images
    score, _ = ssim(img1_gray, img2_gray, full=True)
    return score

def get_images_from_url(url):
    response = requests.get(url)
    image = Image.open(BytesIO(response.content))
    return image

def extract_top_colors(image, num_clusters):
    #image = Image.open(image)
    image = image.convert('RGB')
    np_image = np.array(image)
    pixels = np_image.reshape(-1, 3)
    kmeans = KMeans(n_clusters=num_clusters, n_init=10)
    kmeans.fit(pixels)
    colors = kmeans.cluster_centers_.round(0).astype(np.uint8)
    labels, counts = np.unique(kmeans.labels_, return_counts=True)
    total_count = np.sum(counts)
    color_ratios = [(colors[i], counts[i] / total_count) for i in labels]
    return sorted(color_ratios, key=lambda x: x[1], reverse=True)

def colormatching(randomrgb):
    def euclidean_distance(rgb1, rgb2):
        return np.sqrt(np.sum((np.array(rgb1) - np.array(rgb2))**2))
    
    min_distance = float('inf')
    closest_color_name = None
    closest_color_rgb = None

    for color_set, color_name in RestArt_color.items():
        if isinstance(color_set, tuple) and isinstance(color_set[0], tuple):
            for color in color_set:
                distance = euclidean_distance(randomrgb, color)
                if distance < min_distance:
                    min_distance = distance
                    closest_color_name = color_name
                    closest_color_rgb = color
        elif isinstance(color_set, tuple):
            distance = euclidean_distance(randomrgb, color_set)
            if distance < min_distance:
                min_distance = distance
                closest_color_name = color_name
                closest_color_rgb = color_set
    return closest_color_name, closest_color_rgb

# def analyze_image_colors(image, num_clusters):
#     top_colors = extract_top_colors(image, num_clusters)
#     color_info = defaultdict(lambda: {'rgb': None, 'ratio': 0, 'count': 0})
#     for color, ratio in top_colors:
#         color_name, color_rgb = colormatching(color)
#         if color_info[color_name]['rgb'] is None:
#             color_info[color_name]['rgb'] = color_rgb
#         color_info[color_name]['ratio'] += ratio
#         color_info[color_name]['count'] += 1
#
#     results = []
#     for color_name, info in color_info.items():
#         results.append([color_name, info['rgb'], round(info['ratio'], 3), info['count']])
#
#     sorted_results = sorted(results, key=lambda x: x[2], reverse=True)
#     return sorted_results

def find_best_matching_images(user_images_urls, image_url_list, similarity_threshold=0.6):
    exhibition_images = []
    for url in image_url_list['url']:
        img = load_image_from_url_with_requests(url)
        if img is not None:
            exhibition_images.append((url, img))


    user_images = []
    for url in user_images_urls:
        img = load_image_from_url_with_requests(url)
        if img is not None:
            user_images.append((url, img))

    # Apply blur and restore images
    #restored_user_images = restore_image(user_images)

    valid_urls2 = {
        'url': [],
        'color_cluster_ratio': []
    }
    for user_filename, user_img in user_images:
        kk = 0
        for exhibition_filename, exhibition_img in exhibition_images:
            similarity = compare_images(user_img, exhibition_img)
            if similarity >= similarity_threshold and exhibition_filename not in valid_urls2['url']:
                valid_urls2['url'].append(exhibition_filename)
                valid_urls2['color_cluster_ratio'].append(image_url_list['color_cluster_ratio'][kk])
                break
            kk+=1

    return valid_urls2

    
def gaussian_kernel(x, y, sigma=1.0):
    return np.exp(-np.linalg.norm(x - y) ** 2 / (2 * (sigma ** 2)))

def analyze_images_and_cluster(user_images_urls, num_clusters_image: int = 10, num_clusters_spectral: int = 4, sigma: float = 30):
    #matching_urls = user_images_urls
    if len(user_images_urls['url'])>4:
        final_dict = {}

        kkk = 0
        for image_url in user_images_urls['url']:
            final_dict[image_url] = tuple(json.loads(user_images_urls['color_cluster_ratio'][kkk])[0][1])
            kkk +=1

        rgb_colors = [value for value in final_dict.values()]
        rgb_colors_array = np.array(rgb_colors)

        n_samples = len(rgb_colors)
        similarity_matrix = np.zeros((n_samples, n_samples))

        for i in range(n_samples):
            for j in range(n_samples):
                similarity_matrix[i, j] = gaussian_kernel(rgb_colors_array[i], rgb_colors_array[j], sigma)

        spectral = SpectralClustering(n_clusters=num_clusters_spectral, affinity='precomputed')
        labels = spectral.fit_predict(similarity_matrix)

        cluster_centers = np.array([rgb_colors_array[labels == i].mean(axis=0) for i in range(num_clusters_spectral)], dtype=int)

        target_keys = []
        for center in cluster_centers:
            distances = cdist([center], rgb_colors_array, metric='euclidean')[0]
            closest_index = np.argmin(distances)
            closest_color = rgb_colors_array[closest_index]
            possible_keys = [key for key, value in final_dict.items() if np.array_equal(value, closest_color)]
            selected_key = np.random.choice(possible_keys)
            target_keys.append(selected_key)

    elif len(user_images_urls['url']) == 4:
        target_keys = user_images_urls['url']
    else:
        target_keys = random.choices(user_images_urls['url'], k=4)
    return target_keys

def find_signiture_color(user_images_urls, num_clusters=10):
    color_list = []

    for i in range(len(user_images_urls)):
        color_list.append(json.loads(user_images_urls[i]))



    color_final_list = []
    for image_colors in color_list:
        for color_info in image_colors:
            color_dict = {}
            color_dict[color_info[0]] = color_info[3]
            color_final_list.append(color_dict)

    signiture_color = {}
    for item in color_final_list:
        for key, value in item.items():
            if key in signiture_color:
                signiture_color[key] += value
            else:
                signiture_color[key] = value

    final_signiture_color = sorted(signiture_color.items(), key=lambda x: x[1], reverse=True)

    return final_signiture_color[0][0]

def find_nearby_exhibitions(current_location, exhibitions, radius):
    def haversine(coord1, coord2):
        R = 6371  # 지구의 반지름 (단위: km)

        lat1, lon1 = coord1
        lat2, lon2 = coord2

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = R * c
        return distance

    # 전시 정보 딕셔너리 생성
    exhibition_dict = {exhibit[0]: exhibit[1] for exhibit in exhibitions}

    # 반경 내에 있는 전시 검색
    found_exhibitions = {}
    for exhibit in exhibitions:
        distance = haversine(current_location, exhibit[1])
        if distance <= radius:
            found_exhibitions[exhibit[0]] = distance

    # 결과 출력
    if found_exhibitions:
        exhibition_name = []
        final_found_exhibitions = sorted(found_exhibitions.items(), key=lambda x: x[1])
        for name, dist in final_found_exhibitions:
            exhibition_name.append(name)
        info = exhibition_name[0]
    else:
        info = None
    return info