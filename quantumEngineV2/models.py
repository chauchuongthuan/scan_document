# models.py
from django.db import models

class CoffeeQuantumModel(models.Model):
    date = models.DateField(primary_key=True, help_text="Ngày dự báo (Ngày T)")
    
    farm_gate_price = models.FloatField(default=0, help_text="Giá vườn sáng nay")
    midstream_price = models.FloatField(default=0, help_text="Giá kho sáng nay")
    trade_volume = models.FloatField(default=0, help_text="Khối lượng (Tấn)")
    diff_value = models.FloatField(default=0, help_text="Trừ lùi (VD: -120)")
    weather_score = models.FloatField(default=0.5, help_text="0: Tốt, 1: Xấu")
    
    rc_bullish_prob = models.FloatField(null=True, blank=True)
    kc_bullish_prob = models.FloatField(null=True, blank=True)
    text_sentiment = models.CharField(max_length=50, null=True, blank=True)
    quantum_purity = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['-date']
        verbose_name = "CoffeeQuantumModel"
        verbose_name_plural = 'CoffeeQuantumModel'
        db_table = 'coffee_quantum_model'