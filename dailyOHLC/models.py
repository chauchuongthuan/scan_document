from django.db import models
class OHLCDataRCDaily(models.Model):
    timestamp = models.DateTimeField(primary_key=True)
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    
    volatility_open = models.FloatField(null=True, blank=True)
    volatility_close = models.FloatField(null=True, blank=True)
    volatility_high = models.FloatField(null=True, blank=True)
    volatility_low = models.FloatField(null=True, blank=True)

    stdev_vol_open_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_high_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_low_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_close_20_days = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'OHLCDataRCDaily'
        verbose_name_plural = 'OHLCDataRCDaily'
        db_table = 'ohlc_data_rc_daily'

class OHLCDataKCDaily(models.Model):
    timestamp = models.DateTimeField(primary_key=True)
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    
    volatility_open = models.FloatField(null=True, blank=True)
    volatility_close = models.FloatField(null=True, blank=True)
    volatility_high = models.FloatField(null=True, blank=True)
    volatility_low = models.FloatField(null=True, blank=True)

    stdev_vol_open_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_high_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_low_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_close_20_days = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'OHLCDataKCDaily'
        verbose_name_plural = 'OHLCDataKCDaily'
        db_table = 'ohlc_data_kc_daily'

class OHLCDataKCKDaily(models.Model):
    timestamp = models.DateTimeField(primary_key=True)
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    
    volatility_open = models.FloatField(null=True, blank=True)
    volatility_close = models.FloatField(null=True, blank=True)
    volatility_high = models.FloatField(null=True, blank=True)
    volatility_low = models.FloatField(null=True, blank=True)

    stdev_vol_open_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_high_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_low_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_close_20_days = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'OHLCDataKCKDaily'
        verbose_name_plural = 'OHLCDataKCKDaily'
        db_table = 'ohlc_data_kck_daily'

class OHLCDataRCKDaily(models.Model):
    timestamp = models.DateTimeField(primary_key=True)
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    
    volatility_open = models.FloatField(null=True, blank=True)
    volatility_close = models.FloatField(null=True, blank=True)
    volatility_high = models.FloatField(null=True, blank=True)
    volatility_low = models.FloatField(null=True, blank=True)

    stdev_vol_open_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_high_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_low_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_close_20_days = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'OHLCDataRCKDaily'
        verbose_name_plural = 'OHLCDataRCKDaily'
        db_table = 'ohlc_data_rck_daily'

class OHLCDataKCUDaily(models.Model):
    timestamp = models.DateTimeField(primary_key=True)
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    
    volatility_open = models.FloatField(null=True, blank=True)
    volatility_close = models.FloatField(null=True, blank=True)
    volatility_high = models.FloatField(null=True, blank=True)
    volatility_low = models.FloatField(null=True, blank=True)

    stdev_vol_open_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_high_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_low_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_close_20_days = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'OHLCDataKCUDaily'
        verbose_name_plural = 'OHLCDataKCUDaily'
        db_table = 'ohlc_data_kcu_daily'

class OHLCDataRCUDaily(models.Model):
    timestamp = models.DateTimeField(primary_key=True)
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    
    volatility_open = models.FloatField(null=True, blank=True)
    volatility_close = models.FloatField(null=True, blank=True)
    volatility_high = models.FloatField(null=True, blank=True)
    volatility_low = models.FloatField(null=True, blank=True)

    stdev_vol_open_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_high_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_low_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_close_20_days = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'OHLCDataRCUDaily'
        verbose_name_plural = 'OHLCDataRCUDaily'
        db_table = 'ohlc_data_rcu_daily'

class OHLCDataKCNDaily(models.Model):
    timestamp = models.DateTimeField(primary_key=True)
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    
    volatility_open = models.FloatField(null=True, blank=True)
    volatility_close = models.FloatField(null=True, blank=True)
    volatility_high = models.FloatField(null=True, blank=True)
    volatility_low = models.FloatField(null=True, blank=True)

    stdev_vol_open_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_high_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_low_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_close_20_days = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'OHLCDataKCNDaily'
        verbose_name_plural = 'OHLCDataKCNDaily'
        db_table = 'ohlc_data_kcn_daily'

