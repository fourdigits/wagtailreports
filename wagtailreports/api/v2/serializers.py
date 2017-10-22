from __future__ import absolute_import, unicode_literals

from rest_framework.fields import Field

from wagtail.api.v2.serializers import BaseSerializer
from wagtail.api.v2.utils import get_full_url


class ReportDownloadUrlField(Field):
    """
    Serializes the "download_url" field for reports.

    Example:
    "download_url": "http://api.example.com/reports/1/my_report.pdf"
    """
    def get_attribute(self, instance):
        return instance

    def to_representation(self, report):
        return get_full_url(self.context['request'], report.url)


class ReportSerializer(BaseSerializer):
    download_url = ReportDownloadUrlField(read_only=True)


class ReportPanelSerializer(BaseSerializer):
    pass
