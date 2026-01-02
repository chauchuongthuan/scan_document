from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import math
import re
import nltk
from typing import Dict, List, Tuple
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

nltk.download('punkt', quiet=True)

class CalculateEntropyByEachParagraphViewV5(View):
    """
    API view với adaptive hybrid entropy calculator
    """
    
    @login_required(login_url="login_cms")
    def post(request):
        if request.method == 'POST':
            try:
                text = request.POST.get('paragraph', '')
                paragraphs = [p.strip() for p in re.split(r'\n{1,}', text) if len(p.strip()) > 0]

                results = []
                
                for idx, paragraph in enumerate(paragraphs, start=1):
                    # Phân tích với adaptive calculator
                    analysis = AdaptiveEntropyCalculator().calculate_adaptive_entropy(paragraph)
                    
                    # Áp dụng công thức của bạn
                    entropy = analysis['semantic_entropy']
                    calculate_semantic_entropy = float(entropy) * math.pi * 2 * 0.72
                    
                    # Chuẩn bị kết quả
                    results.append({
                        "paragraph_index": idx,
                        "semantic_entropy": float(entropy),
                        "calculate_semantic_entropy": calculate_semantic_entropy,
                        "normalized_entropy": float(analysis['normalized_entropy']),
                        "num_sentences": analysis['num_sentences'],
                        "explanation": analysis['explanation'],
                        "analysis_method": analysis['analysis_method'],
                        "adaptive_weights": analysis.get('adaptive_weights', {}),
                        "text_features": analysis.get('text_features', {})
                    }) 
                
                # Tính final entropy
                final_semantic_entropy = sum(item['semantic_entropy'] for item in results)
                
                return JsonResponse({
                    "status": "success",
                    "message": "Calculated with adaptive hybrid method!",
                    "result": {
                        "detail_results": results,
                        "final_semantic_entropy": final_semantic_entropy,
                        "analysis_method": "adaptive_hybrid"
                    }
                })
                
            except Exception as e:
                import traceback
                print(f"Error: {traceback.format_exc()}")
                
                return JsonResponse({
                    "status": "error",
                    "message": f"Calculate failed: {str(e)}"
                }, status=400)
        
        return render(request, 'entropy/create-v5.html')

