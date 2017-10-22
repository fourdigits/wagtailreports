from __future__ import absolute_import, unicode_literals

import json

from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailadmin.widgets import AdminChooser
from wagtailreports.models import get_report_model


class AdminReportChooser(AdminChooser):
    choose_one_text = _('Choose a report')
    choose_another_text = _('Choose another report')
    link_to_chosen_text = _('Edit this report')

    def __init__(self, **kwargs):
        super(AdminReportChooser, self).__init__(**kwargs)
        self.report_model = get_report_model()

    def render_html(self, name, value, attrs):
        instance, value = self.get_instance_and_id(self.report_model, value)
        original_field_html = super(AdminReportChooser, self).render_html(name, value, attrs)

        return render_to_string("wagtailreports/widgets/report_chooser.html", {
            'widget': self,
            'original_field_html': original_field_html,
            'attrs': attrs,
            'value': value,
            'report': instance,
        })

    def render_js_init(self, id_, name, value):
        return "createReportChooser({0});".format(json.dumps(id_))
