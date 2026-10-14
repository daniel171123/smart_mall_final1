from django.db import models
from django.conf import settings


class MaintenanceRequest(models.Model):

    class Priority(models.TextChoices):
        LOW    = 'LOW',    'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH   = 'HIGH',   'High'
        URGENT = 'URGENT', 'Urgent'

    class Status(models.TextChoices):
        SUBMITTED   = 'SUBMITTED',   'Submitted'
        ASSIGNED    = 'ASSIGNED',    'Assigned'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED   = 'COMPLETED',   'Completed'
        CANCELLED   = 'CANCELLED',   'Cancelled'

    shop         = models.ForeignKey(
                       'malls.Shop',
                       on_delete=models.CASCADE,
                       related_name='maintenance_requests'
                   )
    requested_by = models.ForeignKey(
                       settings.AUTH_USER_MODEL,
                       on_delete=models.SET_NULL,
                       null=True,
                       related_name='maintenance_requests'
                   )
    title        = models.CharField(max_length=200)
    description  = models.TextField()
    priority     = models.CharField(
                       max_length=10,
                       choices=Priority.choices,
                       default=Priority.MEDIUM
                   )
    status       = models.CharField(
                       max_length=15,
                       choices=Status.choices,
                       default=Status.SUBMITTED
                   )
    # WHY: SET_NULL — request stays even if assigned
    # staff member leaves the system
    assigned_to  = models.ForeignKey(
                       settings.AUTH_USER_MODEL,
                       on_delete=models.SET_NULL,
                       null=True,
                       blank=True,
                       related_name='assigned_maintenance'
                   )
    created_at   = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering     = ['-created_at']
        verbose_name = 'Maintenance Request'
        verbose_name_plural = 'Maintenance Requests'

    def __str__(self):
        return (
            f'{self.title} — '
            f'Shop {self.shop.shop_number} '
            f'({self.status})'
        )