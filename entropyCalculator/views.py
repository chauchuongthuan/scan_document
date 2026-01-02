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
import os
from google import genai
from google.genai import types

from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
import re
import nltk
from nltk.tokenize import sent_tokenize
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from typing import Dict, List, Tuple, Optional

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
                            "calculate_semantic_entropy": 1.0 * math.pi * 2 * 0.72,
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
                        "calculate_semantic_entropy": float(entropy) * math.pi * 2 * 0.72,
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
                        "calculate_semantic_entropy": float(entropy) * math.pi * 2 * 0.72,
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
                scale_factor = math.pi * 2 * 0.72
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

class CalculateEntropyByEachParagraphViewV3(View):
    """
    API view to calculate semantic entropy by paragraph
    """
    @login_required(login_url="login_cms")
    def post(request):
        if request.method == 'POST':
            try:
                text = request.POST.get('paragraph', '')
                paragraphs = [p.strip() for p in re.split(r'\n{1,}', text) if len(p.strip()) > 0]

                results = []
                
                for idx, paragraph in enumerate(paragraphs, start=1):
                    # Use the advanced analyzer
                    analysis = UniversalSemanticEntropyCalculator().calculate_semantic_entropy(paragraph)
                    
                    # Format results for your expected output
                    # if 'combined_entropy' in analysis:
                    #     entropy = analysis['combined_entropy']
                    # else:
                    #     entropy = analysis['entropy']

                    entropy = analysis['semantic_entropy']

                    results.append({
                        "paragraph_index": idx,
                        "semantic_entropy": float(entropy),
                        "calculate_semantic_entropy": float(entropy) * math.pi * 2 * 0.72,
                        "normalized_entropy": float(entropy),
                        "num_sentences": analysis['num_sentences'],
                        "explanation": analysis['explanation'],
                        "detailed_analysis": {
                            'variance_entropy': analysis['variance_entropy'],
                            'similarity_entropy': analysis['similarity_entropy'],
                            'certainty_entropy': analysis['certainty_entropy'],
                            'sentence_analysis': analysis['sentence_analysis']
                        }
                    })
                
                # Calculate final entropy
                final_semantic_entropy = sum(item['semantic_entropy'] for item in results)
                
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

        return render(request, 'entropy/create-v3.html')

class CalculateEntropyByEachParagraphViewV4(View):
    """
    API view tính semantic entropy theo công thức lý thuyết
    """
    @login_required(login_url="login_cms")
    def post(request):
        if request.method == 'POST':
            try:
                text = request.POST.get('paragraph', '')

                paragraphs = [p.strip() for p in re.split(r'\n{1,}', text) if len(p.strip()) > 0]
                
                results = []
                
                for idx, paragraph in enumerate(paragraphs, start=1):
                    # Phân tích toàn bộ văn bản (có thể chia đoạn nếu cần)
                    analysis = EnhancedTheoreticalCalculator().calculate_semantic_entropy(paragraph)
                    
                    # Áp dụng công thức tính của bạn
                    entropy = analysis['semantic_entropy']
                    
                    # Chuẩn bị kết quả
                    results.append({
                        "paragraph_index": idx,
                        "semantic_entropy": float(entropy),
                        "calculate_semantic_entropy": float(entropy) * math.pi * 2 * 0.72,
                        "normalized_entropy": float(analysis['normalized_entropy']),
                        "num_sentences": analysis['num_sentences'],
                        "num_semantic_clusters": analysis.get('num_semantic_clusters', 1),
                        "explanation": analysis['explanation'],
                        "detailed_analysis": {
                            'cluster_distribution': analysis.get('cluster_distribution', {}),
                            'clusters_detail': analysis.get('clusters_detail', {})
                        }
                    }) 
                
                # Tính final entropy (theo logic của bạn)
                final_semantic_entropy = sum(item['semantic_entropy'] for item in results)
                
                return JsonResponse({
                    "status": "success",
                    "message": "Calculated semantic entropy using theoretical formula!",
                    "result": {
                        "detail_results": results,
                        "final_semantic_entropy": final_semantic_entropy,
                        "analysis_method": "theoretical_semantic_entropy"
                    }
                })
                
            except Exception as e:
                return JsonResponse({
                    "status": "error",
                    "message": f"Calculate failed: {str(e)}"
                }, status=400)
        
        return render(request, 'entropy/create-v4.html')

