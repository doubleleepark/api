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
        ((207, 46, 49), (231, 47, 39)): "Cinnabar",
        (172, 35, 48): "Guardsman Red",
        (233, 163, 144): "Tonys Pink",
        (231, 108, 86): "Terra Cotta",
        (236, 217, 202): "Almond",
        (213, 182, 166): "Clam Shell",
        ((211, 142, 110), (215, 145, 96)): "Feldspar",
        ((171, 131, 115), (158, 128, 110), (148, 133, 105), (160, 147, 131)): "Hemp",
        ((162, 88, 61), (167, 100, 67), (169, 87, 49)): "Tuscany",
        ((116, 47, 50), (111, 61, 56)): "Tamarillo",
        ((115, 63, 44), (79, 46, 43), (85, 55, 43), (75, 63, 45), (88, 60, 50)): "Cioccolato",
        ((238, 113, 25), (226, 132, 45)): "Pumpkin",
        ((241, 176, 102), (242, 178, 103)): "Harvest Gold",
        ((255, 200, 8), (227, 189, 28), (255, 203, 88), (155, 196, 113)): "Yellow",
        ((255, 228, 15), (255, 236, 79)): "Paris Daisy",
        ((170, 198, 27), (162, 179, 36), (169, 199, 35), (195, 202, 101)): "Bahia",
        (219, 220, 93): "Manz",
        ((19, 166, 50), (18, 154, 47), (88, 171, 45)): "Forest Green",
        ((146, 198, 131), (141, 188, 90), (140, 195, 110)): "Mantis",
        ((4, 148, 87), (6, 134, 84), (43, 151, 89)): "Salem",
        ((39, 122, 62), (23, 106, 43), (20, 114, 48), (30, 98, 50)): "Camarone",
        ((1, 134, 141), (3, 130, 122), (0, 147, 159), (117, 173, 169)): "Eastern Blue",
        (53, 109, 98): "Genoa",
        ((3, 86, 155), (44, 77, 143)): "Cobalt",
        ((6, 113, 148), (59, 130, 157)): "Cerulean",
        ((46, 20, 141), (58, 55, 119)): "Persian Indigo",
        ((44, 60, 49), (53, 52, 48), (60, 60, 60), (38, 38, 38), (10, 10, 10)): "Black",
        ((244, 244, 244), (236, 236, 236)): "White Smoke",
        ((206, 206, 206), (180, 180, 180), (184, 190, 189), (151, 150, 139)): "Very Light Grey",
        ((152, 152, 152), (126, 126, 126), (86, 86, 86)): "Grey",
        ((40, 47, 103), (34, 54, 68)): "Deep Koamaru",
        ((34, 62, 51), (31, 56, 45), (29, 60, 47), (25, 62, 63)): "Palm Green",
        ((245, 223, 181), (228, 235, 191), (233, 227, 143), (249, 239, 189)): "Corn Field",
        ((24, 89, 63), (20, 88, 60), (18, 83, 65), (27, 86, 49)): "Fun Green",
        ((8, 87, 107), (16, 76, 84)): "Sherpa Blue",
        ((197, 188, 213), (170, 165, 199)): "Wistful",
        ((127, 175, 166), (130, 154, 145), (133, 154, 153)): "Granny Smith",
        ((147, 184, 213), (138, 166, 187)): "Nepal",
        ((218, 176, 176), (205, 154, 149)): "Rose",
        ((144, 135, 96), (109, 116, 73)): "Granite Green",
        ((88, 126, 61), (91, 132, 47)): "Dingley",
        ((139, 117, 65), (103, 91, 44)): "Costa Del Sol",
        (204, 63, 92): "Mandy",
        (92, 104, 106): "Pale Sky",
        (175, 97, 87): "Au Chico",
        (178, 137, 166): "London Hue",
        (209, 100, 109): "Cabaret",
        (126, 188, 209): "Seagull",
        (221, 232, 207): "Frostee",
        (209, 234, 211): "Aqua Squeeze",
        (194, 222, 242): "Pattens Blue",
        (203, 215, 232): "Hawkes Blue",
        (224, 218, 230): "Titan White",
        (235, 219, 224): "Pale Rose",
        (218, 196, 148): "Raffia",
        (209, 116, 73): "Red Damask",
        (179, 202, 157): "Sprout",
        (166, 201, 163): "Spring Rain",
        (165, 184, 199): "Heather",
        (206, 185, 179): "Wafer",
        (143, 162, 121): "Sage",
        (122, 165, 123): "Oxley",
        (156, 137, 37): "Lemon Ginger",
        (115, 71, 79): "Tosca",
        (54, 88, 48): "Green House"
    }
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
    recom_exhibition['exhibition_img'] = recom_exhibition1[0]['exhibition_img']
    recom_exhibition['name'] = recom_exhibition1[0]['name']
    recom_exhibition['start_date'] = recom_exhibition1[0]['start_date']
    recom_exhibition['end_date'] = recom_exhibition1[0]['end_date']
    return recom_exhibition

