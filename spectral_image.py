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


app = FastAPI()

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

class ImageData(BaseModel):
    user_images_urls: List[HttpUrl] = [
        "https://ifh.cc/g/oY2K9B.jpg",
        "https://ifh.cc/g/zwxOAA.jpg",
        "https://ifh.cc/g/XSAScb.jpg",
        "https://ifh.cc/g/DgrlJL.jpg",
        "https://ifh.cc/g/Pkdahy.jpg",
        "https://ifh.cc/g/JfftWD.jpg",
        "https://ifh.cc/g/bsx2AQ.jpg"]


def find_matching_images(data: ImageData):
    if not data.user_images_urls:
        raise HTTPException(status_code=400, detail="The user images URL list is empty.")

    matching_urls = find_best_matching_images(data.user_images_urls, image_url_list, data.similarity_threshold)

    return {"matching_urls": matching_urls}


def exact_match(emotions, target):
    return set(emotions) == set(target)


# Helper function to count the number of matches
def count_matches(emotions, target):
    return sum(1 for e in emotions if e in target)


similarity_threshold = 0.7
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


def apply_blur_to_images(images):
    blurred_images = []
    for filename, img in images:
        blurred_img = cv2.blur(img, (4, 4))
        blurred_images.append((filename, blurred_img))
    return blurred_images


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

def find_best_matching_images(user_images_urls, image_url_list, similarity_threshold):
    exhibition_images = []
    for url, _, _, _, *_ in image_url_list:
        img = load_image_from_url_with_requests(url)
        if img is not None:
            exhibition_images.append((url, img))

    user_images = []
    for url in user_images_urls:
        img = load_image_from_url_with_requests(url)
        if img is not None:
            user_images.append((url, img))

    # Apply blur and restore images
    # blurred_user_images = apply_blur_to_images(user_images)
    restored_user_images = restore_image(user_images)

    valid_urls = []

    for user_filename, user_img in restored_user_images:
        for exhibition_filename, exhibition_img in exhibition_images:
            similarity = compare_images(user_img, exhibition_img)
            if similarity >= similarity_threshold and exhibition_filename not in valid_urls:
                valid_urls.append(exhibition_filename)
                break

    return valid_urls


def gaussian_kernel(x, y, sigma=1.0):
    return np.exp(-np.linalg.norm(x - y) ** 2 / (2 * (sigma ** 2)))

@app.post("/analyze-most-different-pictures/")
async def analyze_images_and_cluster(user_images_urls, num_clusters_image: int = 10, num_clusters_spectral: int = 4, sigma: float = 30):
    #matching_urls = user_images_urls
    if len(user_images_urls)>4:
        final_dict = {}

        for image_url in user_images_urls:
            for i in range(len(image_url_list)):
                if image_url_list[i][0] == image_url:
                    final_dict[image_url] = image_url_list[i][5][0][1]

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

    elif len(user_images_urls) == 4:
        target_keys = user_images_urls
    else:
        target_keys = random.choices(user_images_urls, k=4)

    return {
        "4pictures": target_keys,
    }

def extract_top_colors_from_image(image_url):
    # This is a placeholder for the actual implementation to extract top colors from the image
    # Replace this with your logic to extract colors from an image based on its URL
    return np.random.randint(0, 255, size=(3,))  # Random RGB color for demonstration purposes

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
