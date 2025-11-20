from django.db import models

class DailyMarketPrice(models.Model):
    """
    Lưu trữ giá thị trường được trích xuất hàng ngày để so sánh.
    """
    date = models.DateField(unique=True, primary_key=True)
    farm_gate_low = models.FloatField(null=True, blank=True)
    farm_gate_high = models.FloatField(null=True, blank=True)
    midstream_low = models.FloatField(null=True, blank=True)
    midstream_high = models.FloatField(null=True, blank=True)
    differential_bid = models.FloatField(null=True, blank=True)
    differential_ask = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta: 
        verbose_name = 'MarketPrice'
        verbose_name_plural = 'MarketPrices'
        ordering = ['-created_at']
        db_table = 'market_price'

    def __str__(self):
        return f"Prices for {self.date}"