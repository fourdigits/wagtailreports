from __future__ import absolute_import, unicode_literals

import os.path
import unittest

import mock

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from wagtail.tests.utils import WagtailTestUtils
from wagtailreports import models


class TestEditView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        self.report = models.Report(title='Test')
        self.report.file.save('test_edit_view.txt',
                                ContentFile('A test content.'))
        self.edit_url = reverse('wagtailreports:edit', args=(self.report.pk,))
        self.storage = self.report.file.storage

    def update_from_db(self):
        self.report = models.Report.objects.get(pk=self.report.pk)

    def test_reupload_same_name(self):
        """
        Checks that reuploading the report file with the same file name
        changes the file name, to avoid browser cache issues (see #3816).
        """
        old_file = self.report.file
        new_name = self.report.filename
        new_file = SimpleUploadedFile(new_name, b'An updated test content.')

        response = self.client.post(self.edit_url, {
            'title': self.report.title, 'file': new_file,
        })
        self.assertRedirects(response, reverse('wagtailreports:index'))
        self.update_from_db()
        self.assertFalse(self.storage.exists(old_file.name))
        self.assertTrue(self.storage.exists(self.report.file.name))
        self.assertNotEqual(self.report.file.name, 'reports/' + new_name)
        self.assertEqual(self.report.file.read(),
                         b'An updated test content.')

    def test_reupload_different_name(self):
        """
        Checks that reuploading the report file with a different file name
        correctly uses the new file name.
        """
        old_file = self.report.file
        new_name = 'test_reupload_different_name.txt'
        new_file = SimpleUploadedFile(new_name, b'An updated test content.')

        response = self.client.post(self.edit_url, {
            'title': self.report.title, 'file': new_file,
        })
        self.assertRedirects(response, reverse('wagtailreports:index'))
        self.update_from_db()
        self.assertFalse(self.storage.exists(old_file.name))
        self.assertTrue(self.storage.exists(self.report.file.name))
        self.assertEqual(self.report.file.name, 'reports/' + new_name)
        self.assertEqual(self.report.file.read(),
                         b'An updated test content.')


class TestServeView(TestCase):
    def setUp(self):
        self.report = models.Report(title="Test report")
        self.report.file.save('example.doc', ContentFile("A boring example report"))

    def tearDown(self):
        # delete the FieldFile directly because the TestCase does not commit
        # transactions to trigger transaction.on_commit() in the signal handler
        self.report.file.delete()

    def get(self):
        return self.client.get(reverse('wagtailreports_serve', args=(self.report.id, self.report.filename)))

    def test_response_code(self):
        self.assertEqual(self.get().status_code, 200)

    def test_content_disposition_header(self):
        self.assertEqual(
            self.get()['Content-Disposition'],
            'attachment; filename="{}"'.format(self.report.filename))

    def test_content_length_header(self):
        self.assertEqual(self.get()['Content-Length'], '25')

    def test_content_type_header(self):
        self.assertEqual(self.get()['Content-Type'], 'application/msword')

    def test_is_streaming_response(self):
        self.assertTrue(self.get().streaming)

    def test_content(self):
        self.assertEqual(b"".join(self.get().streaming_content), b"A boring example report")

    def test_report_served_fired(self):
        mock_handler = mock.MagicMock()
        models.report_served.connect(mock_handler)

        self.get()

        self.assertEqual(mock_handler.call_count, 1)
        self.assertEqual(mock_handler.mock_calls[0][2]['sender'], models.Report)
        self.assertEqual(mock_handler.mock_calls[0][2]['instance'], self.report)

    def test_with_nonexistent_report(self):
        response = self.client.get(reverse('wagtailreports_serve', args=(1000, 'blahblahblah', )))
        self.assertEqual(response.status_code, 404)

    def test_with_incorrect_filename(self):
        response = self.client.get(reverse('wagtailreports_serve', args=(self.report.id, 'incorrectfilename')))
        self.assertEqual(response.status_code, 404)

    def clear_sendfile_cache(self):
        from wagtail.utils.sendfile import _get_sendfile
        _get_sendfile.clear()


class TestServeViewWithSendfile(TestCase):
    def setUp(self):
        # Import using a try-catch block to prevent crashes if the
        # django-sendfile module is not installed
        try:
            import sendfile  # noqa
        except ImportError:
            raise unittest.SkipTest("django-sendfile not installed")

        self.report = models.Report(title="Test report")
        self.report.file.save('example.doc', ContentFile("A boring example report"))

    def tearDown(self):
        # delete the FieldFile directly because the TestCase does not commit
        # transactions to trigger transaction.on_commit() in the signal handler
        self.report.file.delete()

    def get(self):
        return self.client.get(reverse('wagtailreports_serve', args=(self.report.id, self.report.filename)))

    def clear_sendfile_cache(self):
        from wagtail.utils.sendfile import _get_sendfile
        _get_sendfile.clear()

    @override_settings(SENDFILE_BACKEND='sendfile.backends.xsendfile')
    def test_sendfile_xsendfile_backend(self):
        self.clear_sendfile_cache()
        response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['X-Sendfile'], self.report.file.path)

    @override_settings(
        SENDFILE_BACKEND='sendfile.backends.mod_wsgi',
        SENDFILE_ROOT=settings.MEDIA_ROOT,
        SENDFILE_URL=settings.MEDIA_URL[:-1]
    )
    def test_sendfile_mod_wsgi_backend(self):
        self.clear_sendfile_cache()
        response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Location'], os.path.join(settings.MEDIA_URL, self.report.file.name))

    @override_settings(
        SENDFILE_BACKEND='sendfile.backends.nginx',
        SENDFILE_ROOT=settings.MEDIA_ROOT,
        SENDFILE_URL=settings.MEDIA_URL[:-1]
    )
    def test_sendfile_nginx_backend(self):
        self.clear_sendfile_cache()
        response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['X-Accel-Redirect'], os.path.join(settings.MEDIA_URL, self.report.file.name))


class TestServeWithUnicodeFilename(TestCase):
    def setUp(self):
        self.report = models.Report(title="Test report")

        # Setting this filename in the content-disposition header fails on Django <1.8, Python 2
        # due to https://code.djangoproject.com/ticket/20889
        self.filename = 'docs\u0627\u0644\u0643\u0627\u062a\u062f\u0631\u0627'
        '\u064a\u064a\u0629_\u0648\u0627\u0644\u0633\u0648\u0642'
        try:
            self.report.file.save(self.filename, ContentFile("A boring example report"))
        except UnicodeEncodeError:
            raise unittest.SkipTest("Filesystem doesn't support unicode filenames")

    def test_response_code(self):
        response = self.client.get(reverse('wagtailreports_serve', args=(self.report.id, self.filename)))
        self.assertEqual(response.status_code, 200)
