from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.contrib import admin

from wagtailreports.models import Report, ReportPanel

if hasattr(settings, 'WAGTAILDOCS_REPORT_MODEL') and settings.WAGTAILDOCS_REPORT_MODEL != 'wagtailreports.Report':
    # This installation provides its own custom report class;
    # to avoid confusion, we won't expose the unused wagtailreports.Report class
    # in the admin.
    pass
else:
    admin.site.register(Report)


if hasattr(settings, 'WAGTAILDOCS_REPORT_PANEL_MODEL') and settings.WAGTAILDOCS_REPORT_PANEL_MODEL != 'wagtailreports.ReportPanel':
    # This installation provides its own custom report panel class;
    # to avoid confusion, we won't expose the unused wagtailreports.ReportPanel class
    # in the admin.
    pass
else:
    admin.site.register(ReportPanel)
