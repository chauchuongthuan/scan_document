import sys
import torch
import numpy as np
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch.nn.functional as F
from nltk.tokenize import sent_tokenize # Thư viện chia câu

class AdvancedMarketAnalyzer:
    def __init__(self):
        print("Loading FinBERT (Sentiment) and Zero-Shot (Topic) models... (Heavy Load)")
        try:
            # 1. Mô hình Phân tích Cảm xúc (Sentiment)
            finbert_name = "ProsusAI/finbert"
            self.finbert_tokenizer = AutoTokenizer.from_pretrained(finbert_name)
            self.finbert_model = AutoModelForSequenceClassification.from_pretrained(finbert_name)
            
            # 2. Mô hình Phân loại Ngữ cảnh (Zero-Shot Classification) - Loại bỏ Keywords
            # Mô hình này giúp phân loại nội dung mà không cần huấn luyện
            self.zero_shot_classifier = pipeline("zero-shot-classification", 
                                                 model="facebook/bart-large-mnli",
                                                 device=0 if torch.cuda.is_available() else -1)

            self.device = 0 if torch.cuda.is_available() else -1
            print("All models loaded successfully.")
        except Exception as e:
            print(f"Error loading models: {e}")
            sys.exit(1)

    def _split_into_contextual_chunks(self, text, max_len=510):
        """
        Chia văn bản thành các đoạn (chunks) theo TỪNG CÂU, 
        đảm bảo mỗi đoạn không vượt quá giới hạn 512 tokens.
        """
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = []
        current_chunk_tokens = 0

        for sentence in sentences:
            # Tokenize câu và kiểm tra độ dài
            sentence_tokens = self.finbert_tokenizer.encode(sentence, add_special_tokens=False)
            token_count = len(sentence_tokens)

            if current_chunk_tokens + token_count < max_len:
                # Nếu câu vừa đủ chỗ, thêm vào chunk hiện tại
                current_chunk.append(sentence)
                current_chunk_tokens += token_count
            else:
                # Nếu không đủ chỗ, kết thúc chunk hiện tại và bắt đầu chunk mới
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_chunk_tokens = token_count
        
        # Thêm chunk cuối cùng
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks

    def _get_context_topic(self, text):
        """
        Sử dụng Zero-Shot Classification để tự động nhận định ngữ cảnh (Supply/Demand/Price)
        mà không cần dùng từ khóa cố định.
        """
        candidate_labels = ['Coffee Supply', 'Coffee Demand', 'Price Action', 'General Market News', 'Political / Regulatory']
        
        # Truncate văn bản đầu vào cho Zero-Shot (thường cũng có giới hạn)
        truncated_text = text[:1500] 
        
        results = self.zero_shot_classifier(truncated_text, candidate_labels, multi_label=False)
        
        # Lấy nhãn có điểm số cao nhất
        best_topic = results['labels'][0]
        confidence = results['scores'][0]
        
        return best_topic, confidence

    def _get_sentiment_score(self, chunk):
        """
        Lấy điểm số cảm xúc (Positive, Negative, Neutral) từ FinBERT cho 1 đoạn văn bản
        """
        with torch.no_grad():
            input_ids = self.finbert_tokenizer.encode(chunk, return_tensors='pt', truncation=True)
            if self.device == 0:
                input_ids = input_ids.to('cuda')
            
            outputs = self.finbert_model(input_ids)
            probs = F.softmax(outputs.logits, dim=1).cpu().detach().numpy()[0]
            
            # FinBERT output order: [Positive, Negative, Neutral]
            return probs # Trả về vector [P, N, Neu]

    def analyze_market_report(self, text, farm_gate_price=None, midstream_price=None, differential=None):
        """
        Hàm phân tích chính, tích hợp cả dữ liệu định tính (text) và định lượng (price).
        """
        # 1. Phân tích ngữ cảnh (Topic)
        overall_topic, topic_confidence = self._get_context_topic(text)
        
        # 2. Phân tích Cảm xúc (Sentiment) - Chia nhỏ theo câu
        chunks = self._split_into_contextual_chunks(text)
        
        if not chunks:
            return {"error": "Không có văn bản hợp lệ để phân tích."}
            
        sentiment_vectors = [self._get_sentiment_score(chunk) for chunk in chunks]
        
        # Tính điểm số trung bình (Aggregation)
        avg_scores = np.mean(sentiment_vectors, axis=0)
        labels = ['positive', 'negative', 'neutral']
        max_idx = np.argmax(avg_scores)
        final_sentiment = labels[max_idx]
        final_confidence = avg_scores[max_idx]

        # 3. Áp dụng Logic Hàng Hóa Dựa trên Zero-Shot Topic
        market_prediction = ""
        
        # Logic dựa trên ngành Hàng hóa (Commodity Logic)
        if overall_topic == 'Coffee Supply':
            if final_sentiment == 'negative':
                # Tin xấu về Nguồn cung (hạn hán, dịch bệnh) => Giá TĂNG (Bullish)
                market_prediction = "BULLISH (GIÁ TĂNG do CUNG GIẢM)"
            elif final_sentiment == 'positive':
                # Tin tốt về Nguồn cung (được mùa, sản lượng kỷ lục) => Giá GIẢM (Bearish)
                market_prediction = "BEARISH (GIÁ GIẢM do CUNG TĂNG)"
            else:
                market_prediction = "NEUTRAL / PHỤ THUỘC YẾU TỐ KHÁC"
        
        elif overall_topic == 'Coffee Demand':
            if final_sentiment == 'negative':
                # Tin xấu về Nhu cầu (người tiêu dùng cắt giảm) => Giá GIẢM (Bearish)
                market_prediction = "BEARISH (GIÁ GIẢM do CẦU GIẢM)"
            elif final_sentiment == 'positive':
                # Tin tốt về Nhu cầu (doanh số tăng, kinh tế phục hồi) => Giá TĂNG (Bullish)
                market_prediction = "BULLISH (GIÁ TĂNG do CẦU TĂNG)"
            else:
                market_prediction = "NEUTRAL / PHỤ THUỘC YẾU TỐ KHÁC"
        
        else: # Price Action, General News, Political
            # Theo sát cảm xúc chung của FinBERT
            market_prediction = f"CHỦ YẾU LÀ {final_sentiment.upper()} (Giá có thể thay đổi theo hướng này)"

        # 4. Tổng hợp Báo cáo
        price_summary = {
            "FarmGate": farm_gate_price,
            "Midstream": midstream_price,
            "Differential": differential
        }
        
        return {
            "processed_chunks": len(chunks),
            "overall_sentiment": final_sentiment,
            "confidence_score": round(float(final_confidence), 4),
            "dominant_topic": overall_topic,
            "topic_confidence": round(float(topic_confidence), 4),
            "market_prediction": market_prediction,
            "quantitative_data": price_summary
        }