class OHLCDataRCNDaily(models.Model):
    timestamp = models.DateTimeField(primary_key=True)
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    
    volatility_open = models.FloatField(null=True, blank=True)
    volatility_close = models.FloatField(null=True, blank=True)
    volatility_high = models.FloatField(null=True, blank=True)
    volatility_low = models.FloatField(null=True, blank=True)

    stdev_vol_open_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_high_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_low_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_close_20_days = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'OHLCDataRCNDaily'
        verbose_name_plural = 'OHLCDataRCNDaily'
        db_table = 'ohlc_data_rcn_daily'

class OHLCDataKCZDaily(models.Model):
    timestamp = models.DateTimeField(primary_key=True)
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    
    volatility_open = models.FloatField(null=True, blank=True)
    volatility_close = models.FloatField(null=True, blank=True)
    volatility_high = models.FloatField(null=True, blank=True)
    volatility_low = models.FloatField(null=True, blank=True)

    stdev_vol_open_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_high_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_low_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_close_20_days = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'OHLCDataKCZDaily'
        verbose_name_plural = 'OHLCDataKCZDaily'
        db_table = 'ohlc_data_kcz_daily'

class OHLCDataRCXDaily(models.Model):
    timestamp = models.DateTimeField(primary_key=True)
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    
    volatility_open = models.FloatField(null=True, blank=True)
    volatility_close = models.FloatField(null=True, blank=True)
    volatility_high = models.FloatField(null=True, blank=True)
    volatility_low = models.FloatField(null=True, blank=True)

    stdev_vol_open_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_high_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_low_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_close_20_days = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'OHLCDataRCXDaily'
        verbose_name_plural = 'OHLCDataRCXDaily'
        db_table = 'ohlc_data_rcx_daily'

class ImpliedVolatility(models.Model):
    timestamp = models.DateTimeField(primary_key=True)

    # IV data
    # CH
    implied_volatility_rc = models.FloatField(null=True, blank=True)
    implied_volatility_kc = models.FloatField(null=True, blank=True)

    # CK
    implied_volatility_kck = models.FloatField(null=True, blank=True)
    implied_volatility_rck = models.FloatField(null=True, blank=True)

    # CN
    implied_volatility_kcn = models.FloatField(null=True, blank=True)
    implied_volatility_rcn = models.FloatField(null=True, blank=True)

    # CU
    implied_volatility_kcu = models.FloatField(null=True, blank=True)
    implied_volatility_rcu = models.FloatField(null=True, blank=True)

    # KCZ, RCX
    implied_volatility_kcz = models.FloatField(null=True, blank=True)
    implied_volatility_rcx = models.FloatField(null=True, blank=True)

    # Check IV data
    # CH
    realized_volatility_rc_has_passed = models.BooleanField(default=False)
    rv_passed_value_rc = models.FloatField(null=True, blank=True)
    realized_volatility_kc_has_passed = models.BooleanField(default=False)
    rv_passed_value_kc = models.FloatField(null=True, blank=True)
    
    # CK
    realized_volatility_kck_has_passed = models.BooleanField(default=False)
    rv_passed_value_kck = models.FloatField(null=True, blank=True)
    realized_volatility_rck_has_passed = models.BooleanField(default=False)
    rv_passed_value_rck = models.FloatField(null=True, blank=True)
    
    # CN
    realized_volatility_kcn_has_passed = models.BooleanField(default=False)
    rv_passed_value_kcn = models.FloatField(null=True, blank=True)
    realized_volatility_rcn_has_passed = models.BooleanField(default=False)
    rv_passed_value_rcn = models.FloatField(null=True, blank=True)
    
    # CU
    realized_volatility_kcu_has_passed = models.BooleanField(default=False)
    rv_passed_value_kcu = models.FloatField(null=True, blank=True)
    realized_volatility_rcu_has_passed = models.BooleanField(default=False)
    rv_passed_value_rcu = models.FloatField(null=True, blank=True)

    # KCZ, RCX
    realized_volatility_kcz_has_passed = models.BooleanField(default=False)
    rv_passed_value_kcz = models.FloatField(null=True, blank=True)
    realized_volatility_rcx_has_passed = models.BooleanField(default=False)
    rv_passed_value_rcx = models.FloatField(null=True, blank=True)
    class Meta:
        ordering = ['timestamp']
        verbose_name = 'ImpliedVolatility'
        verbose_name_plural = 'ImpliedVolatility'
        db_table = 'implied_volatility'