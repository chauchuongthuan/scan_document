# Thêm các import này ở đầu file views.py
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.conf import settings # Import settings
import numpy as np
import os
import re
import math
import nltk
from nltk.tokenize import sent_tokenize
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import logging # Thêm logging để theo dõi lỗi
from django.shortcuts import render
from datetime import datetime, timedelta
import requests

# from .models import DailyMarketPrice
# from .market_agent_utils import (
#     calculate_paragraph_entropy,
#     safe_float,
#     identify_paragraph_type,
#     get_detailed_price_signals
# )

# Cấu hình logging
logger = logging.getLogger(__name__)

# Tải NLTK
# nltk.download('punkt', quiet=True)

# # --- KHỞI TẠO MÔ HÌNH VÀ MỎ NEO (CHẠY 1 LẦN KHI SERVER START) ---

# def create_anchor_from_file(filepath, model):
#     """Hàm này đọc file mẫu và tạo vector mỏ neo (anchor)."""
#     try:
#         if not os.path.exists(filepath):
#             logger.error(f"[MarketAgent] File not found: {filepath}")
#             return None
#         with open(filepath, 'r', encoding='utf-8') as f:
#             lines = [line.strip() for line in f if len(line.strip()) > 5]
#         if not lines:
#             logger.warning(f"[MarketAgent] Anchor file is empty: {filepath}")
#             return None
#         logger.info(f"[MarketAgent] Learning anchor from {len(lines)} samples in {filepath}...")
#         embeddings = model.encode(lines, normalize_embeddings=True)
#         mean_vec = np.mean(embeddings, axis=0, keepdims=True)
#         mean_vec = mean_vec / np.linalg.norm(mean_vec)
#         logger.info(f"[MarketAgent] Anchor loaded successfully for {filepath}")
#         return mean_vec
#     except Exception as e:
#         logger.error(f"[MarketAgent] Error loading anchor file {filepath}: {e}")
#         return None
# # 1. Tải mô hình
# try:
#     MODEL = SentenceTransformer("all-MiniLM-L6-v2")
#     logger.info("[MarketAgent] SentenceTransformer model loaded.")
# except Exception as e:
#     MODEL = None
#     logger.error(f"[MarketAgent] CRITICAL: Failed to load SentenceTransformer model: {e}")

# # 2. Định nghĩa đường dẫn file
# BULLISH_FILE_PATH = os.path.join(settings.MARKET_AGENT_DATA_DIR, 'bullish.txt')
# BEARISH_FILE_PATH = os.path.join(settings.MARKET_AGENT_DATA_DIR, 'bearish.txt')

# # 3. Tải và cache các vector mỏ neo
# if MODEL:
#     BULLISH_VECTOR = create_anchor_from_file(BULLISH_FILE_PATH, MODEL)
#     BEARISH_VECTOR = create_anchor_from_file(BEARISH_FILE_PATH, MODEL)
# else:
#     BULLISH_VECTOR = None
#     BEARISH_VECTOR = None

# MAX_CLUSTERS = 5
# SCALE_FACTOR = 4 * math.pi * 2 * 0.72
# # -----------------------------------------------------------------
# class MarketAgentView(View):
#     """
#     API view để tính toán Tác động Giá (Price Impact) của văn bản.
#     Sử dụng các mỏ neo ngữ nghĩa (bullish/bearish) để chấm điểm.
#     """ 
#     @login_required(login_url="login_cms")
#     def post(request):
#         if request.method == 'POST':
#             try:
#                 # Kiểm tra quan trọng
#                 if MODEL is None or BULLISH_VECTOR is None or BEARISH_VECTOR is None:
#                     return JsonResponse({"status": "error", "message": "Market Agent is not ready. Model or anchors failed."}, status=500)

#                 text = request.POST.get('paragraph', '')
#                 date_str = request.POST.get('date', '') # Lấy date từ request
#                 curr_prices = {
#                     "farm_gate_low": safe_float(request.POST.get('farm_gate_low', None)),
#                     "farm_gate_high": safe_float(request.POST.get('farm_gate_high', None)),
#                     "midstream_low": safe_float(request.POST.get('midstream_low', None)),
#                     "midstream_high": safe_float(request.POST.get('midstream_high', None)),
#                     "differential_ask": safe_float(request.POST.get('differential_ask', None)),
#                     "differential_bid": safe_float(request.POST.get('differential_bid', None))
#                 }
                

#                 if not text or len(text.strip()) < 5:
#                     return JsonResponse({"status": "error", "message": "No valid text input."}, status=400)
#                 if not date_str:
#                     return JsonResponse({"status": "error", "message": "Missing 'date' field (YYYY-MM-DD)."}, status=400)

#                 # --- 1. XỬ LÝ GIÁ VÀ SO SÁNH NGÀY ---
#                 try:
#                     current_date = datetime.fromisoformat(date_str).date()
#                     prev_prices = None
#                     for i in range(1, 5):
#                          try:
#                              prev_prices = DailyMarketPrice.objects.get(date=current_date - timedelta(days=i))
#                              break
#                          except DailyMarketPrice.DoesNotExist: continue
#                 except ValueError: return JsonResponse({"status": "error", "message": "Invalid date format."}, status=400)
                
