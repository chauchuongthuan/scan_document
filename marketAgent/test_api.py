import math
from collections import Counter

# 1️⃣ Hàm tính xác suất P(ϕ)
def probability(event_count, total_count):
    return event_count / total_count if total_count > 0 else 0

# 2️⃣ Hàm tính surprisal S(w_t) = -log P(v_t | v_{t-1})
def surprisal(prob):
    if prob <= 0:
        return float('inf')
    return -math.log(prob, 2)  # log cơ số 2 cho đơn vị bit

# 3️⃣ Hàm tính entropy H(t)
def entropy(probabilities):
    return -sum(p * math.log(p, 2) for p in probabilities if p > 0)

# 4️⃣ Hàm tính entropy reduction ΔH(w_t) = H(t-1) - H(t)
def entropy_reduction(H_prev, H_current):
    return H_prev - H_current

# 5️⃣ Hàm phân tích văn bản theo từ và tính surprisal + entropy
def analyze_text_entropy(text_tokens):
    """
    text_tokens: list các từ trong văn bản
    """
    # Tần suất xuất hiện từ
    counts = Counter(text_tokens)
    total = sum(counts.values())
    
    # Xác suất mỗi từ
    probs = {word: probability(count, total) for word, count in counts.items()}
    
    # Entropy toàn văn bản
    H_total = entropy(list(probs.values()))
    
    # Surprisal từng từ
    surprisal_values = {word: surprisal(p) for word, p in probs.items()}
    
    return {
        "entropy_total": H_total,
        "surprisal_values": surprisal_values,
        "probabilities": probs
    }

# 6️⃣ Ví dụ sử dụng
if __name__ == "__main__":
    text = """
    Tomorrow it will rain.
    """
    tokens = text.lower().split()
    
    result = analyze_text_entropy(tokens)
    
    print("Entropy tổng thể:", result["entropy_total"])
    print("Surprisal từng từ:")
    for word, s in result["surprisal_values"].items():
        print(f"  {word}: {s:.3f}")
