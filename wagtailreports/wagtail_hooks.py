from __future__ import absolute_import, unicode_literals

from django.conf.urls import include, url
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core import urlresolvers
from django.template.loader import get_template, render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from wagtail.wagtailadmin.menu import MenuItem
from wagtail.wagtailcore import hooks

from wagtailreports import admin_report_urls, admin_reportpanel_urls
from wagtailreports.api.admin.endpoints import ReportPanelsAdminAPIEndpoint, ReportsAdminAPIEndpoint
from wagtailreports.models import get_report_model, get_report_panel_model
from wagtailreports.permissions import report_panel_permission_policy, report_permission_policy


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^reports/', include(admin_report_urls, app_name='wagtailreports', namespace='wagtailreports')),
        url(r'^reportpanels/', include(admin_reportpanel_urls, app_name='wagtailreportpanels', namespace='wagtailreportpanels')),
    ]


@hooks.register('construct_admin_api')
def construct_admin_api(router):
    router.register_endpoint('reports', ReportsAdminAPIEndpoint)
    router.register_endpoint('reportpanels', ReportPanelsAdminAPIEndpoint)


class ReportsMenuItem(MenuItem):
    def is_shown(self, request):
        return report_permission_policy.user_has_any_permission(
            request.user, ['add', 'change', 'delete']
        )


@hooks.register('register_settings_menu_item')
def register_reports_menu_item():
    return ReportsMenuItem(
        _('Reports'),
        urlresolvers.reverse('wagtailreports:index'),
        name='reports',
        classnames='icon icon-doc-full-inverse',
        order=900  # TODO: Put order in a setting, add default.
    )


class ReportPanelMenuItem(MenuItem):
    def is_shown(self, request):
        return report_panel_permission_policy.user_has_any_permission(
            request.user, ['add', 'change', 'delete']
        )


@hooks.register('register_settings_menu_item')
def register_report_panels_menu_item():
    return ReportPanelMenuItem(
        _('Report panels'),
        urlresolvers.reverse('wagtailreportpanels:index'),
        name='report-panels',
        classnames='icon icon-doc-full-inverse',
        order=1000  # TODO: Put order in a setting, add default.
    )


@hooks.register('register_permissions')
def register_report_panels_permissions():
    Report = get_report_model()
    ReportPanel = get_report_panel_model()
    content_types = ContentType.objects.get_for_models(Report, ReportPanel).values()
    return Permission.objects.filter(content_type__in=content_types)


class ReportPanel(object):
    order = 100

    def __init__(self, request):
        self.request = request

    def render(self):
        context = {
            'panels': self.request.user.report_panel_for_users.all().prefetch_related('reports'),
        }
        rendered = render_to_string('wagtailreports/homepage/report_panels.html', context)
        return mark_safe(rendered)


@hooks.register('construct_homepage_panels')
def add_report_panel(request, panels):
    return panels.append(ReportPanel(request))
