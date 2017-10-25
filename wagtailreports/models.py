from __future__ import absolute_import, unicode_literals

from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.db import models
from django.dispatch import Signal
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from wagtail.wagtailsearch import index
from wagtail.wagtailsearch.queryset import SearchableQuerySetMixin


def string_to_datetime(val):
    now = timezone.now()
    day_start = now.replace(hour=0, minute=0, second=0)
    day_end = day_start + timedelta(days=1)
    return {
        'now-14d': (now, day_end + timedelta(days=14)),
        'now-7d': (now, day_end + timedelta(days=7)),
        'now-3d': (now, day_end + timedelta(days=3)),
        'now-2d': (now, day_end + timedelta(days=2)),
        'now-1d': (now, day_end + timedelta(days=1)),
        'now-3h': (now, now + timedelta(hours=3)),
        'now-2h': (now, now + timedelta(hours=2)),
        'now-1h': (now, now + timedelta(hours=1)),
        'today': (day_start, day_end),
        '1h-now': (now - timedelta(hours=1), now),
        '2h-now': (now - timedelta(hours=2), now),
        '3h-now': (now - timedelta(hours=3), now),
        'mn-now': (day_start, now),
        '2d-now': (day_start - timedelta(days=2), now),
        '3d-now': (day_start - timedelta(days=3), now),
        '7d-now': (day_start - timedelta(days=7), now),
        '14d-now': (day_start - timedelta(days=14), now),
    }[val]


class ReportQuerySet(SearchableQuerySetMixin, models.QuerySet):
    pass


@python_2_unicode_compatible
class AbstractReport(index.Indexed, models.Model):
    title = models.CharField(
        max_length=255,
        verbose_name=_('title'),
    )
    query = models.CharField(
        verbose_name=_('query'),
        max_length=200,
        blank=True,
    )
    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        verbose_name=_('content type'),
        related_name='reports',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    ANYONE = ''
    ME = 'me'
    NOT_ME = 'not me'
    OWNER_CHOICES = [
        (ANYONE, _('Anyone')),
        (ME, _('Me')),
        (NOT_ME, _('Not me')),
    ]
    owner = models.CharField(
        choices=OWNER_CHOICES,
        max_length=100,
        blank=True,
    )
    live = models.NullBooleanField(
        verbose_name=_('live'),
        default=None,
    )
    PERIOD_CHOICES = [
        ('now-14d', _('Comming 2 weeks')),
        ('now-7d', _('Comming week')),
        ('now-3d', _('Comming 3 days')),
        ('now-2d', _('Comming 2 days')),
        ('now-1d', _('now - tomorrow midnight')),
        ('now-mn', _('now - midnight')),
        ('now-3h', _('Comming 3 hours')),
        ('now-2h', _('Comming 2 hours')),
        ('now-1h', _('Comming hour')),
        ('today', _('Today')),
        ('1h-now', _('Past hour')),
        ('2h-now', _('Past 2 hours')),
        ('3h-now', _('Past 3 hours')),
        ('mn-now', _('Past midnight - now')),
        ('2d-now', _('Past 2 days')),
        ('3d-now', _('Past 3 days')),
        ('7d-now', _('Past week')),
        ('14d-now', _('Past 2 weeks')),
    ]
    go_live_at = models.CharField(
        verbose_name=_('go live date/time'),
        max_length=100,
        blank=True,
        choices=PERIOD_CHOICES,
    )
    expire_at = models.CharField(
        verbose_name=_("expiry date/time"),
        max_length=100,
        blank=True,
        choices=PERIOD_CHOICES,
    )
    expired = models.NullBooleanField(
        verbose_name=_('expired'),
        default=None,
    )
    locked = models.NullBooleanField(
        verbose_name=_('locked'),
        default=None,
    )
    has_unpublished_changes = models.NullBooleanField(
        verbose_name=_('has unpublished changes'),
        default=None,
    )
    # Display options
    list_length = models.PositiveIntegerField(
        verbose_name=_('list length'),
        default=5
    )
    total_count = models.BooleanField(
        verbose_name=_('display total count'),
        default=False
    )
    # Meta fields
    created_at = models.DateTimeField(
        verbose_name=_('created at'),
        auto_now_add=True
    )
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
        qs = self.content_type.get_all_objects_for_this_type()
        if self.query:
            qs = qs.filter(title__icontains=self.query)
        # if self.owner == self.ME:
        #     qs = qs.filter(owner=self.request.user)
        # if self.owner == self.NOT_ME:
        #     qs = qs.exclude(owner=self.request.user)
        if self.live is not None:
            qs = qs.filter(live=self.live)
        if self.go_live_at:
            start, end = string_to_datetime(self.go_live_at)
            qs = qs.filter(go_live_at__gte=start, go_live_at__lte=end)
        if self.expire_at:
            start, end = string_to_datetime(self.expire_at)
            qs = qs.filter(expire_at__gte=start, expire_at__lte=end)
        if self.expired is not None:
            qs = qs.filter(expired=self.expired)
        if self.locked is not None:
            qs = qs.filter(locked=self.locked)
        if self.has_unpublished_changes is not None:
            qs = qs.filter(has_unpublished_changes=self.has_unpublished_changes)
        ctx = {
            'list': qs[:self.list_length]
        }
        if self.total_count:
            ctx.update({
                'count': qs.count()
            })
        return ctx

    class Meta:
        abstract = True
        verbose_name = _('report')


class Report(AbstractReport):
    admin_form_fields = (
        'title',
        'list_length',
        'total_count',
        'query',
        'content_type',
        'owner',
        'live',
        'go_live_at',
        'expire_at',
        'expired',
        'locked',
        'has_unpublished_changes',
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
