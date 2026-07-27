from django.db import models

class KeywordGroup(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    log_tag = models.CharField(max_length=100)
    keywords = models.TextField(default="", help_text="Lưu dạng chuỗi cách nhau bằng dấu phẩy")

    def get_keyword_list(self):
        if not self.keywords: return []
        return [k.strip() for k in self.keywords.split(',') if k.strip()]

    def set_keyword_list(self, k_list):
        self.keywords = ",".join(dict.fromkeys(k_list))
        self.save()
    class Meta:
        db_table = 'keyword_group'
    def __str__(self):
        return self.name

class ScanRule(models.Model):
    LOGIC_CHOICES = [
        ('AND', 'Bắt buộc thỏa mãn TẤT CẢ các nhóm (AND)'),
        ('OR', 'Chỉ cần thỏa mãn MỘT trong các nhóm (OR)'),
    ]
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, verbose_name="Tên quy tắc quét")
    log_tag = models.CharField(max_length=100, verbose_name="Nhãn hiển thị khi log", default="TIN TỔNG HỢP")
    keyword_groups = models.ManyToManyField(KeywordGroup, related_name="rules")
    logic_type = models.CharField(max_length=3, choices=LOGIC_CHOICES, default='OR')
    is_active = models.BooleanField(default=True)
    class Meta:
        db_table = 'scan_rule'
    
    def __str__(self):
        return self.name

class DailyNewsFromVietNamSign(models.Model):
    date = models.DateField(unique=True, primary_key=True)
    sign_summary = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta: 
        verbose_name = 'NewsSign'
        verbose_name_plural = 'NewsSigns'
        ordering = ['-created_at']
        db_table = 'news_sign'

    def __str__(self):
        return f"Signs for {self.date}"