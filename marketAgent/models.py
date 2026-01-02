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

class IceData(models.Model):
    date = models.DateField(unique=True, primary_key=True)
    total_in_bag = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta: 
        verbose_name = 'IceData'
        verbose_name_plural = 'IceDatas'
        ordering = ['-created_at']
        db_table = 'ice_data'

    def __str__(self):
        return f"Data for {self.date}"

class IceRCStockData(models.Model):
    date = models.DateField(unique=True, primary_key=True)
    lots_with_val_cert = models.TextField(null=True, blank=True)
    lots_non_tend = models.TextField(null=True, blank=True)
    lots_suspended = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta: 
        verbose_name = 'IceRCStockData'
        verbose_name_plural = 'IceRCStockData'
        ordering = ['-created_at']
        db_table = 'ice_rc_stock_data'

    def __str__(self):
        return f"Data for {self.date}"