from django.db import models


class Mall(models.Model):
    """
    WHY: Top-level entity. Everything in the system
    belongs to a mall. Building this now makes the
    system scalable to multiple malls from day one.
    """
    name          = models.CharField(max_length=200)
    location      = models.TextField()
    city          = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField()
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering     = ['name']
        verbose_name = 'Mall'
        verbose_name_plural = 'Malls'

    def __str__(self):
        return f'{self.name} — {self.city}'

    def get_total_shops(self):
        return self.shops.count()

    def get_occupied_shops(self):
        return self.shops.filter(status='OCCUPIED').count()

    def get_vacant_shops(self):
        return self.shops.filter(status='VACANT').count()

    def get_occupancy_rate(self):
        total = self.get_total_shops()
        if total == 0:
            return 0
        return round((self.get_occupied_shops() / total) * 100, 2)


class Shop(models.Model):
    """
    WHY: A shop is the physical unit being rented.
    It must always belong to a mall.
    Status is managed by the system automatically
    when leases are created or terminated.
    """

    class Status(models.TextChoices):
        VACANT           = 'VACANT',           'Vacant'
        OCCUPIED         = 'OCCUPIED',          'Occupied'
        UNDER_MAINTENANCE = 'UNDER_MAINTENANCE', 'Under Maintenance'

    mall        = models.ForeignKey(
                      Mall,
                      on_delete=models.PROTECT,
                      # WHY PROTECT: Prevent deleting a mall
                      # that still has shops inside it
                      related_name='shops'
                  )
    shop_number = models.CharField(max_length=20)
    floor       = models.CharField(max_length=50)
    size_sqm    = models.DecimalField(max_digits=8, decimal_places=2)
    shop_type   = models.CharField(max_length=100)
    status      = models.CharField(
                      max_length=20,
                      choices=Status.choices,
                      default=Status.VACANT
                  )
    description = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        # WHY: Prevents two shops with same number in the same mall
        unique_together = ('mall', 'shop_number')
        ordering        = ['mall', 'floor', 'shop_number']
        verbose_name    = 'Shop'
        verbose_name_plural = 'Shops'

    def __str__(self):
        return f'Shop {self.shop_number} — {self.mall.name} ({self.floor} Floor)'

    def get_active_lease(self):
        # WHY: Helper used everywhere to get current tenant
        return self.leases.filter(status='ACTIVE').first()