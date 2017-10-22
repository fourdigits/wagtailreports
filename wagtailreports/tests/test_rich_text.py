from __future__ import absolute_import, unicode_literals

from bs4 import BeautifulSoup

from django.test import TestCase

from wagtailreports.rich_text import ReportLinkHandler


class TestReportRichTextLinkHandler(TestCase):
    fixtures = ['test.json']

    def test_get_db_attributes(self):
        soup = BeautifulSoup('<a data-id="test-id">foo</a>', 'html5lib')
        tag = soup.a
        result = ReportLinkHandler.get_db_attributes(tag)
        self.assertEqual(result,
                         {'id': 'test-id'})

    def test_expand_db_attributes_report_does_not_exist(self):
        result = ReportLinkHandler.expand_db_attributes(
            {'id': 0},
            False
        )
        self.assertEqual(result, '<a>')

    def test_expand_db_attributes_for_editor(self):
        result = ReportLinkHandler.expand_db_attributes(
            {'id': 1},
            True
        )
        self.assertEqual(result,
                         '<a data-linktype="report" data-id="1" href="/reports/1/test.pdf">')

    def test_expand_db_attributes_not_for_editor(self):
        result = ReportLinkHandler.expand_db_attributes(
            {'id': 1},
            False
        )
        self.assertEqual(result,
                         '<a href="/reports/1/test.pdf">')