class MarketEntropyCalculator:
    """Specialized calculator for market/financial text"""
    
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Market-specific reference sentences
        self.market_references = self._create_market_references()
        
    def _create_market_references(self) -> Dict:
        """Create market-specific reference sentences"""
        return {
            'factual_reporting': [
                "Prices are currently at $100 per unit.",
                "The volume traded was 1,000 units.",
                "The market opened at 9:00 AM.",
                "The exchange rate is 1.20.",
                "The index closed at 5,000 points.",
                "Trading volume was 2 million shares.",
                "The price range was $50 to $55.",
                "The stock is trading at $25.50.",
                "The yield is currently 3.5%.",
                "The inflation rate is 2.1%."
            ],
            'speculative_analysis': [
                "Prices may rise in the coming weeks.",
                "The market could potentially decline.",
                "There is a chance that rates will increase.",
                "We might see a correction soon.",
                "It's possible that demand will soften.",
                "The trend could reverse at any time.",
                "We cannot be sure about future direction.",
                "The outlook remains uncertain.",
                "Many factors could influence the outcome.",
                "Predictions are difficult at this time."
            ],
            'definitive_analysis': [
                "The market will definitely continue its uptrend.",
                "Prices are certain to rise next quarter.",
                "There is no doubt about the recovery.",
                "The trend is absolutely clear.",
                "This will undoubtedly lead to higher prices.",
                "The data conclusively shows improvement.",
                "It is guaranteed that volumes will increase.",
                "The evidence clearly supports this view.",
                "This is an undeniable trend.",
                "The outcome is absolutely predictable."
            ],
            'hedged_statement': [
                "In my opinion, prices might stabilize.",
                "I believe there's a possibility of recovery.",
                "Some analysts suggest that the trend may change.",
                "It appears that conditions could improve.",
                "One interpretation is that demand will grow.",
                "Based on current data, it seems likely.",
                "There are indications that prices may firm.",
                "The evidence seems to point toward recovery.",
                "It looks as though the market may bottom.",
                "There are reasons to think that prices could rise."
            ]
        }
    
    def analyze_market_text(self, text: str) -> Dict:
        """Analyze market/financial text for entropy"""
        sentences = self._split_market_sentences(text)
        
        if len(sentences) == 0:
            return {'error': 'No sentences found'}
        
        sentence_analyses = []
        for sentence in sentences:
            analysis = self._analyze_market_sentence(sentence)
            sentence_analyses.append(analysis)
        
        # Calculate overall entropy
        entropies = [a['entropy'] for a in sentence_analyses]
        avg_entropy = np.mean(entropies)
        entropy_variation = np.std(entropies)
        
        # Market text with specific numbers has lower entropy
        # Adjust for numerical specificity
        numeric_score = self._calculate_numeric_specificity(text)
        adjusted_entropy = avg_entropy * (1.0 - numeric_score * 0.3)
        
        # Adjust for temporal specificity
        temporal_score = self._calculate_temporal_specificity(text)
        adjusted_entropy = adjusted_entropy * (1.0 - temporal_score * 0.2)
        
        return {
            'market_entropy': float(min(max(adjusted_entropy, 0.0), 1.0)),
            'raw_entropy': float(avg_entropy),
            'numeric_specificity': float(numeric_score),
            'temporal_specificity': float(temporal_score),
            'entropy_variation': float(entropy_variation),
            'num_sentences': len(sentences),
            'sentence_analyses': sentence_analyses,
            'explanation': self._generate_market_explanation(text, adjusted_entropy, numeric_score)
        }
    
    def _analyze_market_sentence(self, sentence: str) -> Dict:
        """Analyze a single market sentence"""
        # Check for numerical specificity first
        has_specific_numbers = bool(re.search(r'\d+[\d,.]*\s*(VND|USD|tons|kg|%|points)', sentence))
        
        # Check for definitive market language
        definitive_terms = ['are', 'is', 'was', 'were', 'ranging from', 'quoted at', 'indicated at']
        has_definitive_language = any(term in sentence.lower() for term in definitive_terms)
        
        # Embedding analysis
        sentence_embedding = self.model.encode(sentence, convert_to_tensor=True)
        
        # Compare to market references
        category_scores = {}
        for category, references in self.market_references.items():
            ref_embeddings = self.model.encode(references, convert_to_tensor=True)
            similarities = torch.nn.functional.cosine_similarity(
                sentence_embedding, ref_embeddings
            )
            category_scores[category] = float(similarities.max().cpu().numpy())
        
        # Map categories to entropy
        category_entropy = {
            'factual_reporting': 0.2,
            'definitive_analysis': 0.3,
            'hedged_statement': 0.6,
            'speculative_analysis': 0.8
        }
        
        # Weighted average
        total_score = sum(category_scores.values())
        if total_score > 0:
            weighted_entropy = sum(
                category_scores[cat] * category_entropy[cat]
                for cat in category_scores
            ) / total_score
        else:
            weighted_entropy = 0.5
        
        # Adjust for numerical specificity
        if has_specific_numbers:
            weighted_entropy *= 0.7  # Reduce entropy for specific numbers
        
        # Adjust for definitive language
        if has_definitive_language:
            weighted_entropy *= 0.8  # Reduce entropy for definitive statements
        
        return {
            'sentence': sentence,
            'entropy': float(weighted_entropy),
            'has_specific_numbers': has_specific_numbers,
            'has_definitive_language': has_definitive_language,
            'dominant_category': max(category_scores, key=category_scores.get),
            'category_scores': {k: float(v) for k, v in category_scores.items()}
        }
    
    def _calculate_numeric_specificity(self, text: str) -> float:
        """Calculate how specific the numerical data is (0-1)"""
        # Find all numbers with units
        number_patterns = [
            r'\d{1,3}(?:,\d{3})*\s*(?:VND|USD|tons|kg|%)',  # Numbers with units
            r'\d+\.?\d*\s*(?:to|-)\s*\d+\.?\d*',  # Ranges
            r'@\s*\d+[\d,.]*',  # At symbols with numbers
            r'\+\d+'  # Positive differentials
        ]
        
        total_matches = 0
        for pattern in number_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            total_matches += len(matches)
        
        # Normalize to 0-1 scale (more matches = more specific)
        specificity = min(total_matches / 5.0, 1.0)
        return specificity
    
    def _calculate_temporal_specificity(self, text: str) -> float:
        """Calculate temporal specificity (0-1)"""
        temporal_terms = [
            'today', 'yesterday', 'tomorrow', 'weekend', 
            'now', 'currently', 'at present', 'as of'
        ]
        
        specific_temporal = [
            '2:53 PM', '2:53 AM', 'November 14, 2025', 
            'over the weekend', 'today\'s morning'
        ]
        
        score = 0
        for term in specific_temporal:
            if term in text:
                score += 0.3
        
        for term in temporal_terms:
            if term.lower() in text.lower():
                score += 0.1
        
        return min(score, 1.0)
    
    def _split_market_sentences(self, text: str) -> List[str]:
        """Split market text, preserving important markers"""
        # Clean but keep important market notation
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Remove bold but keep text
        text = re.sub(r'\*(?!\s)(.*?)\*', r'\1', text)  # Remove italics but not asterisk bullets
        
        # Use nltk but with custom handling for market abbreviations
        sentences = nltk.sent_tokenize(text)
        
        # Filter and clean
        cleaned = []
        for sent in sentences:
            sent = sent.strip()
            if len(sent) > 5:  # Keep meaningful sentences
                # Restore important market notation that might have been broken
                if sent.endswith('VND/kg') and len(cleaned) > 0:
                    cleaned[-1] = cleaned[-1] + ' ' + sent
                else:
                    cleaned.append(sent)
        
        return cleaned
    
    def _generate_market_explanation(self, text: str, entropy: float, numeric_specificity: float) -> str:
        """Generate market-appropriate explanation"""
        if entropy < 0.3:
            level = "low"
            if numeric_specificity > 0.5:
                reason = "high numerical specificity and factual reporting"
            else:
                reason = "definitive market analysis"
        elif entropy < 0.5:
            level = "medium-low"
            reason = "mix of factual reporting with some analytical commentary"
        elif entropy < 0.7:
            level = "medium-high"
            reason = "analytical commentary with some speculative elements"
        else:
            level = "high"
            reason = "highly speculative or uncertain market analysis"
        
        return (f"This market text shows {level} semantic entropy ({entropy:.2f}) "
                f"due to its {reason}. The text contains {numeric_specificity:.1%} "
                f"numerical specificity, indicating {'high' if numeric_specificity > 0.5 else 'moderate'} factual content.")