class HybridSemanticEntropyCalculator:
    """
    Kết hợp cả công thức lý thuyết và semantic similarity
    để có kết quả chính xác và nhất quán
    """
    
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Universal reference cho certainty analysis
        self.reference_categories = self._create_universal_references()
    
    def calculate_hybrid_entropy(self, text: str) -> Dict:
        """
        Tính entropy bằng phương pháp hybrid
        """
        # 1. Phân tích cơ bản
        sentences = self._split_sentences(text)
        
        if len(sentences) == 0:
            return self._empty_result()
        
        # 2. Tính entropy bằng nhiều phương pháp
        results = {
            'theoretical': self._calculate_theoretical_entropy(sentences),
            'similarity': self._calculate_similarity_entropy(sentences),
            'certainty': self._calculate_certainty_entropy(sentences)
        }
        
        # 3. Kết hợp thông minh dựa trên context
        final_entropy = self._intelligent_combination(results, sentences)
        
        # 4. Tạo giải thích chi tiết
        explanation = self._generate_hybrid_explanation(
            results, final_entropy, len(sentences)
        )
        
        return {
            'semantic_entropy': float(final_entropy),
            'normalized_entropy': float(final_entropy),  # Đã normalized 0-1
            'num_sentences': len(sentences),
            'method_breakdown': results,
            'explanation': explanation,
            'analysis_method': 'hybrid'
        }
    
    def _calculate_theoretical_entropy(self, sentences: List[str]) -> Dict:
        """
        Tính entropy theo công thức lý thuyết
        H_s = -Σ p(𝒰_i) log2 p(𝒰_i)
        """
        if len(sentences) == 1:
            # Với câu đơn: tính entropy dựa trên COMPLEXITY và CERTAINTY
            sentence = sentences[0]
            complexity = self._analyze_sentence_complexity(sentence)
            certainty = self._analyze_sentence_certainty(sentence)
            
            # Công thức CẢI TIẾN: entropy = complexity * (1 - certainty)
            # certainty cao -> entropy thấp, complexity cao -> entropy cao
            entropy = complexity * (1 - certainty)
            
            # Thêm điều chỉnh: câu càng chắc chắn, entropy càng thấp
            if certainty > 0.7:  # Rất chắc chắn
                entropy *= 0.5
            elif certainty > 0.5:  # Khá chắc chắn
                entropy *= 0.7
            
            return {
                'entropy': max(0.1, min(0.9, entropy)), 
                'method': 'single_sentence_enhanced',
                'complexity': complexity,
                'certainty': certainty
            }
        
        embeddings = self.model.encode(sentences, normalize_embeddings=True)
        
        # Phân cụm
        n_clusters = min(5, max(2, len(sentences) // 2))
        kmeans = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
        labels = kmeans.fit_predict(embeddings)
        
        # Tính xác suất cụm
        cluster_counts = {}
        for label in labels:
            cluster_counts[label] = cluster_counts.get(label, 0) + 1
        
        # Tính entropy
        total = len(sentences)
        entropy = 0.0
        for count in cluster_counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        
        # Normalize
        max_entropy = math.log2(len(cluster_counts)) if len(cluster_counts) > 0 else 0
        normalized = entropy / max_entropy if max_entropy > 0 else 0.5
        
        return {
            'entropy': normalized,
            'raw_entropy': entropy,
            'num_clusters': len(cluster_counts),
            'method': 'theoretical_clustering'
        }
    
    def _calculate_similarity_entropy(self, sentences: List[str]) -> Dict:
        """
        Tính entropy dựa trên semantic similarity
        """
        if len(sentences) <= 1:
            return {'entropy': 0.5, 'method': 'single_sentence_fallback'}
        
        embeddings = self.model.encode(sentences, normalize_embeddings=True)
        
        # Tính ma trận similarity
        sim_matrix = cosine_similarity(embeddings)
        
        # Tính độ đa dạng: 1 - average similarity
        np.fill_diagonal(sim_matrix, 0)  # Loại bỏ self-similarity
        n_pairs = len(sentences) * (len(sentences) - 1)
        if n_pairs > 0:
            avg_similarity = sim_matrix.sum() / n_pairs
            diversity = 1 - avg_similarity
        else:
            diversity = 0.5
        
        return {
            'entropy': float(diversity),
            'avg_similarity': float(avg_similarity) if 'avg_similarity' in locals() else 0,
            'method': 'semantic_similarity'
        }
    
    def _calculate_certainty_entropy(self, sentences: List[str]) -> Dict:
        """
        Tính entropy dựa trên mức độ chắc chắn
        """
        certainty_scores = []
        
        for sentence in sentences:
            # Phân tích mức độ chắc chắn của từng câu
            score = self._analyze_sentence_certainty(sentence)
            certainty_scores.append(score)
        
        if certainty_scores:
            avg_certainty = np.mean(certainty_scores)
            # Chuyển certainty thành entropy: chắc chắn cao = entropy thấp
            certainty_entropy = 1 - avg_certainty
            std_certainty = np.std(certainty_scores) if len(certainty_scores) > 1 else 0
        else:
            certainty_entropy = 0.5
            avg_certainty = 0.5
            std_certainty = 0
        
        return {
            'entropy': float(certainty_entropy),
            'avg_certainty': float(avg_certainty),
            'certainty_variation': float(std_certainty),
            'method': 'certainty_analysis'
        }
    
    def _analyze_sentence_certainty(self, sentence: str) -> float:
        """
        Phân tích mức độ chắc chắn của câu (0-1) - VERSION NHẠY HƠN
        """
        # Encode sentence
        sentence_embedding = self.model.encode([sentence], normalize_embeddings=True)
        
        # So sánh với các mẫu reference
        certainty_score = 0.5  # Mặc định
        
        if hasattr(self, 'reference_categories'):
            # Tính similarity với các reference - DÙNG MAX THAY VÌ MEAN
            high_sim = 0.0
            speculative_sim = 0.0
            
            # HIGH CERTAINTY references
            if 'high_certainty' in self.reference_categories:
                high_refs = self.reference_categories['high_certainty']
                high_embeddings = self.model.encode(high_refs, normalize_embeddings=True)
                high_similarities = cosine_similarity(sentence_embedding, high_embeddings)[0]
                high_sim = np.max(high_similarities)  # Dùng MAX để phát hiện pattern tốt nhất
            
            # SPECULATIVE references
            if 'speculative' in self.reference_categories:
                spec_refs = self.reference_categories['speculative']
                spec_embeddings = self.model.encode(spec_refs, normalize_embeddings=True)
                spec_similarities = cosine_similarity(sentence_embedding, spec_embeddings)[0]
                speculative_sim = np.max(spec_similarities)  # Dùng MAX
            
            # Thêm MEDIUM CERTAINTY references để phân biệt tốt hơn
            medium_sim = 0.0
            if 'medium_certainty' in self.reference_categories:
                medium_refs = self.reference_categories['medium_certainty']
                medium_embeddings = self.model.encode(medium_refs, normalize_embeddings=True)
                medium_similarities = cosine_similarity(sentence_embedding, medium_embeddings)[0]
                medium_sim = np.max(medium_similarities)
            
            # Công thức MỚI: tập trung vào sự khác biệt giữa high và speculative
            # Thêm weight cho high certainty khi câu có "definitely"
            base_certainty = 0.5
            
            # Điều chỉnh dựa trên similarity differences
            high_weight = 1.5  # Tăng weight cho high certainty
            spec_weight = 1.0
            medium_weight = 0.8
            
            # Tính weighted score
            weighted_high = high_sim * high_weight
            weighted_spec = speculative_sim * spec_weight
            weighted_medium = medium_sim * medium_weight
            
            total_weighted = weighted_high + weighted_spec + weighted_medium
            
            if total_weighted > 0:
                # Nếu high similarity cao hơn nhiều so với speculative -> certainty cao
                if high_sim > speculative_sim * 1.5:  # Ngưỡng 1.5x
                    certainty_score = 0.7 + (high_sim - speculative_sim) * 0.3
                elif speculative_sim > high_sim * 1.5:
                    certainty_score = 0.3 - (speculative_sim - high_sim) * 0.2
                else:
                    # Trường hợp cân bằng
                    certainty_score = 0.4 + (high_sim - speculative_sim) * 0.2
            
            # Điều chỉnh thêm nếu câu chứa các từ đặc biệt (KHÔNG hard-code, dùng embedding)
            # Tạo embedding cho từ "definitely" và so sánh
            definitely_embedding = self.model.encode(["definitely"], normalize_embeddings=True)
            definitely_similarity = cosine_similarity(sentence_embedding, definitely_embedding)[0][0]
            
            if definitely_similarity > 0.7:  # Nếu câu rất giống với "definitely"
                certainty_score = min(0.9, certainty_score + 0.2)
        
        # Giới hạn trong [0.1, 0.9]
        return max(0.1, min(0.9, certainty_score))
    
    def _analyze_sentence_complexity(self, sentence: str) -> float:
        """Phân tích độ phức tạp của câu (0-1)"""
        words = sentence.split()
        word_count = len(words)
        
        # Đếm clauses
        clauses = sentence.count(',') + sentence.count(';') + sentence.count(':') + 1
        
        # Tính complexity
        complexity = (
            min(word_count / 25.0, 1.0) * 0.4 +
            min(clauses / 4.0, 1.0) * 0.3 +
            min(len([w for w in words if len(w) > 6]) / max(len(words), 1), 1.0) * 0.3
        )
        
        return max(0.1, min(0.9, complexity))
    
    def _intelligent_combination(self, results: Dict, sentences: List[str]) -> float:
        """
        Kết hợp thông minh các phương pháp dựa trên context
        """
        n_sentences = len(sentences)
        
        if n_sentences == 1:
            # Với câu đơn: ưu tiên certainty analysis
            weights = {
                'theoretical': 0.3,
                'similarity': 0.2,
                'certainty': 0.5
            }
        elif n_sentences < 5:
            # Với vài câu: cân bằng
            weights = {
                'theoretical': 0.4,
                'similarity': 0.3,
                'certainty': 0.3
            }
        else:
            # Với nhiều câu: ưu tiên theoretical và similarity
            weights = {
                'theoretical': 0.5,
                'similarity': 0.4,
                'certainty': 0.1
            }
        
        # Tính weighted average
        combined = 0.0
        for method, weight in weights.items():
            combined += results[method]['entropy'] * weight
        
        return combined
    
    def _create_universal_references(self) -> Dict:
        """Tạo universal reference sentences với 3 levels"""
        return {
            'high_certainty': [
                "This is absolutely certain.",
                "It will definitely happen.",
                "There is no doubt about this.",
                "This has been confirmed.",
                "The results are conclusive.",
                "This is a proven fact.",
                "It is guaranteed to occur.",
                "This is beyond question.",
                "This has been verified.",
                "This is established knowledge.",
                "It will certainly occur.",
                "Undoubtedly, this will happen.",
                "This is sure to happen.",
                "It is indisputable.",
                "This is unquestionable.",
                "Without a doubt, this is true.",
                "This is confirmed by evidence.",
                "The data conclusively shows.",
                "This is an undeniable fact.",
                "It is 100% certain."
            ],
            'medium_certainty': [
                "This is likely to happen.",
                "It will probably occur.",
                "There is a good chance.",
                "This seems probable.",
                "The evidence suggests this.",
                "This appears to be the case.",
                "It is expected to happen.",
                "This is quite possible.",
                "This is a reasonable assumption.",
                "This seems to be true.",
                "It is plausible.",
                "The odds are in favor.",
                "This is anticipated.",
                "It is projected to happen.",
                "This is foreseeable.",
                "It is very likely.",
                "There is a high probability.",
                "This will most likely happen.",
                "The chances are good.",
                "It is reasonably certain."
            ],
            'speculative': [
                "This might happen.",
                "It could possibly occur.",
                "Perhaps this will happen.",
                "There is a chance that.",
                "This is uncertain.",
                "It's hard to predict.",
                "This is not clear.",
                "The outcome is ambiguous.",
                "This is speculative.",
                "We cannot be sure.",
                "It is unclear.",
                "The future is uncertain.",
                "This is unpredictable.",
                "It is not certain.",
                "This is doubtful.",
                "Maybe this will occur.",
                "It's possible but not sure.",
                "The result is unknown.",
                "There's some uncertainty.",
                "It could go either way."
            ]
        }
    
    def _split_sentences(self, text: str) -> List[str]:
        """Tách câu"""
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(?!\s)(.*?)\*', r'\1', text)
        text = re.sub(r'\[.*?\]\(.*?\)', '', text)
        
        sentences = nltk.sent_tokenize(text)
        cleaned = [s.strip() for s in sentences if len(s.strip()) > 3]
        
        return cleaned
    
    def _generate_hybrid_explanation(self, results: Dict, final_entropy: float, 
                                   num_sentences: int) -> str:
        """Tạo giải thích hybrid"""
        theoretical = results['theoretical']['entropy']
        similarity = results['similarity']['entropy']
        certainty = results['certainty']['entropy']
        
        explanation = (
            f"Hybrid analysis of {num_sentences} sentence(s). "
            f"Theoretical entropy: {theoretical:.3f}, "
            f"Semantic similarity entropy: {similarity:.3f}, "
            f"Certainty-based entropy: {certainty:.3f}. "
            f"Final combined entropy: {final_entropy:.3f}. "
        )
        
        if final_entropy < 0.3:
            explanation += "The text shows low semantic entropy, indicating high certainty and coherence."
        elif final_entropy < 0.6:
            explanation += "The text shows moderate semantic entropy, with a mix of certain and uncertain elements."
        else:
            explanation += "The text shows high semantic entropy, indicating significant uncertainty or topic diversity."
        
        return explanation
    
    def _empty_result(self):
        return {
            'semantic_entropy': 0.0,
            'normalized_entropy': 0.0,
            'num_sentences': 0,
            'explanation': 'No text content to analyze.',
            'analysis_method': 'hybrid'
        }


class AdaptiveEntropyCalculator(HybridSemanticEntropyCalculator):
    """
    Phiên bản adaptive: tự động điều chỉnh weights dựa trên nội dung
    """
    
    def calculate_adaptive_entropy(self, text: str) -> Dict:
        """
        Tính entropy với adaptive weighting
        """
        sentences = self._split_sentences(text)
        
        if len(sentences) == 0:
            return self._empty_result()
        
        # Phân tích đặc điểm văn bản
        text_features = self._analyze_text_features(text, sentences)
        
        # Tính các phương pháp
        results = {
            'theoretical': self._calculate_theoretical_entropy(sentences),
            'similarity': self._calculate_similarity_entropy(sentences),
            'certainty': self._calculate_certainty_entropy(sentences)
        }
        
        # Adaptive weighting dựa trên text features
        weights = self._calculate_adaptive_weights(text_features, results)
        
        # Tính entropy cuối cùng
        final_entropy = 0.0
        for method, weight in weights.items():
            final_entropy += results[method]['entropy'] * weight
        
        # Post-processing: điều chỉnh dựa trên heuristic
        final_entropy = self._post_process_entropy(final_entropy, text_features)
        
        return {
            'semantic_entropy': float(final_entropy),
            'normalized_entropy': float(final_entropy),
            'num_sentences': len(sentences),
            'method_breakdown': results,
            'adaptive_weights': weights,
            'text_features': text_features,
            'explanation': self._generate_adaptive_explanation(
                results, weights, final_entropy, len(sentences), text_features
            ),
            'analysis_method': 'adaptive_hybrid'
        }
    
    def _analyze_text_features(self, text: str, sentences: List[str]) -> Dict:
        """
        Phân tích đặc điểm văn bản để điều chỉnh weights
        """
        # 1. Numerical density
        numbers = re.findall(r'\d+[\d,.]*\s*(?:VND|USD|tons|kg|%|vnd|usd)', text, re.IGNORECASE)
        numerical_density = len(numbers) / max(len(sentences), 1)
        
        # 2. Temporal references
        temporal_terms = ['today', 'tomorrow', 'yesterday', 'week', 'month', 'year', 
                         'hour', 'minute', 'second', 'ago', 'later']
        temporal_count = sum(1 for term in temporal_terms if term in text.lower())
        temporal_density = temporal_count / max(len(sentences), 1)
        
        # 3. Speculative language detection (sử dụng embedding)
        speculative_score = self._detect_speculative_language(text)
        
        # 4. Sentence length variation
        sent_lengths = [len(s.split()) for s in sentences]
        if sent_lengths:
            length_variation = np.std(sent_lengths) / np.mean(sent_lengths)
        else:
            length_variation = 0
        
        return {
            'numerical_density': min(1.0, numerical_density),
            'temporal_density': min(1.0, temporal_density),
            'speculative_score': speculative_score,
            'length_variation': length_variation,
            'is_market_report': numerical_density > 0.5 and temporal_density > 0.3,
            'is_news_article': temporal_density > 0.2 and len(sentences) > 3,
            'is_speculative': speculative_score > 0.6
        }
    
    def _detect_speculative_language(self, text: str) -> float:
        """
        Phát hiện ngôn ngữ suy đoán bằng embedding
        """
        text_embedding = self.model.encode([text], normalize_embeddings=True)
        
        # Reference embeddings cho speculative text
        speculative_refs = [
            "This is uncertain and speculative.",
            "We cannot predict with certainty.",
            "The outcome is unclear and ambiguous.",
            "This involves significant uncertainty.",
            "The future is unpredictable."
        ]
        
        factual_refs = [
            "This is based on factual data.",
            "The numbers confirm this conclusion.",
            "This has been statistically verified.",
            "The evidence is clear and definitive.",
            "This is an established fact."
        ]
        
        # Tính similarity
        speculative_embeddings = self.model.encode(speculative_refs, normalize_embeddings=True)
        factual_embeddings = self.model.encode(factual_refs, normalize_embeddings=True)
        
        spec_similarities = cosine_similarity(text_embedding, speculative_embeddings)[0]
        fact_similarities = cosine_similarity(text_embedding, factual_embeddings)[0]
        
        avg_spec = np.mean(spec_similarities)
        avg_fact = np.mean(fact_similarities)
        
        # Tính speculative score
        if avg_spec + avg_fact > 0:
            speculative_score = avg_spec / (avg_spec + avg_fact)
        else:
            speculative_score = 0.5
        
        return float(speculative_score)
    
    def _calculate_adaptive_weights(self, features: Dict, results: Dict) -> Dict[str, float]:
        """
        Tính adaptive weights dựa trên đặc điểm văn bản
        """
        base_weights = {'theoretical': 0.33, 'similarity': 0.33, 'certainty': 0.33}
    
        # Điều chỉnh dựa trên features
        if features.get('is_market_report', False):
            # Market reports: ưu tiên certainty (vì có số liệu cụ thể)
            base_weights['certainty'] += 0.25
            base_weights['theoretical'] -= 0.15
            base_weights['similarity'] -= 0.10
        
        if features.get('is_speculative', False):
            # Speculative text: ưu tiên certainty và similarity
            base_weights['certainty'] += 0.20
            base_weights['similarity'] += 0.15
            base_weights['theoretical'] -= 0.35
        
        # QUAN TRỌNG: Single sentence luôn ưu tiên certainty
        if features.get('num_sentences', 0) == 1:
            base_weights['certainty'] = 0.70  # 70% weight cho certainty
            base_weights['theoretical'] = 0.15
            base_weights['similarity'] = 0.15
        
        # Đảm bảo weights dương
        for key in base_weights:
            base_weights[key] = max(0.05, base_weights[key])
        
        # Normalize weights
        total = sum(base_weights.values())
        normalized = {k: v/total for k, v in base_weights.items()}
        
        return normalized
    
    def _post_process_entropy(self, entropy: float, features: Dict) -> float:
        """
        Post-processing: điều chỉnh entropy dựa trên heuristic
        """
        # Market reports với số liệu cụ thể → giảm entropy
        if features['is_market_report'] and features['numerical_density'] > 0.3:
            entropy *= 0.8
        
        # Văn bản speculative → tăng entropy
        if features['is_speculative']:
            entropy = min(1.0, entropy * 1.2)
        
        # Văn bản với temporal references cụ thể → giảm entropy
        if features['temporal_density'] > 0.4:
            entropy *= 0.9
        
        return max(0.0, min(1.0, entropy))
    
    def _generate_adaptive_explanation(self, results: Dict, weights: Dict, 
                                     entropy: float, num_sentences: int, 
                                     features: Dict) -> str:
        """Tạo giải thích adaptive"""
        explanation = (
            f"Adaptive analysis of {num_sentences} sentence(s). "
            f"Weights: Theoretical ({weights['theoretical']:.2f}), "
            f"Similarity ({weights['similarity']:.2f}), "
            f"Certainty ({weights['certainty']:.2f}). "
            f"Final entropy: {entropy:.3f}. "
        )
        
        # Thêm đặc điểm văn bản
        if features['is_market_report']:
            explanation += "Text appears to be a market report with numerical data. "
        elif features['is_news_article']:
            explanation += "Text appears to be a news article. "
        
        if features['is_speculative']:
            explanation += "Text contains speculative language. "
        
        # Kết luận
        if entropy < 0.3:
            explanation += "Overall, the text shows low semantic entropy (high certainty)."
        elif entropy < 0.6:
            explanation += "Overall, the text shows moderate semantic entropy."
        else:
            explanation += "Overall, the text shows high semantic entropy (significant uncertainty)."
        
        return explanation