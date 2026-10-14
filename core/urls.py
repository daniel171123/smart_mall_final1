from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('',
         RedirectView.as_view(url='/accounts/login/'),
         name='root'),
    path('admin/',     admin.site.urls),
    path('accounts/',  include('accounts.urls',
                                namespace='accounts')),
    path('dashboard/', include('dashboard.urls',
                                namespace='dashboard')),
    path('malls/',     include('malls.urls',
                                namespace='malls')),
    path('tenants/',   include('tenants.urls',
                                namespace='tenants')),
    path('leases/',    include('leases.urls',
                                namespace='leases')),
    path('invoices/',  include('invoices.urls',
                                namespace='invoices')),
    path('payments/',  include('payments.urls',
                                namespace='payments')),
    path('complaints/', include('complaints.urls',
                                 namespace='complaints')),
    path('maintenance/', include('maintenance.urls',
                                  namespace='maintenance')),
    path('notifications/', include('notifications.urls',
                                    namespace='notifications')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )