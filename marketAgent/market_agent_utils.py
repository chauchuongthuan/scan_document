import numpy as np
import math
import re
import logging
import json
from datetime import timedelta

from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sentence_transformers import SentenceTransformer

# Setup logging
logger = logging.getLogger(__name__)

# --- CÁC HÀM ENTROPY (Refactored từ views.py của bạn) ---

def safe_number(x):
    """Ép kiểu float và loại NaN/inf."""
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return 0.0
    return float(x)

def deviation_entropy(embeddings):
    """Tính Deviation Entropy (Độ lệch so với trung tâm)."""
    if embeddings.shape[0] <= 1:
        return 0.0, 0.0
    
    mean_vec = embeddings.mean(axis=0, keepdims=True)
    sims = cosine_similarity(embeddings, mean_vec).flatten()
    deviations = 1 - sims
    
    if deviations.sum() <= 0:
        probs = np.ones_like(deviations) / len(deviations)
    else:
        probs = deviations / deviations.sum()
        
    probs = np.nan_to_num(probs, nan=1/len(probs))
    probs = probs[probs > 0] # Chỉ tính toán trên prob > 0
    
    H = -np.sum(probs * np.log2(probs + 1e-12))
    H_norm = H / math.log2(len(probs)) if len(probs) > 1 else 0.0
    return safe_number(H), safe_number(H_norm)

def cluster_entropy(embeddings, max_k):
    """Tính Cluster Entropy (Độ đa dạng chủ đề)."""
    n = len(embeddings)
    if n <= 1:
        return 0.0, 0.0, 1
        
    k = min(max_k, n)
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10).fit(embeddings)
    labels = kmeans.labels_
    counts = np.bincount(labels, minlength=k)
    
    probs = counts / counts.sum() if counts.sum() > 0 else np.ones(k) / k
    probs = probs[probs > 0]
    
    H = -np.sum(probs * np.log2(probs + 1e-12))
    H_norm = H / math.log2(len(probs)) if len(probs) > 1 else 0.0
    return safe_number(H), safe_number(H_norm), int(len(probs))

def calculate_paragraph_entropy(sentences, model, max_clusters, scale_factor):
    """
    Hàm wrapper tính toán tất cả các chỉ số entropy cho một đoạn.
    """
    if len(sentences) == 0:
        return {
            "num_clusters": 0,
            "deviation_entropy": 0.0,
            "cluster_entropy": 0.0,
            "normalized_entropy": 0.0,
            "scaled_entropy": 0.0
        }
        
    embeddings = model.encode(sentences, normalize_embeddings=True)

    H_dev, Hn_dev = deviation_entropy(embeddings)
    H_clu, Hn_clu, n_clusters = cluster_entropy(embeddings, max_clusters)

    H_comb = safe_number((H_dev + H_clu) / 2)
    Hn_comb = safe_number((Hn_dev + Hn_clu) / 2)
    scaled = safe_number(H_comb * scale_factor)

    return {
        "num_clusters": int(n_clusters),
        "deviation_entropy": round(H_dev, 4),
        "cluster_entropy": round(H_clu, 4),
        "normalized_entropy": round(Hn_comb, 4),
        "scaled_entropy": round(scaled, 4)
    }

# --- CÁC HÀM TÁC ĐỘNG GIÁ (Logic mới) ---

def safe_float(price_str):
    """Chuyển đổi string từ POST sang float, xử lý None hoặc rỗng."""
    if price_str is None or price_str.strip() == "":
        return None
    try:
        return float(re.sub(r',', '', price_str))
    except (ValueError, TypeError):
        return None
def identify_paragraph_type(para_text):
        """Xác định xem đoạn văn nói về loại giá nào."""
        text_lower = para_text.lower()
        if "farm-gate" in text_lower or "upstream" in text_lower:
            return "farm_gate"
        if "midstream" in text_lower or "middlemen" in text_lower:
            return "midstream"
        if "differential" in text_lower:
            return "differential"
        return "semantic"

def get_detailed_price_signals(current_prices, previous_prices_obj):
    signals = {"farm_gate": "neutral", "midstream": "neutral", "differential": "neutral"}
    descriptions = []

    if previous_prices_obj is None: 
        signals["description"] = "Không có dữ liệu ngày trước để so sánh."
        return signals

    # 1. Farm-Gate & Midstream (Logic thông thường: Tăng là +, Giảm là -)
    for price_type in ["farm_gate", "midstream"]:
        curr = current_prices.get(f"{price_type}_low")
        prev = getattr(previous_prices_obj, f"{price_type}_low", None)
        if curr is not None and prev is not None:
            diff = curr - prev
            if diff > 0: 
                signals[price_type] = "+"
                descriptions.append(f"{price_type.capitalize()} tăng {diff:,.0f}")
            elif diff < 0: 
                signals[price_type] = "-"
                descriptions.append(f"{price_type.capitalize()} giảm {abs(diff):,.0f}")

    # 2. Differential (Logic đặc biệt: Tăng (ví dụ -80 lên -50) là +, Giảm là -)
    # Chúng ta ưu tiên so sánh BID, nếu không có thì so sánh ASK
    curr_diff = current_prices.get("differential_bid")
    prev_diff = previous_prices_obj.differential_bid

    if curr_diff is None or prev_diff is None:
         # Fallback sang ASK nếu BID thiếu
         curr_diff = current_prices.get("differential_ask")
         prev_diff = previous_prices_obj.differential_ask

    if curr_diff is not None and prev_diff is not None:
        diff = curr_diff - prev_diff
        # QUAN TRỌNG: Diff tăng (về phía dương) là BULLISH (+)
        if diff > 0: 
            signals["differential"] = "+"
            descriptions.append(f"Diff tăng {diff:,.0f}")
        elif diff < 0: 
            signals["differential"] = "-"
            descriptions.append(f"Diff giảm {abs(diff):,.0f}")
        # Nếu diff == 0 thì giữ nguyên là "neutral"

    signals["description"] = ". ".join(descriptions) if descriptions else "Không có thay đổi đáng kể."
    return signals

