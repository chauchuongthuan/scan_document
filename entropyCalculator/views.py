from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from django.contrib.auth.decorators import login_required
# from .models import ViralContentAnalyzer
from django.shortcuts import render
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from math import log2
from coffee.helpers import split_sentences
import math

from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
import re
import nltk
from nltk.tokenize import sent_tokenize
from collections import Counter

nltk.download('punkt', quiet=True)

model = SentenceTransformer('all-MiniLM-L6-v2')
class CalculateEntropyByEachParagraphView(View):
    """
    API view to calculate semantic entropy by paragraph
    """
    @login_required(login_url="login_cms")
    def post(request):
        if request.method == 'POST':
            try:
                raw_text = request.POST.get('paragraph', '')
                paragraphs = [p.strip() for p in re.split(r'\n{1,}', raw_text) if len(p.strip()) > 0]

                results = []
                
                for idx, paragraph in enumerate(paragraphs, start=1):
                    sentences = split_sentences(paragraph)

                    # Nếu chỉ có 1 câu => entropy mặc định = 1
                    if len(sentences) <= 1:
                        results.append({
                            "paragraph_index": idx,
                            "semantic_entropy": 1.0,
                            "calculate_semantic_entropy": 1.0 * 4 * math.pi * 2 * 0.72,
                            "normalized_entropy": 1.0,
                            "num_sentences": len(sentences),
                            "clusters": None,
                            "explanation": "Only one sentence detected, default entropy = 1."
                        })
                        continue

                    # --- Lấy embeddings ---
                    embeddings = model.encode(sentences, normalize_embeddings=True)

                    # --- Tính entropy ---
                    mean_vec = np.mean(embeddings, axis=0, keepdims=True)
                    sims = cosine_similarity(embeddings, mean_vec).flatten()
                    deviations = 1 - sims
                    probs = deviations / deviations.sum() if deviations.sum() > 0 else np.ones_like(deviations)/len(deviations)
                    entropy = -np.sum(probs * np.log2(probs + 1e-12))
                    max_entropy = log2(len(sentences))
                    normalized_entropy = entropy / max_entropy

                    # --- Gom cụm ý ---
                    n_clusters = min(3, len(sentences))
                    kmeans = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
                    labels = kmeans.fit_predict(embeddings)

                    # --- Trích keywords ---
                    vectorizer = TfidfVectorizer(
                        stop_words='english',
                        token_pattern=r"(?u)\b[a-zA-Z0-9_./~,-]+\b"
                    )
                    X = vectorizer.fit_transform(sentences)
                    feature_names = np.array(vectorizer.get_feature_names_out())

                    cluster_keywords = {}
                    for i in range(n_clusters):
                        idxs = np.where(labels == i)[0]
                        cluster_text = " ".join([sentences[j] for j in idxs])
                        X_cluster = vectorizer.transform([cluster_text])
                        top_idx = np.argsort(X_cluster.toarray()[0])[::-1][:5]
                        cluster_keywords[f"cluster_{i+1}"] = {
                            "sentences": [sentences[j] for j in idxs],
                            "keywords": feature_names[top_idx].tolist()
                        }

                    # --- Giải thích ---
                    explanation = (
                        f"Paragraph {idx} has {n_clusters} semantic clusters "
                        f"with topics like {', '.join([', '.join(v['keywords']) for v in cluster_keywords.values()])}. "
                        f"Higher topic diversity leads to a semantic entropy of {entropy} "
                        f"(normalized {normalized_entropy})."
                    )
                    results.append({
                        "paragraph_index": idx,
                        "semantic_entropy": float(entropy),
                        "calculate_semantic_entropy": float(entropy) * 4 * math.pi * 2 * 0.72,
                        "normalized_entropy": float(normalized_entropy),
                        "num_sentences": len(sentences),
                        "clusters": cluster_keywords,
                        "explanation": explanation
                    })

                final_semantic_entropy = sum(item['calculate_semantic_entropy'] for item in results)
                return JsonResponse({
                    "status": "success",
                    "message": f"Calculated {len(results)} paragraph(s) successfully!",
                    "result": {
                        "detail_results": results,
                        "final_semantic_entropy": final_semantic_entropy,
                    }
                })

            except Exception as e:
                return JsonResponse({
                    "status": "error",
                    "message": f"Calculate failed: {str(e)}"
                }, status=400)

        return render(request, 'entropy/create.html')