#                 # Lấy giá ngày hôm trước từ DB
#                 price_signals = get_detailed_price_signals(curr_prices, prev_prices)

#                 # Lưu giá hôm nay
#                 if any(v is not None for v in curr_prices.values()):
#                     DailyMarketPrice.objects.update_or_create(date=current_date, defaults=curr_prices)

#                 # --- 2. XỬ LÝ TỪNG ĐOẠN (IMPACT & ENTROPY) ---
#                 paragraphs = [p.strip() for p in re.split(r'\n{1,}', text) if len(p.strip()) > 0]
#                 results = []
#                 total_impact = 0.0

#                 paragraphs = [p.strip() for p in re.split(r'\n{1,}', text) if len(p.strip()) > 0]
#                 results = []
#                 total_impact = 0.0
#                 final_weighted_entropy = 0.0 # Biến mới cho Entropy có hướng

#                 for idx, para in enumerate(paragraphs, start=1):
#                     sentences = [s.strip() for s in sent_tokenize(para) if len(s.strip().split()) > 3]
#                     if not sentences: continue

#                     para_type = identify_paragraph_type(para)
#                     sign = "neutral"
#                     impact_val = 0.0
#                     needs_review = False

#                     if para_type in ["farm_gate", "midstream", "differential"]:
#                         sign = price_signals.get(para_type, "neutral")
#                         impact_val = 1.0 if sign == "+" else (-1.0 if sign == "-" else 0.0)
#                     else:
#                         # Logic semantic (mỏ neo)
#                         emb = MODEL.encode(sentences, normalize_embeddings=True)
#                         bullish = np.sum(cosine_similarity(emb, BULLISH_VECTOR))
#                         bearish = np.sum(cosine_similarity(emb, BEARISH_VECTOR))
#                         impact_val = float(bullish - bearish)
#                         sign = "+" if impact_val > 0.05 else ("-" if impact_val < -0.05 else "neutral")

#                     # Nếu là neutral, đánh dấu cần xem lại
#                     if sign == "neutral":
#                         needs_review = True

#                     entropy_data = calculate_paragraph_entropy(sentences, MODEL, MAX_CLUSTERS, SCALE_FACTOR)
#                     scaled_entropy = entropy_data["scaled_entropy"]

#                     # --- LOGIC MỚI CHO FINAL ENTROPY ---
#                     entropy_weight = 0
#                     if sign == "+": entropy_weight = 1
#                     elif sign == "-": entropy_weight = -1

#                     final_weighted_entropy += (scaled_entropy * entropy_weight)
#                     # ------------------------------------

#                     results.append({
#                         "paragraph_index": idx,
#                         "type": para_type,
#                         "paragraph_sign": sign,
#                         "paragraph_impact_score": round(impact_val, 4),
#                         "scaled_entropy": scaled_entropy,
#                         "deviation_entropy": entropy_data["deviation_entropy"],
#                         "cluster_entropy": entropy_data["cluster_entropy"],
#                         "num_clusters": entropy_data["num_clusters"],
#                         "needs_manual_review": needs_review,
#                         "text_preview": para
#                     })

#                 return JsonResponse({
#                     "status": "success",
#                     "result": {
#                         "final_market_flow_score": round(total_impact, 4),
#                         "final_weighted_entropy": round(final_weighted_entropy, 4),
#                         "price_signals": price_signals,
#                         "paragraphs": results
#                     }
#                 }, status=200)

#             except Exception as e:
#                 logger.error(f"[MarketAgent] Calculate failed: {str(e)}", exc_info=True)
#                 return JsonResponse({
#                     "status": "error",
#                     "message": f"Calculate failed: {str(e)}"
#                 }, status=500)
#         return render(request, 'market-agent/create.html')

class SearchGGView(View):
    def get(request):
        api_key = os.environ.get('API_KEY_GG_SEARCH')
        cx = os.environ.get('CX_GG_SEARCH')
        url = "https://www.googleapis.com/customsearch/v1"
        keywords_query = [
            'tin tức thiên tai tây nguyên mới nhất', 
            'thiên tai Gia Lai mới nhất', 
            'thiên tai dak lak mới nhất', 
            'thiên tai dak nong mới nhất',
            'lũ lụt mới nhất',
            'thuế mới nhất',
            # "coffee",
            # "tariff",
            # "Trump",
            # "eudr"
        ]
        
        final_data = []

        for keyword in keywords_query:
            params = {
                'key': api_key,
                'cx': cx,
                'q': keyword,
                'dateRestrict': 'd1',  # Giới hạn 1 ngày qua (d1 = 1 day)
                'gl': 'vn',
            }
            
            response = requests.get(url, params=params)
            print("response", response)
            data = response.json()

            current_keyword_articles = []
            
            if 'items' in data:
                for item in data['items']:
                    current_keyword_articles.append({
                        'title': item['title'],
                        'link': item['link'],
                        'snippet': item['snippet']
                    })

            final_data.append({
                'keyword': keyword,
                'articles': current_keyword_articles,
                'count': len(current_keyword_articles)
            })
        print("final_data", final_data)
        return render(request, 'market-agent/gg-search.html', {'results': final_data})
