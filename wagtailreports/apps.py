from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig


class WagtailReportsAppConfig(AppConfig):
    name = 'wagtailreports'
    label = 'wagtailreports'
    verbose_name = "Wagtail reports"

    def ready(self):
        from wagtailreports.signal_handlers import register_signal_handlers
        register_signal_handlers()
