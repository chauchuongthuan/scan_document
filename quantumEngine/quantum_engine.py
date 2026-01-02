import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

class QuantumPredictor:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        self.sigma_x = np.array([[0, 1], [1, 0]])
        self.sigma_y = np.array([[0, -1j], [1j, 0]])
        self.sigma_z = np.array([[1, 0], [0, -1]])
        self.I = np.eye(2)

    def analyze_sentiment(self, text):
        """Phân tích cảm xúc văn bản tin tức (-1 đến 1)"""
        if not text: return 0
        scores = self.analyzer.polarity_scores(text)
        return scores['compound']

    def calculate_quantum_state(self, sentiment, trend_z, volatility):
        """
        Tính toán Ma trận mật độ & Các chỉ số lượng tử
        - sentiment: Trục X
        - trend_z: Trục Z (Tính từ chênh lệch giá bạn nhập vs giá hôm qua)
        - volatility: Trục Y (Nhiễu)
        """
        # 1. Chuẩn hóa vào khối cầu Bloch
        z = np.clip(trend_z, -1, 1)
        x = np.clip(sentiment, -1, 1)
        
        # Volatility càng cao, trạng thái càng bị đẩy vào trong (mất tin cậy)
        y = np.clip(volatility * 5, 0, 0.5)
        
        # Decoherence (Mất liên kết lượng tử do nhiễu)
        decoherence = np.exp(-volatility * 5)
        x *= decoherence
        z *= decoherence

        # Đảm bảo bán kính r <= 1
        r = np.sqrt(x**2 + y**2 + z**2)
        if r > 1: x, y, z = x/r, y/r, z/r

        # 2. Tạo Density Matrix
        rho = 0.5 * (self.I + x*self.sigma_x + y*self.sigma_y + z*self.sigma_z)
        
        # 3. Tính Purity (Độ tinh khiết)
        purity = np.real(np.trace(np.linalg.matrix_power(rho, 2)))
        
        # 4. Tính Bullish Probability (Xác suất tăng)
        eigenvalues = np.linalg.eigvals(rho)
        bullish_prob = np.max(np.real(eigenvalues))
        
        # Điều chỉnh hướng xác suất dựa trên Z
        if z < 0:
            bullish_prob = 1.0 - bullish_prob

        return {
            'purity': round(purity, 4),
            'bullish_prob': round(bullish_prob, 4),
            'sentiment': round(x, 4),
            'trend_z': round(z, 4)
        }