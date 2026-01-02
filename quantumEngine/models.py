from django.db import models

class QuantumEngine(models.Model):
    date = models.DateField(unique=True, help_text="Ngày dữ liệu", primary_key=True)
    # --- Dữ liệu nhập tay hằng ngày ---
    manual_farm_gate_price = models.FloatField(help_text="Giá tại vườn (VND/kg)", default=0)
    manual_midstream_price = models.FloatField(help_text="Giá đại lý/kho (VND/kg)", default=0, null=True, blank=True)
    news_content = models.TextField(blank=True, help_text="Đoạn văn tổng hợp thị trường")
       
    rc_open = models.FloatField(null=True, blank=True)
    rc_high = models.FloatField(null=True, blank=True)
    rc_low = models.FloatField(null=True, blank=True)
    rc_close = models.FloatField(null=True, blank=True)
    rc_inventory = models.FloatField(null=True, blank=True, help_text="LOTS WITH VAL CERT")
    
    # --- Arabica Data (KC) ---
    kc_open = models.FloatField(null=True, blank=True)
    kc_high = models.FloatField(null=True, blank=True)
    kc_low = models.FloatField(null=True, blank=True)
    kc_close = models.FloatField(null=True, blank=True)
    kc_inventory = models.FloatField(null=True, blank=True, help_text="Bags")

    # --- Kết quả tính toán Lượng tử (Output) ---
    sentiment_score = models.FloatField(null=True, blank=True) 
    market_trend_z = models.FloatField(null=True, blank=True)    
    volatility_y = models.FloatField(null=True, blank=True)      
    
    purity = models.FloatField(null=True, blank=True)          
    bullish_prob = models.FloatField(null=True, blank=True)    

    class Meta:
        ordering = ['-date']
        verbose_name = "QuantumEngine"
        verbose_name_plural = 'QuantumEngine'
        db_table = 'quantum_engine'

    def __str__(self):
        return f"{self.date} - Farm: {self.manual_farm_gate_price}"