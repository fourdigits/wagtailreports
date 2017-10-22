from __future__ import absolute_import, unicode_literals

from wagtail.api.v2.endpoints import BaseAPIEndpoint
from wagtail.api.v2.filters import FieldsFilter, OrderingFilter, SearchFilter

from ...models import get_report_model, get_report_panel_model
from .serializers import ReportSerializer, ReportPanelSerializer


class ReportsAPIEndpoint(BaseAPIEndpoint):
    base_serializer_class = ReportSerializer
    filter_backends = [FieldsFilter, OrderingFilter, SearchFilter]
    body_fields = BaseAPIEndpoint.body_fields + ['title']
    meta_fields = BaseAPIEndpoint.meta_fields + ['tags', 'download_url']
    listing_default_fields = BaseAPIEndpoint.listing_default_fields + ['title', 'tags', 'download_url']
    nested_default_fields = BaseAPIEndpoint.nested_default_fields + ['title', 'download_url']
    name = 'reports'
    model = get_report_model()


class ReportPanelsAPIEndpoint(BaseAPIEndpoint):
    base_serializer_class = ReportPanelSerializer
    filter_backends = [FieldsFilter, OrderingFilter, SearchFilter]
    body_fields = BaseAPIEndpoint.body_fields + ['title']
    meta_fields = BaseAPIEndpoint.meta_fields + ['tags', 'download_url']
    listing_default_fields = BaseAPIEndpoint.listing_default_fields + ['title', 'tags', 'download_url']
    nested_default_fields = BaseAPIEndpoint.nested_default_fields + ['title', 'download_url']
    name = 'reportpanels'
    model = get_report_panel_model()
