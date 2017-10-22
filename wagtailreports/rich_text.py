from __future__ import absolute_import, unicode_literals

from django.utils.html import escape

from wagtailreports.models import get_report_model


class ReportLinkHandler(object):
    @staticmethod
    def get_db_attributes(tag):
        return {'id': tag['data-id']}

    @staticmethod
    def expand_db_attributes(attrs, for_editor):
        Report = get_report_model()
        try:
            report = Report.objects.get(id=attrs['id'])

            if for_editor:
                editor_attrs = 'data-linktype="report" data-id="%d" ' % report.id
            else:
                editor_attrs = ''

            return '<a %shref="%s">' % (editor_attrs, escape(report.url))
        except Report.DoesNotExist:
            return "<a>"
