from __future__ import absolute_import, unicode_literals

from wagtail.wagtailcore.permission_policies import ModelPermissionPolicy

from wagtailreports.models import get_report_model, get_report_panel_model

report_permission_policy = ModelPermissionPolicy(get_report_model())
report_panel_permission_policy = ModelPermissionPolicy(get_report_panel_model())
