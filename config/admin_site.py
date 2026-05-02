from two_factor.admin import AdminSiteOTPRequiredMixin
from unfold.sites import UnfoldAdminSite


class AdminSite(AdminSiteOTPRequiredMixin, UnfoldAdminSite):
    pass
