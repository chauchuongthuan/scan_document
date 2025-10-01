from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from django.utils.text import slugify
from django.urls import reverse
from uuid import uuid4
class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    comco_ref = models.CharField(max_length=255)
    buyer_ref = models.CharField(max_length=255)
    contract_date = models.DateField()
    price = models.CharField(max_length=255)
    dds_and_geo = models.CharField(max_length=255, null=True, blank=True)
    docs = models.CharField(max_length=255, null=True, blank=True)
    shippers = models.CharField(max_length=255)
    buyers = models.CharField(max_length=255)
    shipment_period = models.CharField(max_length=255, null=True, blank=True)
    quality = models.CharField(max_length=255)
    quantity = models.CharField(max_length=255)
    conts_no = models.CharField(max_length=255)
    packing = models.CharField(max_length=255)
    sample = models.CharField(max_length=255, null=True, blank=True)
    result = models.CharField(max_length=255, null=True, blank=True)
    stuffing_date = models.DateField(null=True, blank=True)
    carriers = models.CharField(max_length=255)
    booking_no = models.CharField(max_length=255)
    etd = models.DateField(null=True, blank=True)
    eta = models.CharField(max_length=255, null=True, blank=True)
    destination = models.CharField(max_length=255)
    inspectors = models.CharField(max_length=255, null=True, blank=True)
    warehouse = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=255, null=True, blank=True)
    weight_claim = models.CharField(max_length=255, null=True, blank=True)
    remark = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta: 
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return self.id