class TransformerEntropyCalculator:
    """Using HuggingFace transformer models that definitely exist"""
    
    def __init__(self):
        # These models definitely exist on HuggingFace
        self.sentiment_model = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )
        
        # For zero-shot classification (works for any text)
        self.zero_shot_model = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli"
        )
        
        # Sentence transformer for embeddings
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def analyze_with_zero_shot(self, text: str) -> Dict:
        """
        Use zero-shot classification to analyze certainty
        """
        # Define categories that correlate with certainty
        candidate_labels = [
            "certain and definitive statement",
            "probable statement with confidence",
            "uncertain or speculative statement",
            "ambiguous or unclear statement"
        ]
        
        # Get classification
        result = self.zero_shot_model(text, candidate_labels)
        
        # Map to entropy values
        label_to_entropy = {
            "certain and definitive statement": 0.1,
            "probable statement with confidence": 0.4,
            "uncertain or speculative statement": 0.7,
            "ambiguous or unclear statement": 0.9
        }
        
        # Get scores
        labels = result['labels']
        scores = result['scores']
        
        # Weighted entropy
        weighted_entropy = sum(
            scores[i] * label_to_entropy.get(labels[i], 0.5)
            for i in range(len(labels))
        )
        
        # Get top label
        top_label = labels[0]
        top_score = scores[0]
        
        return {
            'entropy': weighted_entropy,
            'top_label': top_label,
            'top_score': top_score,
            'all_scores': dict(zip(labels, scores)),
            'explanation': f"Zero-shot classification: '{top_label}' with {top_score:.2f} confidence"
        }
    
    def analyze_with_sentiment_and_embedding(self, text: str) -> Dict:
        """
        Combine sentiment analysis with embedding similarity
        """
        # Sentiment analysis
        sentiment_result = self.sentiment_model(text)[0]
        
        # Get embedding
        embedding = self.embedding_model.encode(text)
        
        # Reference embeddings for comparison
        certain_ref = self.embedding_model.encode("This is absolutely certain.")
        uncertain_ref = self.embedding_model.encode("This is uncertain and speculative.")
        
        # Calculate similarities
        sim_certain = np.dot(embedding, certain_ref) / (
            np.linalg.norm(embedding) * np.linalg.norm(certain_ref)
        )
        sim_uncertain = np.dot(embedding, uncertain_ref) / (
            np.linalg.norm(embedding) * np.linalg.norm(uncertain_ref)
        )
        
        # Sentiment affects certainty
        # Positive sentiment often correlates with certainty
        if sentiment_result['label'] == 'POSITIVE':
            sentiment_factor = 0.3
        else:
            sentiment_factor = 0.7
        
        # Combine factors
        similarity_factor = sim_uncertain / (sim_certain + sim_uncertain + 1e-10)
        
        # Final entropy
        entropy = (similarity_factor + sentiment_factor) / 2
        
        return {
            'entropy': float(entropy),
            'sentiment': sentiment_result,
            'similarity_to_certain': float(sim_certain),
            'similarity_to_uncertain': float(sim_uncertain),
            'explanation': f"Sentiment: {sentiment_result['label']} ({sentiment_result['score']:.2f}). "
                        f"Semantic similarity indicates {'higher' if entropy > 0.5 else 'lower'} uncertainty."
        }

