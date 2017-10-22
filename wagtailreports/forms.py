from __future__ import absolute_import, unicode_literals

from django import forms
from django.forms.models import modelform_factory
from wagtailreports.permissions import report_permission_policy, report_panel_permission_policy


class BaseReportForm(forms.ModelForm):
    permission_policy = report_permission_policy


def get_report_form(model):
    fields = model.admin_form_fields

    return modelform_factory(
        model,
        form=BaseReportForm,
        fields=fields,
    )


class BaseReportPanelForm(forms.ModelForm):
    permission_policy = report_panel_permission_policy


def get_report_panel_form(model):
    fields = model.admin_form_fields

    return modelform_factory(
        model,
        form=BaseReportPanelForm,
        fields=fields,
    )
