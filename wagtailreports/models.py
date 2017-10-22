from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.db import models
from django.dispatch import Signal
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
# from wagtail.wagtailadmin.utils import get_object_usage
from wagtail.wagtailcore.models import Page
from wagtail.wagtailsearch import index
from wagtail.wagtailsearch.queryset import SearchableQuerySetMixin


class ReportQuerySet(SearchableQuerySetMixin, models.QuerySet):
    pass


@python_2_unicode_compatible
class AbstractReport(index.Indexed, models.Model):
    title = models.CharField(max_length=255, verbose_name=_('title'))
    query = models.TextField(verbose_name=_('query'), blank=True)
    created_at = models.DateTimeField(verbose_name=_('created at'), auto_now_add=True)
    created_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('created by user'),
        null=True,
        blank=True,
        editable=False,
        on_delete=models.SET_NULL
    )

    objects = ReportQuerySet.as_manager()

    def __str__(self):
        return self.title

    @property
    def url(self):
        return reverse('wagtailreports_serve', args=[self.id])

    def is_editable_by_user(self, user):
        from wagtailreports.permissions import report_permission_policy
        return report_permission_policy.user_has_permission_for_instance(user, 'change', self)

    def results(self):
        objects = Page.objects.all()[:5]
        return objects

    class Meta:
        abstract = True
        verbose_name = _('report')


class Report(AbstractReport):
    admin_form_fields = (
        'title',
        'query',
    )


def get_report_model():
    """
    Get the report model from the ``WAGTAILDOCS_REPORT_MODEL`` setting.
    Defauts to the standard :class:`~wagtailreports.models.Report` model
    if no custom model is defined.
    """
    from django.conf import settings
    from django.apps import apps

    try:
        app_label, model_name = settings.WAGTAILDOCS_REPORT_MODEL.split('.')
    except AttributeError:
        return Report
    except ValueError:
        raise ImproperlyConfigured("WAGTAILREPORTS_REPORT_MODEL must be of the form 'app_label.model_name'")

    report_model = apps.get_model(app_label, model_name)
    if report_model is None:
        raise ImproperlyConfigured(
            "WAGTAILREPORTS_REPORT_MODEL refers to model '%s' that has not been installed" %
            settings.WAGTAILDOCS_REPORT_MODEL
        )
    return report_model


report_served = Signal(providing_args=['request'])


class ReportPanelQuerySet(SearchableQuerySetMixin, models.QuerySet):
    pass


@python_2_unicode_compatible
class AbstractReportPanel(index.Indexed, models.Model):
    title = models.CharField(max_length=255, verbose_name=_('title'))
    reports = models.ManyToManyField(
        Report,
        blank=True,
        help_text=_('All reports you like to display in this panel.'),
    )
    for_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        help_text=_('All users that will have this panel displayed on their dashboard.'),
        related_name='report_panel_for_users'
    )
    created_at = models.DateTimeField(verbose_name=_('created at'), auto_now_add=True)
    created_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('created by user'),
        null=True,
        blank=True,
        editable=False,
        on_delete=models.SET_NULL
    )

    objects = ReportPanelQuerySet.as_manager()

    def __str__(self):
        return self.title

    @property
    def url(self):
        return reverse('wagtailreportpanels_serve', args=[self.id])

    def is_editable_by_user(self, user):
        from wagtailreports.permissions import report_panel_permission_policy
        return report_panel_permission_policy.user_has_permission_for_instance(user, 'change', self)

    class Meta:
        abstract = True
        verbose_name = _('report panel')


class ReportPanel(AbstractReportPanel):
    admin_form_fields = (
        'title',
        'reports',
        'for_users',
    )


def get_report_panel_model():
    """
    Get the report panel model from the ``WAGTAILDOCS_REPORT_PANEL_MODEL`` setting.
    Defauts to the standard :class:`~wagtailreports.models.ReportPanel` model
    if no custom model is defined.
    """
    from django.conf import settings
    from django.apps import apps

    try:
        app_label, model_name = settings.WAGTAILDOCS_REPORT_PANEL_MODEL.split('.')
    except AttributeError:
        return ReportPanel
    except ValueError:
        raise ImproperlyConfigured("WAGTAILDOCS_REPORT_PANEL_MODEL must be of the form 'app_label.model_name'")

    report_panel_model = apps.get_model(app_label, model_name)
    if report_panel_model is None:
        raise ImproperlyConfigured(
            "WAGTAILDOCS_REPORT_PANEL_MODEL refers to model '%s' that has not been installed" %
            settings.WAGTAILDOCS_REPORT_PANEL_MODEL
        )
    return report_panel_model


report_panel_served = Signal(providing_args=['request'])
