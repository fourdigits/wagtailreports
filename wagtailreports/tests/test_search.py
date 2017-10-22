from __future__ import absolute_import, unicode_literals

import unittest

from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings
from django.utils.six import b

from wagtail.tests.utils import WagtailTestUtils
from wagtailreports import models


@override_settings(_WAGTAILSEARCH_FORCE_AUTO_UPDATE=['elasticsearch'])
class TestIssue613(TestCase, WagtailTestUtils):
    def get_elasticsearch_backend(self):
        from django.conf import settings
        from wagtail.wagtailsearch.backends import get_search_backend

        backend_path = 'wagtail.wagtailsearch.backends.elasticsearch'

        # Search WAGTAILSEARCH_BACKENDS for an entry that uses the given backend path
        for backend_name, backend_conf in settings.WAGTAILSEARCH_BACKENDS.items():
            if backend_conf['BACKEND'] == backend_path:
                return get_search_backend(backend_name)
        else:
            # no conf entry found - skip tests for this backend
            raise unittest.SkipTest("No WAGTAILSEARCH_BACKENDS entry for the backend %s" % backend_path)

    def setUp(self):
        self.search_backend = self.get_elasticsearch_backend()
        self.login()

    def add_report(self, **params):
        # Build a fake file
        fake_file = ContentFile(b("A boring example report"))
        fake_file.name = 'test.txt'

        # Submit
        post_data = {
            'title': "Test report",
            'file': fake_file,
        }
        post_data.update(params)
        response = self.client.post(reverse('wagtailreports:add'), post_data)

        # User should be redirected back to the index
        self.assertRedirects(response, reverse('wagtailreports:index'))

        # Report should be created
        report = models.Report.objects.filter(title=post_data['title'])
        self.assertTrue(report.exists())
        return report.first()

    def edit_report(self, **params):
        # Build a fake file
        fake_file = ContentFile(b("A boring example report"))
        fake_file.name = 'test.txt'

        # Create a report without tags to edit
        report = models.Report.objects.create(title="Test report", file=fake_file)

        # Build another fake file
        another_fake_file = ContentFile(b("A boring example report"))
        another_fake_file.name = 'test.txt'

        # Submit
        post_data = {
            'title': "Test report changed!",
            'file': another_fake_file,
        }
        post_data.update(params)
        response = self.client.post(reverse('wagtailreports:edit', args=(report.id,)), post_data)

        # User should be redirected back to the index
        self.assertRedirects(response, reverse('wagtailreports:index'))

        # Report should be changed
        report = models.Report.objects.filter(title=post_data['title'])
        self.assertTrue(report.exists())
        return report.first()

    def test_issue_613_on_add(self):
        # Reset the search index
        self.search_backend.reset_index()
        self.search_backend.add_type(models.Report)

        # Add a report with some tags
        report = self.add_report(tags="hello")
        self.search_backend.refresh_index()

        # Search for it by tag
        results = self.search_backend.search("hello", models.Report)

        # Check
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, report.id)

    def test_issue_613_on_edit(self):
        # Reset the search index
        self.search_backend.reset_index()
        self.search_backend.add_type(models.Report)

        # Add a report with some tags
        report = self.edit_report(tags="hello")
        self.search_backend.refresh_index()

        # Search for it by tag
        results = self.search_backend.search("hello", models.Report)

        # Check
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, report.id)