# ==========================================
# KHU VỰC TEST
# ==========================================
if __name__ == "__main__":
    
    # Khởi tạo Analyzer (sẽ tải 2 mô hình)
    analyzer = AdvancedMarketAnalyzer()

    print("\n" + "="*70)
    print("PHÂN TÍCH BÁO CÁO THỊ TRƯỜNG CÀ PHÊ")
    print("="*70 + "\n")

    # Báo cáo mẫu của bạn, chứa nhiều câu và thông tin giá
    long_report_text = """
    Farm-Gate (Upstream): Prices have weakened strongly, now ranging from 108,500 to 110,500 VND/kg. Daily trading volume steadied to lowered between 2,000 to 2,500 tons daily over the weekend due to consistent rain throughout the weekend with today's morning flow ranging slightly higher between 2,600 tons to 2,800. This had prompt for a slightly lower bid in purchasing price from middlemen to farmers, particularly in Lam Dong by 200 to 400 VND/kg. 
    
    Midstream: Prices at middlemen warehouses are quoted steady in the range of 110,000 to 112,000 VND/kg.
    
    Differential: New crop differentials are indicated at +40 (ask) to +70 (bid).
    
    Weather Update: Despite some localized rain, overall drought conditions in key Central American growing regions are a significant concern. The extended dry period has analysts fearing a 10% shortfall in next year's harvest forecast. This potential supply shock is keeping a floor under futures prices.
    """
    
    # THÊM DỮ LIỆU ĐỊNH LƯỢNG THỦ CÔNG VÀO FIELD RIÊNG
    price_data = {
        "farm_gate_price": "108,500 - 110,500 VND/kg (Weakening)",
        "midstream_price": "110,000 - 112,000 VND/kg (Steady)",
        "differential": "+40 to +70 (bid)"
    }

    result = analyzer.analyze_market_report(
        text=long_report_text,
        farm_gate_price=price_data["farm_gate_price"],
        midstream_price=price_data["midstream_price"],
        differential=price_data["differential"]
    )

    print(f"BÁO CÁO PHÂN TÍCH:")
    print("-" * 30)
    print(f"1. Số đoạn được xử lý: {result['processed_chunks']} đoạn (Chia theo câu)")
    print(f"2. Ngữ cảnh (Topic):   {result['dominant_topic']} (Tin cậy: {result['topic_confidence']*100:.2f}%)")
    print(f"3. Cảm xúc (Sentiment): {result['overall_sentiment'].upper()} (Tin cậy: {result['confidence_score']*100:.2f}%)")
    print(f"4. DỰ ĐOÁN THỊ TRƯỜNG:  {result['market_prediction']}")
    print("\n5. DỮ LIỆU ĐỊNH LƯỢNG:")
    print(f"   - Giá Cổng trại (Farm-Gate): {result['quantitative_data']['FarmGate']}")
    print(f"   - Giá Kho trung gian:         {result['quantitative_data']['Midstream']}")
    print(f"   - Differential:              {result['quantitative_data']['Differential']}")
    print("="*70)