def find_matching_images(data: ImageData, image_url_list2):
    if not data.user_images_urls:
        raise HTTPException(status_code=400, detail="The user images URL list is empty.")
    
    matching_urls = find_best_matching_images(data.user_images_urls, image_url_list2)

    return {'matching_urls': matching_urls}

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


def find_best_matching_images(user_images_urls, image_url_list, similarity_threshold=0.2):
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
    valid_urls2 = {
        'url': [],
        'color_cluster_ratio': []
    }
    for user_filename, user_img in user_images:
        best_match_url = None
        best_similarity = 0
        kk=0
        jj=0
        for exhibition_filename, exhibition_img in exhibition_images:
            similarity = compare_images(user_img, exhibition_img)
            if similarity >= best_similarity:
                best_similarity = similarity
                best_match_url = exhibition_filename
                jj = kk
            kk += 1
        if best_similarity >= similarity_threshold:
            if best_match_url not in valid_urls2['url']:
                valid_urls2['url'].append(best_match_url)
                valid_urls2['color_cluster_ratio'].append(image_url_list['color_cluster_ratio'][jj])
    return valid_urls2

    
def gaussian_kernel(x, y, sigma=1.0):
    return np.exp(-np.linalg.norm(x - y) ** 2 / (2 * (sigma ** 2)))



def analyze_images_and_cluster(user_images_urls, result, num_clusters_spectral: int = 4, sigma: float = 30):
    #matching_urls = user_images_urls
    print(user_images_urls['url'])
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
            rgb_colors_array = np.delete(rgb_colors_array, closest_index, axis=0)
            possible_keys = [key for key, value in final_dict.items() if np.array_equal(value, closest_color)]
            selected_key = np.random.choice(possible_keys)
            target_keys.append(selected_key)
    elif len(user_images_urls['url']) == 4:
        target_keys = user_images_urls['url']
    elif user_images_urls['url'] == []:
        target_keys = random.choices(result['url'], k=4)
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
    print(signiture_color)
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


List1 = ["Cinnabar", "Paris Daisy", "Corn Field", "Kournikova", "Tangerine Yellow", "Pumpkin", "Harvest Gold", "Brandy Rose", "Granite Green", "Manz", "Cioccolato", "Deep Bronze", "Metallic Copper", "Feldspar", "Vesuvius", "Lemon Ginger", "Costa Del Sol"]
List2 = ["White Smoke", "Wistful", "Tonys Pink", "Wafer", "Granny Smith", "Wheat", "Pale Rose", "Oyster Pink", "Opal", "London Hue", "Mandy", "Chetwode Blue", "Aqua Squeeze", "Sprout", "Oxley", "Seagull", "Gulf Stream", "Heather", "Hawkes Blue"]
List3 = ["Black", "Persian Indigo", "Cobalt", "Wild Willow", "Cerulean", "Timber Green", "Palm Green", "Tiber", "Tamarillo", "Apple Blossom", "Surfie Green", "Blue Lagoon", "Guardsman Red"]
List4 = ["Matterhorn", "Nobel", "Very Light Grey", "Bahia", "Gossip", "Dark Pastel Green", "Shamrock Green", "Salem", "Eastern Blue", "Chelsea Cucumber", "Fun Green", "Deep Teal", "Camarone", "Vida Loca", "Green House", "Siam"]

def leaflet_design(dominant_color):
    if dominant_color in List1:
      return 1
    elif dominant_color in List2:
      return 2
    elif dominant_color in List3:
      return 3
    else:
      return 4