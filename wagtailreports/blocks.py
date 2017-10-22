from __future__ import absolute_import, unicode_literals

from django.utils.functional import cached_property
from django.utils.html import format_html

from wagtail.wagtailcore.blocks import ChooserBlock


class ReportChooserBlock(ChooserBlock):
    @cached_property
    def target_model(self):
        from wagtailreports.models import get_report_model
        return get_report_model()

    @cached_property
    def widget(self):
        from wagtailreports.widgets import AdminReportChooser
        return AdminReportChooser

    def render_basic(self, value, context=None):
        if value:
            return format_html('<a href="{0}">{1}</a>', value.url, value.title)
        else:
            return ''

    class Meta:
        icon = "doc-empty"