def calculate_paragraph_entropy_v1(sentences, model, scale_factor):
    """
    Tính toán Semantic Entropy theo công thức V1:
    - Dùng Deviation distribution để tính Entropy.
    - Dùng TF-IDF để trích xuất keywords cho từng cluster.
    """
    # 1. Xử lý trường hợp ít câu
    if len(sentences) <= 1:
        return {
            "semantic_entropy": 1.0,
            "calculate_semantic_entropy": 1.0 * scale_factor,
            "normalized_entropy": 1.0,
            "num_sentences": len(sentences),
            "clusters": None,
            "explanation": "Only one sentence detected, default entropy = 1."
        }

    # 2. Lấy embeddings
    embeddings = model.encode(sentences, normalize_embeddings=True)

    # 3. Tính Entropy (Dựa trên Deviation)
    mean_vec = np.mean(embeddings, axis=0, keepdims=True)
    sims = cosine_similarity(embeddings, mean_vec).flatten()
    deviations = 1 - sims
    
    # Tính xác suất (probs) từ deviations
    if deviations.sum() > 0:
        probs = deviations / deviations.sum()
    else:
        probs = np.ones_like(deviations) / len(deviations)
    
    # Shannon Entropy
    entropy = -np.sum(probs * np.log2(probs + 1e-12))
    
    # Normalized Entropy
    max_entropy = log2(len(sentences)) if len(sentences) > 0 else 1
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0

    # 4. Gom cụm ý (Clustering) & Trích xuất Keywords (TF-IDF)
    n_clusters = min(3, len(sentences))
    cluster_keywords = {}
    explanation = ""
    
    try:
        kmeans = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
        labels = kmeans.fit_predict(embeddings)

        vectorizer = TfidfVectorizer(
            stop_words='english',
            token_pattern=r"(?u)\b[a-zA-Z0-9_./~,-]+\b"
        )
        # Fit trên toàn bộ câu trong đoạn
        vectorizer.fit(sentences)
        feature_names = np.array(vectorizer.get_feature_names_out())

        for i in range(n_clusters):
            idxs = np.where(labels == i)[0]
            cluster_sentences = [sentences[j] for j in idxs]
            
            # Tạo văn bản gộp của cluster để tính TF-IDF đại diện
            cluster_text = " ".join(cluster_sentences)
            X_cluster = vectorizer.transform([cluster_text])
            
            # Lấy top 5 keywords có điểm TF-IDF cao nhất
            top_idx = np.argsort(X_cluster.toarray()[0])[::-1][:5]
            keywords = feature_names[top_idx].tolist()
            
            cluster_keywords[f"cluster_{i+1}"] = {
                "sentences": cluster_sentences,
                "keywords": keywords
            }

        # Tạo giải thích tự động
        topics_str = ", ".join(['[' + ', '.join(v['keywords']) + ']' for v in cluster_keywords.values()])
        explanation = (
            f"Paragraph has {n_clusters} semantic clusters with topics like {topics_str}. "
            f"Higher topic diversity leads to a semantic entropy of {round(entropy, 4)} "
            f"(normalized {round(normalized_entropy, 4)})."
        )

    except Exception as e:
        logger.warning(f"Clustering/Keyword extraction failed: {e}")
        explanation = f"Calculation done, but keyword extraction failed: {e}"

    return {
        "semantic_entropy": float(entropy),
        "calculate_semantic_entropy": float(entropy) * scale_factor,
        "normalized_entropy": float(normalized_entropy),
        "num_sentences": len(sentences),
        "clusters": cluster_keywords,
        "explanation": explanation
    }

def convert_json_string_to_object(json_string):
  """
  Chuyển đổi một chuỗi JSON thành một đối tượng Python (List/Dictionary).

  Args:
    json_string: Chuỗi chứa dữ liệu JSON.

  Returns:
    Đối tượng Python được tạo ra từ chuỗi JSON.
  """
  try:
    # json.loads() sẽ phân tích chuỗi JSON và trả về đối tượng Python tương ứng.
    json_object = json.loads(json_string)
    return json_object
  except json.JSONDecodeError as e:
    print(f"Lỗi khi giải mã JSON: {e}")
    return None