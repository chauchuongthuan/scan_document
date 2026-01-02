import nltk
import math
from collections import Counter
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet

# Tải dữ liệu cần thiết (chỉ cần chạy lần đầu)
nltk.download('punkt')
nltk.download('wordnet')

def get_synset_key(word):
    """
    Lấy khóa nhóm đồng nghĩa (synset) cho một từ.
    Trả về tên synset đầu tiên trong WordNet, hoặc chính từ đó nếu không tìm thấy.
    """
    synsets = wordnet.synsets(word)
    return synsets[0].name() if synsets else word

def calculate_semantic_entropy(text):
    """
    Tính semantic entropy của một văn bản tiếng Anh.
    """
    # 1. Token hóa và chuẩn hóa (chỉ lấy từ chữ cái, viết thường)
    tokens = word_tokenize(text)
    words = [word.lower() for word in tokens if word.isalpha()]
    
    if not words:
        return 0.0
    
    # 2. Tính xác suất của mỗi từ
    word_counts = Counter(words)
    total_words = len(words)
    word_probs = {word: count / total_words for word, count in word_counts.items()}
    
    # 3. Nhóm các từ vào tập đồng nghĩa (synset)
    synset_probs = {}
    for word, prob in word_probs.items():
        synset_key = get_synset_key(word)
        synset_probs[synset_key] = synset_probs.get(synset_key, 0.0) + prob
    
    # 4. Tính semantic entropy
    entropy = 0.0
    for prob in synset_probs.values():
        if prob > 0:
            entropy -= prob * math.log2(prob)
    
    return entropy

# Ví dụ sử dụng
if __name__ == "__main__":
    text = """
    Tomorrow it will definitely rain.
    """
    entropy = calculate_semantic_entropy(text)
    print(f"Semantic Entropy: {entropy:.4f} sebits")