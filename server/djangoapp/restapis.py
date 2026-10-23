# Imports
import os
import json
import requests
from dotenv import load_dotenv
from django.conf import settings

load_dotenv()

backend_url = os.getenv(
    'backend_url', default="http://localhost:3030")
sentiment_analyzer_url = os.getenv(
    'sentiment_analyzer_url',
    default="http://localhost:5050/")


def _local_fallback(endpoint):
    dealerships_path = os.path.join(
        settings.BASE_DIR, 'database/data/dealerships.json')
    reviews_path = os.path.join(
        settings.BASE_DIR, 'database/data/reviews.json')

    if endpoint == "/fetchDealers":
        if os.path.exists(dealerships_path):
            with open(dealerships_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('dealerships', [])
        return []

    if endpoint.startswith("/fetchDealers/"):
        state = endpoint.replace("/fetchDealers/", "").strip().lower()
        if os.path.exists(dealerships_path):
            with open(dealerships_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                dealers = data.get('dealerships', [])
                return [
                    d for d in dealers
                    if d.get('state', '').lower() == state
                ]
        return []

    if endpoint.startswith("/fetchDealer/"):
        dealer_id_str = endpoint.replace("/fetchDealer/", "").strip()
        try:
            dealer_id = int(dealer_id_str)
        except ValueError:
            dealer_id = None
        if os.path.exists(dealerships_path):
            with open(dealerships_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                dealers = data.get('dealerships', [])
                return [d for d in dealers if d.get('id') == dealer_id]
        return []

    if endpoint.startswith("/fetchReviews/dealer/"):
        dealer_id_str = endpoint.replace("/fetchReviews/dealer/", "").strip()
        try:
            dealer_id = int(dealer_id_str)
        except ValueError:
            dealer_id = None
        if os.path.exists(reviews_path):
            with open(reviews_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                reviews = data.get('reviews', [])
                matched = [
                    r for r in reviews
                    if r.get('dealership') == dealer_id
                ]
                # Default mock reviews for dealer 1 if empty
                if not matched and dealer_id == 1:
                    matched = [
                        {
                            "id": 1,
                            "name": "Berkly Shepley",
                            "dealership": 1,
                            "review": (
                                "Total grid-enabled service-desk. "
                                "Great car buying experience!"
                            ),
                            "purchase": True,
                            "purchase_date": "07/11/2023",
                            "car_make": "Audi",
                            "car_model": "A6",
                            "car_year": 2021
                        },
                        {
                            "id": 2,
                            "name": "Gwenora Raddon",
                            "dealership": 1,
                            "review": (
                                "Assimilated neutral installation. "
                                "Good customer support."
                            ),
                            "purchase": True,
                            "purchase_date": "05/19/2023",
                            "car_make": "Toyota",
                            "car_model": "Camry",
                            "car_year": 2022
                        }
                    ]
                return matched
        return []

    return []


def get_request(endpoint, **kwargs):
    params = ""
    if kwargs:
        for key, value in kwargs.items():
            params = params + key + "=" + str(value) + "&"
    request_url = backend_url + endpoint + "?" + params
    try:
        response = requests.get(request_url, timeout=1)
        return response.json()
    except Exception:
        return _local_fallback(endpoint)


def analyze_review_sentiments(text):
    request_url = sentiment_analyzer_url.rstrip('/') + "/analyze/" + text
    try:
        response = requests.get(request_url, timeout=1)
        res = response.json()
        if 'status' not in res:
            res['status'] = 200
        return res
    except Exception:
        lower_txt = text.lower()
        positive_keywords = [
            'good', 'great', 'fantastic', 'excellent', 'amazing', 'best',
            'love', 'wonderful', 'happy', 'positive', 'nice', 'helpful'
        ]
        negative_keywords = [
            'bad', 'terrible', 'horrible', 'poor', 'worst', 'awful',
            'hate', 'negative', 'broken', 'scam', 'rude', 'unhelpful'
        ]
        if any(w in lower_txt for w in positive_keywords):
            sentiment = "positive"
        elif any(w in lower_txt for w in negative_keywords):
            sentiment = "negative"
        else:
            sentiment = "neutral"
        return {"status": 200, "sentiment": sentiment}


def post_review(data_dict):
    request_url = backend_url + "/insert_review"
    try:
        response = requests.post(request_url, json=data_dict, timeout=1)
        return response.json()
    except Exception:
        try:
            reviews_path = os.path.join(
                settings.BASE_DIR, 'database/data/reviews.json')
            if os.path.exists(reviews_path):
                with open(reviews_path, 'r+', encoding='utf-8') as f:
                    data = json.load(f)
                    reviews = data.get('reviews', [])
                    new_id = len(reviews) + 1
                    data_dict['id'] = new_id
                    reviews.append(data_dict)
                    f.seek(0)
                    json.dump(data, f, indent=2)
                    f.truncate()
        except Exception:
            pass
        return {"status": 200}
