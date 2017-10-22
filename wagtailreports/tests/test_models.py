from __future__ import absolute_import, unicode_literals

import unittest

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.files.base import ContentFile
from django.db import transaction
from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings

from wagtail.wagtailcore.models import GroupCollectionPermission
from wagtailreports import models, signal_handlers
from wagtailreports.models import get_report_model
from wagtail.wagtailimages.tests.utils import get_test_image_file


class TestReportQuerySet(TestCase):
    def test_search_method(self):
        # Make a test report
        report = models.Report.objects.create(title="Test report")

        # Search for it
        results = models.Report.objects.search("Test")
        self.assertEqual(list(results), [report])

    def test_operators(self):
        aaa_report = models.Report.objects.create(title="AAA Test report")
        zzz_report = models.Report.objects.create(title="ZZZ Test report")

        results = models.Report.objects.search("aaa test", operator='and')
        self.assertEqual(list(results), [aaa_report])

        results = models.Report.objects.search("aaa test", operator='or')
        sorted_results = sorted(results, key=lambda doc: report.title)
        self.assertEqual(sorted_results, [aaa_report, zzz_report])

    def test_custom_ordering(self):
        aaa_report = models.Report.objects.create(title="AAA Test report")
        zzz_report = models.Report.objects.create(title="ZZZ Test report")

        results = models.Report.objects.order_by('title').search("Test")
        self.assertEqual(list(results), [aaa_report, zzz_report])
        results = models.Report.objects.order_by('-title').search("Test")
        self.assertEqual(list(results), [zzz_report, aaa_report])


class TestReportPermissions(TestCase):
    def setUp(self):
        # Create some user accounts for testing permissions
        User = get_user_model()
        self.user = User.objects.create_user(username='user', email='user@email.com', password='password')
        self.owner = User.objects.create_user(username='owner', email='owner@email.com', password='password')
        self.editor = User.objects.create_user(username='editor', email='editor@email.com', password='password')
        self.editor.groups.add(Group.objects.get(name='Editors'))
        self.administrator = User.objects.create_superuser(
            username='administrator',
            email='administrator@email.com',
            password='password'
        )

        # Owner user must have the add_report permission
        self.adders_group = Group.objects.create(name='Report adders')
        self.owner.groups.add(self.adders_group)

        # Create a report for running tests on
        self.report = models.Report.objects.create(title="Test report", created_by_user=self.owner)

    def test_administrator_can_edit(self):
        self.assertTrue(self.report.is_editable_by_user(self.administrator))

    def test_editor_can_edit(self):
        self.assertTrue(self.report.is_editable_by_user(self.editor))

    def test_owner_can_edit(self):
        self.assertTrue(self.report.is_editable_by_user(self.owner))

    def test_user_cant_edit(self):
        self.assertFalse(self.report.is_editable_by_user(self.user))


class TestReportFilenameProperties(TestCase):
    def setUp(self):
        self.report = models.Report(title="Test report")
        self.report.file.save('example.doc', ContentFile("A boring example report"))

        self.extensionless_report = models.Report(title="Test report")
        self.extensionless_report.file.save('example', ContentFile("A boring example report"))

    def test_filename(self):
        self.assertEqual('example.doc', self.report.filename)
        self.assertEqual('example', self.extensionless_report.filename)

    def test_file_extension(self):
        self.assertEqual('doc', self.report.file_extension)
        self.assertEqual('', self.extensionless_report.file_extension)

    def tearDown(self):
        # delete the FieldFile directly because the TestCase does not commit
        # transactions to trigger transaction.on_commit() in the signal handler
        self.report.file.delete()
        self.extensionless_report.file.delete()


class TestFilesDeletedForDefaultModels(TransactionTestCase):
    '''
    Because we expect file deletion to only happen once a transaction is
    successfully committed, we must run these tests using TransactionTestCase
    per the following reportation:

        Django's TestCase class wraps each test in a transaction and rolls back that
        transaction after each test, in order to provide test isolation. This means
        that no transaction is ever actually committed, thus your on_commit()
        callbacks will never be run. If you need to test the results of an
        on_commit() callback, use a TransactionTestCase instead.
        https://docs.djangoproject.com/en/1.10/topics/db/transactions/#use-in-tests
    '''
    def setUp(self):
        pass

    def test_oncommit_available(self):
        self.assertEqual(hasattr(transaction, 'on_commit'), signal_handlers.TRANSACTION_ON_COMMIT_AVAILABLE)

    @unittest.skipUnless(signal_handlers.TRANSACTION_ON_COMMIT_AVAILABLE, 'is required for this test')
    def test_report_file_deleted_oncommit(self):
        with transaction.atomic():
            report = get_report_model().objects.create(title="Test Image", file=get_test_image_file())
            self.assertTrue(report.file.storage.exists(report.file.name))
            report.delete()
            self.assertTrue(report.file.storage.exists(report.file.name))
        self.assertFalse(report.file.storage.exists(report.file.name))

    @unittest.skipIf(signal_handlers.TRANSACTION_ON_COMMIT_AVAILABLE, 'duplicate')
    def test_report_file_deleted(self):
        '''
            this test duplicates `test_image_file_deleted_oncommit` for
            django 1.8 support and can be removed once django 1.8 is no longer
            supported
        '''
        with transaction.atomic():
            report = get_report_model().objects.create(title="Test Image", file=get_test_image_file())
            self.assertTrue(report.file.storage.exists(report.file.name))
            report.delete()
        self.assertFalse(report.file.storage.exists(report.file.name))


@override_settings(WAGTAILDOCS_REPORT_MODEL='tests.CustomReport')
class TestFilesDeletedForCustomModels(TestFilesDeletedForDefaultModels):
    def setUp(self):
        #: Sadly signal receivers only get connected when starting django.
        #: We will re-attach them here to mimic the django startup behavior
        #: and get the signals connected to our custom model..
        signal_handlers.register_signal_handlers()

    def test_report_model(self):
        cls = get_report_model()
        self.assertEqual('%s.%s' % (cls._meta.app_label, cls.__name__), 'tests.CustomReport')