class CalculateEntropyAllParagraphView(View):
    """
    API view to calculate semantic entropy by paragraph
    """
    @login_required(login_url="login_cms")
    def post(request):
        if request.method == 'POST':
            try:
                paragraph = request.POST.get('paragraph', '')
                sentences = split_sentences(paragraph)

                if len(sentences) <= 1:
                    return JsonResponse({
                        "status": "ok",
                        "message": "Too short text",
                        "result": {"semantic_entropy": 1.0}
                    })

                # --- Bước 1: Lấy embeddings ---
                embeddings = model.encode(sentences, normalize_embeddings=True)

                # --- Bước 2: Tính entropy ---
                mean_vec = np.mean(embeddings, axis=0, keepdims=True)
                sims = cosine_similarity(embeddings, mean_vec).flatten()
                deviations = 1 - sims
                probs = deviations / deviations.sum() if deviations.sum() > 0 else np.ones_like(deviations)/len(deviations)
                entropy = -np.sum(probs * np.log2(probs + 1e-12))
                max_entropy = log2(len(sentences))
                normalized_entropy = entropy / max_entropy

                # --- Bước 3: Gom cụm ý (topic clustering) ---
                n_clusters = min(3, len(sentences))  # tối đa 3 cụm cho đoạn ngắn
                kmeans = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
                labels = kmeans.fit_predict(embeddings)

                # --- Bước 4: Rút keywords cho từng cụm ---
                vectorizer = TfidfVectorizer(stop_words='english')
                X = vectorizer.fit_transform(sentences)
                feature_names = np.array(vectorizer.get_feature_names_out())

                cluster_keywords = {}
                for i in range(n_clusters):
                    idx = np.where(labels == i)[0]
                    cluster_text = " ".join([sentences[j] for j in idx])
                    X_cluster = vectorizer.transform([cluster_text])
                    top_idx = np.argsort(X_cluster.toarray()[0])[::-1][:5]
                    cluster_keywords[f"cluster_{i+1}"] = {
                        "sentences": [sentences[j] for j in idx],
                        "keywords": feature_names[top_idx].tolist()
                    }

                # --- Bước 5: Tạo giải thích ---
                explanation = (
                    f"This text has {n_clusters} semantic clusters "
                    f"with topics like {', '.join([', '.join(v['keywords'][:2]) for v in cluster_keywords.values()])}. "
                    f"Higher topic diversity leads to a semantic entropy of {entropy:.2f} "
                    f"(normalized {normalized_entropy:.2f})."
                )

                return JsonResponse({
                    "status": "success",
                    "message": "Calculate successfully!",
                    "result": {
                        "semantic_entropy": float(entropy),
                        "calculate_semantic_entropy": float(entropy) * 4 * math.pi * 2 * 0.72,
                        "normalized_entropy": float(normalized_entropy),
                        "num_sentences": len(sentences),
                        "clusters": cluster_keywords,
                        "explanation": explanation
                    }
                })

            except Exception as e:
                return JsonResponse({
                    "status": "error",
                    "message": f"Calculate failed: {str(e)}"
                }, status=400)

        return render(request, 'entropy/create-all-paragraph.html')

class CalculateEntropyByEachParagraphViewV2(View):
    @login_required(login_url="login_cms")
    def post(request):
        if request.method == 'POST':
            try:
                max_clusters = 5
                scale_factor = 4 * math.pi * 2 * 0.72
                text = request.POST.get('paragraph', '')

                if not text or len(text.strip()) < 5:
                    return JsonResponse({
                        "status": "error",
                        "message": "No valid text input."
                    }, status=400)

                paragraphs = [p.strip() for p in re.split(r'\n{1,}', text) if len(p.strip()) > 0]

                results = []

                def safe_number(x):
                    """Ép kiểu float và loại NaN/inf."""
                    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
                        return 0.0
                    return float(x)

                def deviation_entropy(embeddings):
                    mean_vec = embeddings.mean(axis=0, keepdims=True)
                    sims = cosine_similarity(embeddings, mean_vec).flatten()
                    deviations = 1 - sims
                    if deviations.sum() <= 0:
                        probs = np.ones_like(deviations) / len(deviations)
                    else:
                        probs = deviations / deviations.sum()
                    probs = np.nan_to_num(probs, nan=1/len(probs))
                    H = -np.sum(probs * np.log2(probs + 1e-12))
                    H_norm = H / math.log2(len(probs)) if len(probs) > 1 else 0.0
                    return safe_number(H), safe_number(H_norm)

                def cluster_entropy(embeddings, max_k):
                    n = len(embeddings)
                    if n <= 1:
                        return 0.0, 0.0, 1
                    k = min(max_k, n)
                    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10).fit(embeddings)
                    labels = kmeans.labels_
                    counts = np.bincount(labels, minlength=k)
                    probs = counts / counts.sum() if counts.sum() > 0 else np.ones(k) / k
                    probs = probs[probs > 0]
                    H = -np.sum(probs * np.log2(probs))
                    H_norm = H / math.log2(len(probs)) if len(probs) > 1 else 0.0
                    return safe_number(H), safe_number(H_norm), int(len(probs))

                for idx, para in enumerate(paragraphs, start=1):
                    sentences = [s for s in sent_tokenize(para) if len(s.split()) > 2]
                    if len(sentences) == 0:
                        continue

                    embeddings = model.encode(sentences, normalize_embeddings=True)

                    H_dev, Hn_dev = deviation_entropy(embeddings)
                    H_clu, Hn_clu, n_clusters = cluster_entropy(embeddings, max_clusters)

                    H_comb = safe_number((H_dev + H_clu) / 2)
                    Hn_comb = safe_number((Hn_dev + Hn_clu) / 2)
                    scaled = safe_number(H_comb * scale_factor)

                    results.append({
                        "paragraph_index": int(idx),
                        "num_sentences": int(len(sentences)),
                        "num_clusters": int(n_clusters),
                        "deviation_entropy": round(H_dev, 4),
                        "cluster_entropy": round(H_clu, 4),
                        "normalized_entropy": round(Hn_comb, 4),
                        "scaled_entropy": round(scaled, 4),
                        "text_preview": para
                    })

                final_entropy = safe_number(sum(r["scaled_entropy"] for r in results))

                return JsonResponse({
                    "status": "success",
                    "final_entropy": round(final_entropy, 4),
                    "paragraphs": results
                }, status=200)

            except Exception as e:
                return JsonResponse({
                    "status": "error",
                    "message": f"Calculate failed: {str(e)}"
                }, status=400)

        return render(request, 'entropy/create-v2.html')