from django.contrib.admin.apps import AdminConfig as BaseAdminConfig

class AdminConfig(BaseAdminConfig):  # pyright: ignore[reportIncompatibleMethodOverride]
    default_site = 'config.admin_site.AdminSite'