class UniversalSemanticEntropyCalculator:
    """
    Universal calculator that works with ANY text type without hard-coding
    Uses information theory principles and neural embeddings
    """
    
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Create a diverse set of reference sentences spanning certainty levels
        # These are GENERAL examples, not domain-specific
        self.reference_categories = self._create_universal_references()
        
    def _create_universal_references(self) -> Dict:
        """Create universal reference sentences covering all types of certainty"""
        return {
            'definitive_factual': [
                "The sky is blue.",
                "Water boils at 100 degrees Celsius.",
                "The Earth orbits the Sun.",
                "Two plus two equals four.",
                "Humans need oxygen to breathe.",
                "Paris is the capital of France.",
                "The sun rises in the east.",
                "Ice melts at 0 degrees Celsius.",
                "There are 24 hours in a day.",
                "Light travels faster than sound."
            ],
            'confident_prediction': [
                "It will rain tomorrow.",
                "The team will win the game.",
                "Stock prices will rise next week.",
                "The movie will be successful.",
                "She will arrive at 5 PM.",
                "Demand will increase in summer.",
                "The project will finish on time.",
                "He will accept the offer.",
                "Sales will grow this quarter.",
                "The temperature will drop tonight."
            ],
            'moderate_uncertainty': [
                "It might rain later.",
                "Prices could go up or down.",
                "Perhaps the meeting will be cancelled.",
                "There's a chance of success.",
                "Maybe we should reconsider.",
                "It's possible that will happen.",
                "I'm not entirely sure.",
                "This could be interpreted differently.",
                "The outcome is unclear.",
                "We'll have to wait and see."
            ],
            'high_uncertainty': [
                "I have no idea what will happen.",
                "The situation is completely unpredictable.",
                "Anything could happen at this point.",
                "It's impossible to know for sure.",
                "The future is uncertain.",
                "There are too many unknown factors.",
                "No one can predict with certainty.",
                "The evidence is inconclusive.",
                "This is pure speculation.",
                "We're in uncharted territory."
            ],
            'speculative': [
                "What if we tried a different approach?",
                "Imagine a world where this happens.",
                "Suppose that were true, then...",
                "Could it be that we're missing something?",
                "One might wonder whether...",
                "It's interesting to consider...",
                "Let's hypothesize for a moment...",
                "This raises the question of...",
                "I'm just thinking out loud...",
                "In a hypothetical scenario..."
            ]
        }
    
    def calculate_semantic_entropy(self, text: str) -> Dict:
        """
        Calculate semantic entropy for ANY text
        
        This works by:
        1. Analyzing how the text's semantic embeddings distribute
        2. Comparing to universal certainty patterns
        3. Using information theory principles
        """
        # Split into sentences
        sentences = self._split_sentences(text)
        
        if len(sentences) == 0:
            return self._empty_result()
        
        # Calculate embedding-based entropy
        embeddings = self.model.encode(sentences, normalize_embeddings=True)
        
        # METHOD 1: Variance-based entropy (measures semantic spread)
        if len(sentences) > 1:
            # Calculate variance in embedding space
            centroid = np.mean(embeddings, axis=0)
            distances = np.sqrt(np.sum((embeddings - centroid) ** 2, axis=1))
            variance_entropy = np.std(distances) / (np.mean(distances) + 1e-10)
            variance_entropy = min(variance_entropy, 1.0)
        else:
            variance_entropy = self._single_sentence_entropy(sentences[0], embeddings[0])
        
        # METHOD 2: Pairwise similarity entropy
        if len(sentences) > 1:
            similarity_matrix = cosine_similarity(embeddings)
            np.fill_diagonal(similarity_matrix, 0)  # Ignore self-similarity
            avg_similarity = np.mean(similarity_matrix)
            similarity_entropy = 1 - avg_similarity
        else:
            similarity_entropy = 0.5  # Neutral for single sentences
        
        # METHOD 3: Certainty analysis (using universal references)
        certainty_entropy = self._analyze_certainty_level(text)
        
        # Combine methods with intelligent weighting
        if len(sentences) > 1:
            # For multi-sentence text, weight variance more
            combined_entropy = (
                0.4 * variance_entropy +
                0.3 * similarity_entropy +
                0.3 * certainty_entropy
            )
        else:
            # For single sentence, rely more on certainty analysis
            combined_entropy = (
                0.2 * variance_entropy +
                0.1 * similarity_entropy +
                0.7 * certainty_entropy
            )
        
        # Ensure entropy is between 0 and 1
        final_entropy = max(0.0, min(1.0, combined_entropy))
        
        return {
            'semantic_entropy': float(final_entropy),
            'variance_entropy': float(variance_entropy),
            'similarity_entropy': float(similarity_entropy),
            'certainty_entropy': float(certainty_entropy),
            'num_sentences': len(sentences),
            'explanation': self._generate_universal_explanation(text, final_entropy, len(sentences)),
            'sentence_analysis': [
                {
                    'sentence': sent,
                    'certainty_score': float(self._sentence_certainty(sent))
                }
                for sent in sentences
            ]
        }
    
    def _single_sentence_entropy(self, sentence: str, embedding: np.ndarray) -> float:
        """Calculate entropy for a single sentence"""
        # Analyze sentence structure
        words = sentence.split()
        word_count = len(words)
        
        # Calculate lexical diversity
        unique_words = len(set(words))
        lexical_diversity = unique_words / word_count if word_count > 0 else 0
        
        # Check for hedging language (without hard-coding specific words)
        embedding_tensor = torch.tensor(embedding).unsqueeze(0)
        
        # Compare to reference categories
        category_scores = []
        for category, references in self.reference_categories.items():
            ref_embeddings = self.model.encode(references, normalize_embeddings=True)
            ref_tensor = torch.tensor(ref_embeddings)
            similarities = torch.nn.functional.cosine_similarity(
                embedding_tensor, ref_tensor
            )
            category_scores.append(float(similarities.max()))
        
        # Category-based entropy mapping
        category_weights = [0.1, 0.3, 0.5, 0.7, 0.8]  # Corresponding to categories
        weighted_entropy = sum(
            score * weight for score, weight in zip(category_scores, category_weights)
        ) / (sum(category_scores) + 1e-10)
        
        # Combine with lexical diversity
        final_entropy = (weighted_entropy * 0.7) + (lexical_diversity * 0.3)
        
        return float(final_entropy)
    
    def _analyze_certainty_level(self, text: str) -> float:
        """Analyze certainty level using semantic similarity to reference patterns"""
        text_embedding = self.model.encode(text, normalize_embeddings=True)
        text_tensor = torch.tensor(text_embedding).unsqueeze(0)
        
        # Calculate similarity to each certainty category
        category_entropies = []
        category_similarities = []
        
        # Map categories to entropy values
        category_mapping = {
            'definitive_factual': 0.1,
            'confident_prediction': 0.3,
            'moderate_uncertainty': 0.5,
            'high_uncertainty': 0.8,
            'speculative': 0.7
        }
        
        for category, references in self.reference_categories.items():
            ref_embeddings = self.model.encode(references, normalize_embeddings=True)
            ref_tensor = torch.tensor(ref_embeddings)
            similarities = torch.nn.functional.cosine_similarity(text_tensor, ref_tensor)
            max_similarity = float(similarities.max())
            
            category_similarities.append(max_similarity)
            category_entropies.append(category_mapping.get(category, 0.5))
        
        # Weighted average based on similarity
        total_similarity = sum(category_similarities)
        if total_similarity > 0:
            weighted_entropy = sum(
                sim * ent for sim, ent in zip(category_similarities, category_entropies)
            ) / total_similarity
        else:
            weighted_entropy = 0.5
        
        return weighted_entropy
    
    def _sentence_certainty(self, sentence: str) -> float:
        """Calculate certainty score for a single sentence"""
        # This uses the model to compare with reference patterns
        # NOT hard-coded keywords
        sentence_embedding = self.model.encode(sentence, normalize_embeddings=True)
        sentence_tensor = torch.tensor(sentence_embedding).unsqueeze(0)
        
        # Compare to definitive vs uncertain references
        definitive_refs = self.reference_categories['definitive_factual']
        uncertain_refs = self.reference_categories['moderate_uncertainty'] + \
                        self.reference_categories['high_uncertainty']
        
        definitive_embeddings = self.model.encode(definitive_refs, normalize_embeddings=True)
        uncertain_embeddings = self.model.encode(uncertain_refs, normalize_embeddings=True)
        
        # Calculate similarities
        def_similarities = torch.nn.functional.cosine_similarity(
            sentence_tensor, torch.tensor(definitive_embeddings)
        )
        unc_similarities = torch.nn.functional.cosine_similarity(
            sentence_tensor, torch.tensor(uncertain_embeddings)
        )
        
        avg_def_sim = float(def_similarities.mean())
        avg_unc_sim = float(unc_similarities.mean())
        
        # Certainty score (0=uncertain, 1=certain)
        if avg_def_sim + avg_unc_sim > 0:
            certainty = avg_def_sim / (avg_def_sim + avg_unc_sim)
        else:
            certainty = 0.5
        
        return certainty
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences, handling various formats"""
        # Clean the text
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(?!\s)(.*?)\*', r'\1', text)
        text = re.sub(r'\[.*?\]\(.*?\)', '', text)
        
        # Split by common sentence boundaries
        sentences = nltk.sent_tokenize(text)
        
        # Filter and clean
        cleaned = []
        for sent in sentences:
            sent = sent.strip()
            if len(sent) > 3 and not sent.isdigit():
                cleaned.append(sent)
        
        return cleaned
    
    def _generate_universal_explanation(self, text: str, entropy: float, num_sentences: int) -> str:
        """Generate explanation that works for any text type"""
        if entropy < 0.25:
            level_desc = "very low"
            reason = "The text shows high semantic coherence and definitive language."
        elif entropy < 0.5:
            level_desc = "low to moderate"
            reason = "The text is relatively coherent with some variation in topics or certainty."
        elif entropy < 0.75:
            level_desc = "moderate to high"
            reason = "The text shows significant semantic diversity or uncertainty."
        else:
            level_desc = "very high"
            reason = "The text is highly diverse, speculative, or uncertain."
        
        sentence_desc = f"{num_sentences} sentence{'s' if num_sentences != 1 else ''}"
        
        return (
            f"This text contains {sentence_desc} with {level_desc} semantic entropy "
            f"({entropy:.2f}). {reason} The entropy score measures how much information "
            f"or uncertainty is contained in the semantic content."
        )
    
    def _empty_result(self):
        """Return result for empty text"""
        return {
            'semantic_entropy': 0.0,
            'variance_entropy': 0.0,
            'similarity_entropy': 0.0,
            'certainty_entropy': 0.0,
            'num_sentences': 0,
            'explanation': 'No text content to analyze.',
            'sentence_analysis': []
        }

class GeminiEntropyAnalyzer:
    """
    Sử dụng Google Gemini API để phân tích entropy
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GG_AI_STUDIO_KEY", "")
        if not self.api_key:
            raise ValueError("GG_AI_STUDIO_KEY không được tìm thấy")
        
        self.client = genai.Client(api_key=self.api_key)
        
        self.model = "gemini-2.5-flash" 
    
    def analyze_semantic_entropy(self, text: str) -> Dict:
        """
        Phân tích semantic entropy sử dụng Gemini
        """
        try:
            # Chuẩn bị prompt
            prompt = self._build_entropy_prompt(text)
            
            # Gọi Gemini API
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            print("response", response)
            # Parse kết quả
            result_text = response.text
            
            # Loại bỏ markdown code blocks nếu có
            result_text = result_text.replace('```json', '').replace('```', '').strip()
            
            # Parse JSON
            result = json.loads(result_text)
            
            # Đảm bảo có đủ các trường
            if 'semantic_entropy' not in result:
                result['semantic_entropy'] = 0.5
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Raw response: {result_text}")
            return self._fallback_analysis(text, result_text)
        except Exception as e:
            print(f"Gemini API error: {e}")
            return self._fallback_analysis(text)
    
    def _build_entropy_prompt(self, text: str) -> str:
        """
        Xây dựng prompt cho phân tích entropy
        """
        return f"""
        Bạn là một chuyên gia phân tích ngôn ngữ. Hãy phân tích "semantic entropy" (mức độ không chắc chắn/thông tin) của văn bản sau.

        **VĂN BẢN CẦN PHÂN TÍCH:**
        {text}

        **HƯỚNG DẪN PHÂN TÍCH:**
        1. Phân tích mức độ chắc chắn: Văn bản chứa thông tin xác định (số liệu, sự kiện) hay không chắc chắn (dự đoán, phỏng đoán)?
        2. Phân tích tính cụ thể: Văn bản có chứa thông tin cụ thể (thời gian, địa điểm, số liệu) hay chung chung?
        3. Phân tích ngôn ngữ: Sử dụng ngôn ngữ khẳng định hay phỏng đoán?
        4. Phân tích domain: Đây là báo cáo thị trường, tin tức, hay phân tích?

        **THANG ĐIỂM ENTROPY (0-1):**
        - 0.0-0.2: Thông tin rất chắc chắn, cụ thể, có số liệu xác thực
        - 0.2-0.4: Thông tin khá chắc chắn, có một vài yếu tố không chắc chắn
        - 0.4-0.6: Cân bằng giữa thông tin chắc chắn và không chắc chắn
        - 0.6-0.8: Nhiều yếu tố không chắc chắn, phỏng đoán
        - 0.8-1.0: Rất không chắc chắn, thiếu bằng chứng, dự đoán thuần túy

        **YÊU CẦU ĐẦU RA (JSON format):**
        {{
            "semantic_entropy": 0.0,  // Giá trị từ 0 đến 1
            "certainty_score": 0.0,    // Điểm chắc chắn từ 0 đến 1
            "key_factors": [],         // Các yếu tố chính ảnh hưởng đến entropy
            "uncertainty_elements": [], // Các yếu tố không chắc chắn được phát hiện
            "certainty_elements": [],  // Các yếu tố chắc chắn được phát hiện
            "domain": "",              // Domain của văn bản (market, news, etc.)
            "explanation": "",         // Giải thích chi tiết bằng tiếng Việt
            "num_sentences_estimated": 0  // Ước lượng số câu
        }}

        **VÍ DỤ:**
        Văn bản: "Giá cà phê hôm nay là 100,000 VND/kg"
        Kết quả: {{
            "semantic_entropy": 0.1,
            "explanation": "Thông tin rất chắc chắn với số liệu cụ thể",
            ...
        }}

        Chỉ trả về JSON, không có nội dung nào khác.
        """
    
    def _fallback_analysis(self, text: str, raw_response: str = "") -> Dict:
        """
        Phân tích fallback nếu Gemini fail
        """
        # Phân tích cơ bản
        sentences = len(re.split(r'[.!?]+', text))
        words = len(text.split())
        
        # Heuristic đơn giản
        if sentences == 0:
            entropy = 0.5
        elif sentences == 1:
            entropy = 0.3
        else:
            # Tính độ dài trung bình
            avg_len = words / sentences
            if avg_len > 25:
                entropy = 0.7  # Văn bản phức tạp
            elif avg_len < 10:
                entropy = 0.4  # Văn bản đơn giản
            else:
                entropy = 0.5
        
        return {
            "semantic_entropy": entropy,
            "certainty_score": 1 - entropy,
            "key_factors": ["Fallback analysis"],
            "uncertainty_elements": [],
            "certainty_elements": [],
            "domain": "unknown",
            "explanation": f"Phân tích cơ bản (Gemini không khả dụng). Entropy: {entropy:.2f}",
            "num_sentences_estimated": sentences,
            "is_fallback": True
        }
    
    def batch_analyze(self, texts: List[str]) -> List[Dict]:
        """
        Phân tích batch để tối ưu chi phí
        """
        results = []
        
        for text in texts:
            result = self.analyze_semantic_entropy(text)
            results.append(result)
        
        return results

class TheoreticalSemanticEntropyCalculator:
    """
    Tính semantic entropy theo đúng công thức lý thuyết
    H_s(Ũ) = - Σ p(𝒰_i) log p(𝒰_i)
    """
    
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def calculate_semantic_entropy(self, text: str) -> Dict:
        """
        Tính semantic entropy dựa trên phân cụm ngữ nghĩa
        """
        # 1. Tách câu
        sentences = self._split_sentences(text)
        
        if len(sentences) == 0:
            return self._empty_result()
        
        # 2. Mã hóa các câu thành embeddings
        embeddings = self.model.encode(sentences, normalize_embeddings=True)
        
        # 3. Phân cụm các câu thành các lớp ý nghĩa (semantic clusters)
        # Đây chính là ánh xạ đồng nghĩa f: mỗi câu → lớp ý nghĩa
        clusters = self._cluster_sentences(embeddings)
        
        # 4. Tính xác suất của mỗi lớp ý nghĩa
        # Giả sử mỗi câu có xác suất bằng nhau: p(u_i) = 1/N
        N = len(sentences)
        cluster_probs = self._calculate_cluster_probabilities(clusters, N)
        
        # 5. Tính semantic entropy theo công thức
        entropy_sebits = self._calculate_theoretical_entropy(cluster_probs)
        
        # 6. Tính normalized entropy (0-1)
        max_entropy = math.log2(len(cluster_probs)) if len(cluster_probs) > 0 else 0
        normalized_entropy = entropy_sebits / max_entropy if max_entropy > 0 else 0
        
        # 7. Tạo explanation
        explanation = self._generate_theoretical_explanation(
            len(sentences), len(cluster_probs), entropy_sebits, normalized_entropy
        )
        
        return {
            'semantic_entropy': float(entropy_sebits),  # Đơn vị: sebits
            'normalized_entropy': float(normalized_entropy),
            'num_sentences': len(sentences),
            'num_semantic_clusters': len(cluster_probs),
            'cluster_distribution': cluster_probs,
            'explanation': explanation,
            'clusters_detail': self._get_cluster_details(clusters, sentences)
        }
    
    def _cluster_sentences(self, embeddings: np.ndarray) -> List[List[int]]:
        """
        Phân cụm các câu thành các lớp ý nghĩa
        Trả về: danh sách các cụm, mỗi cụm là list chỉ số của câu
        """
        n = len(embeddings)
        
        if n <= 1:
            # Nếu chỉ có 1 câu, coi như 1 cụm
            return [[0]] if n == 1 else []
        
        # Xác định số cụm tối ưu
        # Có thể dùng elbow method, nhưng ở đây dùng heuristic
        n_clusters = min(5, max(2, n // 2))
        
        # Phân cụm bằng KMeans
        kmeans = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
        labels = kmeans.fit_predict(embeddings)
        
        # Nhóm các chỉ số theo cluster
        clusters_dict = {}
        for idx, label in enumerate(labels):
            if label not in clusters_dict:
                clusters_dict[label] = []
            clusters_dict[label].append(idx)
        
        # Chuyển thành list
        clusters = list(clusters_dict.values())
        
        # Nếu có cụm quá nhỏ (1 phần tử), gộp vào cụm gần nhất
        merged_clusters = []
        small_clusters = []
        
        for cluster in clusters:
            if len(cluster) == 1:
                small_clusters.append(cluster[0])
            else:
                merged_clusters.append(cluster)
        
        # Gộp các cụm nhỏ vào cụm gần nhất
        for small_idx in small_clusters:
            # Tìm cụm gần nhất
            closest_cluster_idx = -1
            min_distance = float('inf')
            
            for i, cluster in enumerate(merged_clusters):
                # Tính khoảng cách trung bình đến cụm
                distances = []
                for c_idx in cluster:
                    dist = np.linalg.norm(embeddings[small_idx] - embeddings[c_idx])
                    distances.append(dist)
                avg_dist = np.mean(distances)
                
                if avg_dist < min_distance:
                    min_distance = avg_dist
                    closest_cluster_idx = i
            
            if closest_cluster_idx >= 0:
                merged_clusters[closest_cluster_idx].append(small_idx)
        
        return merged_clusters
    
    def _calculate_cluster_probabilities(self, clusters: List[List[int]], total_sentences: int) -> Dict[int, float]:
        """
        Tính xác suất của mỗi lớp ý nghĩa: p(𝒰_i) = Σ_{j∈𝒩_i} p(u_j)
        Giả sử p(u_j) = 1/N (đều nhau)
        """
        cluster_probs = {}
        
        for i, cluster in enumerate(clusters):
            # Xác suất của cụm = số câu trong cụm / tổng số câu
            probability = len(cluster) / total_sentences
            cluster_probs[i] = probability
        
        return cluster_probs
    
    def _calculate_theoretical_entropy(self, cluster_probs: Dict[int, float]) -> float:
        """
        Tính semantic entropy: H_s = - Σ p(𝒰_i) log2 p(𝒰_i)
        """
        entropy = 0.0
        
        for prob in cluster_probs.values():
            if prob > 0:
                entropy -= prob * math.log2(prob)
        
        return entropy
    
    def _split_sentences(self, text: str) -> List[str]:
        """Tách văn bản thành các câu"""
        # Clean text
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(?!\s)(.*?)\*', r'\1', text)
        text = re.sub(r'\[.*?\]\(.*?\)', '', text)
        
        # Tách câu
        sentences = nltk.sent_tokenize(text)
        
        # Lọc và làm sạch
        cleaned = []
        for sent in sentences:
            sent = sent.strip()
            if len(sent) > 3:  # Bỏ qua câu quá ngắn
                cleaned.append(sent)
        
        return cleaned
    
    def _generate_theoretical_explanation(self, num_sentences: int, num_clusters: int, 
                                        entropy: float, normalized_entropy: float) -> str:
        """Tạo giải thích theo lý thuyết"""
        return (
            f"The text contains {num_sentences} sentences grouped into {num_clusters} semantic clusters. "
            f"Semantic entropy calculated using theoretical formula: H_s = -Σ p(𝒰_i) log2 p(𝒰_i) = {entropy:.3f} sebits. "
            f"Normalized entropy: {normalized_entropy:.3f} (0-1 scale). "
            f"A higher value indicates more semantic diversity across the text."
        )
    
    def _get_cluster_details(self, clusters: List[List[int]], sentences: List[str]) -> Dict:
        """Lấy chi tiết từng cụm"""
        details = {}
        
        for i, cluster in enumerate(clusters):
            cluster_sentences = [sentences[idx] for idx in cluster]
            
            # Lấy câu đại diện (câu đầu tiên)
            representative = cluster_sentences[0] if cluster_sentences else ""
            
            details[f"cluster_{i}"] = {
                "size": len(cluster),
                "sentence_indices": cluster,
                "representative_sentence": representative,
                "all_sentences": cluster_sentences[:3]  # Giới hạn 3 câu
            }
        
        return details
    
    def _empty_result(self):
        """Kết quả cho văn bản trống"""
        return {
            'semantic_entropy': 0.0,
            'normalized_entropy': 0.0,
            'num_sentences': 0,
            'num_semantic_clusters': 0,
            'cluster_distribution': {},
            'explanation': 'No text content to analyze.',
            'clusters_detail': {}
        }

class EnhancedTheoreticalCalculator(TheoreticalSemanticEntropyCalculator):
    """
    Phiên bản nâng cao với xác suất không đều và xử lý single sentence
    """
    
    def calculate_semantic_entropy(self, text: str) -> Dict:
        """
        Tính semantic entropy với xác suất không đều cho các câu
        """
        sentences = self._split_sentences(text)
        
        if len(sentences) == 0:
            return self._empty_result()
        
        # Xử lý trường hợp single sentence
        if len(sentences) == 1:
            # Theo lý thuyết, nếu chỉ có 1 câu → 1 cụm → entropy = 0
            # Nhưng trong thực tế, một câu có thể chứa nhiều thông tin
            # Chúng ta có thể phân tích độ phức tạp của câu đó
            sentence_complexity = self._analyze_sentence_complexity(sentences[0])
            
            # Điều chỉnh: câu phức tạp có entropy cao hơn
            adjusted_entropy = sentence_complexity * 0.5  # Scale xuống
            
            return {
                'semantic_entropy': float(adjusted_entropy),
                'normalized_entropy': float(adjusted_entropy),
                'num_sentences': 1,
                'num_semantic_clusters': 1,
                'cluster_distribution': {0: 1.0},
                'explanation': f"Single sentence analyzed. Complexity score: {sentence_complexity:.2f}. "
                              f"Adjusted semantic entropy: {adjusted_entropy:.3f} sebits.",
                'is_single_sentence': True
            }
        
        embeddings = self.model.encode(sentences, normalize_embeddings=True)
        clusters = self._cluster_sentences(embeddings)
        
        # Tính xác suất không đều dựa trên độ dài câu
        sentence_weights = self._calculate_sentence_weights(sentences)
        total_weight = sum(sentence_weights)
        
        # Tính xác suất cụm
        cluster_probs = {}
        for i, cluster in enumerate(clusters):
            cluster_weight = sum(sentence_weights[idx] for idx in cluster)
            cluster_probs[i] = cluster_weight / total_weight
        
        # Tính entropy
        entropy_sebits = self._calculate_theoretical_entropy(cluster_probs)
        
        # Normalize
        max_entropy = math.log2(len(cluster_probs)) if len(cluster_probs) > 0 else 0
        normalized_entropy = entropy_sebits / max_entropy if max_entropy > 0 else 0
        
        explanation = self._generate_enhanced_explanation(
            len(sentences), len(clusters), entropy_sebits, normalized_entropy, 
            self._get_dominant_cluster_ratio(cluster_probs)
        )
        
        return {
            'semantic_entropy': float(entropy_sebits),
            'normalized_entropy': float(normalized_entropy),
            'num_sentences': len(sentences),
            'num_semantic_clusters': len(clusters),
            'cluster_distribution': cluster_probs,
            'sentence_weights': sentence_weights,
            'explanation': explanation,
            'clusters_detail': self._get_cluster_details(clusters, sentences)
        }
    
    def _calculate_sentence_weights(self, sentences: List[str]) -> List[float]:
        """
        Tính trọng số cho mỗi câu dựa trên độ dài và độ phức tạp
        """
        weights = []
        
        for sent in sentences:
            # Trọng số cơ bản dựa trên độ dài
            length_weight = len(sent.split()) / 10.0  # Chuẩn hóa
            
            # Thêm yếu tố phức tạp
            complexity = self._analyze_sentence_complexity(sent)
            
            # Kết hợp
            weight = length_weight * (1 + complexity * 0.5)
            weights.append(weight)
        
        # Chuẩn hóa để tổng = 1
        total = sum(weights)
        if total > 0:
            weights = [w/total for w in weights]
        
        return weights
    
    def _analyze_sentence_complexity(self, sentence: str) -> float:
        """
        Phân tích độ phức tạp của câu (0-1)
        """
        words = sentence.split()
        word_count = len(words)
        
        # Đếm clauses (xấp xỉ bằng số dấu câu)
        clauses = sentence.count(',') + sentence.count(';') + sentence.count(':') + 1
        
        # Đếm từ phức tạp (dài)
        long_words = sum(1 for w in words if len(w) > 6)
        
        # Tính complexity
        complexity = (
            min(word_count / 30.0, 1.0) * 0.4 +
            min(clauses / 5.0, 1.0) * 0.3 +
            min(long_words / len(words), 1.0) * 0.3 if len(words) > 0 else 0
        )
        
        return complexity
    
    def _get_dominant_cluster_ratio(self, cluster_probs: Dict[int, float]) -> float:
        """Tính tỷ lệ của cụm lớn nhất"""
        if not cluster_probs:
            return 0.0
        
        max_prob = max(cluster_probs.values())
        return max_prob
    
    def _generate_enhanced_explanation(self, num_sentences: int, num_clusters: int,
                                      entropy: float, normalized_entropy: float,
                                      dominant_ratio: float) -> str:
        """Tạo giải thích nâng cao"""
        if normalized_entropy < 0.3:
            diversity = "low semantic diversity"
            reason = f"one dominant cluster ({dominant_ratio:.0%} of content)"
        elif normalized_entropy < 0.6:
            diversity = "moderate semantic diversity"
            reason = f"balanced distribution across {num_clusters} clusters"
        else:
            diversity = "high semantic diversity"
            reason = f"well-distributed content across {num_clusters} semantic clusters"
        
        return (
            f"Text analysis: {num_sentences} sentences grouped into {num_clusters} semantic clusters. "
            f"Semantic entropy: {entropy:.3f} sebits (normalized: {normalized_entropy:.3f}). "
            f"This indicates {diversity}, with {reason}. "
            f"Calculation follows H_s(Ũ) = -Σ p(𝒰_i) log₂ p(𝒰_i) from semantic information theory."
        )