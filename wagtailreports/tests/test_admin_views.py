from __future__ import absolute_import, unicode_literals

import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings
from django.utils.six import b

from wagtail.tests.testapp.models import EventPage, EventPageRelatedLink
from wagtail.tests.utils import WagtailTestUtils
from wagtail.wagtailcore.models import Page
from wagtailreports import models


class TestReportIndexView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def test_simple(self):
        response = self.client.get(reverse('wagtailreports:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailreports/reports/index.html')
        self.assertContains(response, "Add a report")

    def test_search(self):
        response = self.client.get(reverse('wagtailreports:index'), {'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query_string'], "Hello")

    def make_docs(self):
        for i in range(50):
            report = models.Report(title="Test " + str(i))
            report.save()

    def test_pagination(self):
        self.make_docs()

        response = self.client.get(reverse('wagtailreports:index'), {'p': 2})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailreports/reports/index.html')

        # Check that we got the correct page
        self.assertEqual(response.context['reports'].number, 2)

    def test_pagination_invalid(self):
        self.make_docs()

        response = self.client.get(reverse('wagtailreports:index'), {'p': 'Hello World!'})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailreports/reports/index.html')

        # Check that we got page one
        self.assertEqual(response.context['reports'].number, 1)

    def test_pagination_out_of_range(self):
        self.make_docs()

        response = self.client.get(reverse('wagtailreports:index'), {'p': 99999})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailreports/reports/index.html')

        # Check that we got the last page
        self.assertEqual(response.context['reports'].number, response.context['reports'].paginator.num_pages)

    def test_ordering(self):
        orderings = ['title', '-created_at']
        for ordering in orderings:
            response = self.client.get(reverse('wagtailreports:index'), {'ordering': ordering})
            self.assertEqual(response.status_code, 200)


class TestReportAddView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def test_get(self):
        response = self.client.get(reverse('wagtailreports:add'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailreports/reports/add.html')

        # Ensure the form supports file uploads
        self.assertContains(response, 'enctype="multipart/form-data"')

    def test_post(self):
        # Build a fake file
        fake_file = ContentFile(b("A boring example report"))
        fake_file.name = 'test.txt'

        # Submit
        post_data = {
            'title': "Test report",
            'file': fake_file,
        }
        response = self.client.post(reverse('wagtailreports:add'), post_data)

        # User should be redirected back to the index
        self.assertRedirects(response, reverse('wagtailreports:index'))

        # Report should be created, and be placed in the root collection
        self.assertTrue(models.Report.objects.filter(title="Test report").exists())


class TestReportEditView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Build a fake file
        fake_file = ContentFile(b("A boring example report"))
        fake_file.name = 'test.txt'

        # Create a report to edit
        self.report = models.Report.objects.create(title="Test report", file=fake_file)

    def test_simple(self):
        response = self.client.get(reverse('wagtailreports:edit', args=(self.report.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailreports/reports/edit.html')

        # Ensure the form supports file uploads
        self.assertContains(response, 'enctype="multipart/form-data"')

    def test_post(self):
        # Build a fake file
        fake_file = ContentFile(b("A boring example report"))
        fake_file.name = 'test.txt'

        # Submit title change
        post_data = {
            'title': "Test report changed!",
            'file': fake_file,
        }
        response = self.client.post(reverse('wagtailreports:edit', args=(self.report.id,)), post_data)

        # User should be redirected back to the index
        self.assertRedirects(response, reverse('wagtailreports:index'))

        # Report title should be changed
        self.assertEqual(models.Report.objects.get(id=self.report.id).title, "Test report changed!")

    def test_with_missing_source_file(self):
        # Build a fake file
        fake_file = ContentFile(b("An ephemeral report"))
        fake_file.name = 'to-be-deleted.txt'

        # Create a new report to delete the source for
        report = models.Report.objects.create(title="Test missing source report", file=fake_file)
        report.file.delete(False)

        response = self.client.get(reverse('wagtailreports:edit', args=(report.id,)), {})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailreports/reports/edit.html')

        self.assertContains(response, 'File not found')


class TestReportDeleteView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Create a report to delete
        self.report = models.Report.objects.create(title="Test report")

    def test_simple(self):
        response = self.client.get(reverse('wagtailreports:delete', args=(self.report.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailreports/reports/confirm_delete.html')

    def test_delete(self):
        # Submit title change
        response = self.client.post(reverse('wagtailreports:delete', args=(self.report.id,)))

        # User should be redirected back to the index
        self.assertRedirects(response, reverse('wagtailreports:index'))

        # Report should be deleted
        self.assertFalse(models.Report.objects.filter(id=self.report.id).exists())


class TestMultipleReportUploader(TestCase, WagtailTestUtils):
    """
    This tests the multiple report upload views located in wagtailreports/views/multiple.py
    """
    def setUp(self):
        self.login()

        # Create a report for running tests on
        self.report = models.Report.objects.create(
            title="Test report",
            file=ContentFile(b("Simple text report")),
        )

    # def test_add(self):
    #     """
    #     This tests that the add view responds correctly on a GET request
    #     """
    #     # Send request
    #     response = self.client.get(reverse('wagtailreports:add_multiple'))
    #
    #     # Check response
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, 'wagtailreports/multiple/add.html')
    #
    #     # no collection chooser when only one collection exists
    #     self.assertNotContains(response, '<label for="id_addreport_collection">')


    # def test_add_post(self):
    #     """
    #     This tests that a POST request to the add view saves the report and returns an edit form
    #     """
    #     response = self.client.post(reverse('wagtailreports:add_multiple'), {
    #         'files[]': SimpleUploadedFile('test.png', b"Simple text report"),
    #     }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    #
    #     # Check response
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response['Content-Type'], 'application/json')
    #     self.assertTemplateUsed(response, 'wagtailreports/multiple/edit_form.html')
    #
    #     # Check report
    #     self.assertIn('doc', response.context)
    #     self.assertEqual(response.context['doc'].title, 'test.png')
    #     self.assertTrue(response.context['doc'].file_size)
    #
    #     # check that it is in the root collection
    #     report = models.Report.objects.get(title='test.png')
    #     root_collection = Collection.get_first_root_node()
    #     self.assertEqual(report.collection, root_collection)
    #
    #     # Check form
    #     self.assertIn('form', response.context)
    #     self.assertEqual(response.context['form'].initial['title'], 'test.png')
    #
    #     # Check JSON
    #     response_json = json.loads(response.content.decode())
    #     self.assertIn('doc_id', response_json)
    #     self.assertIn('form', response_json)
    #     self.assertIn('success', response_json)
    #     self.assertEqual(response_json['doc_id'], response.context['doc'].id)
    #     self.assertTrue(response_json['success'])


    def test_edit_get(self):
        """
        This tests that a GET request to the edit view returns a 405 "METHOD NOT ALLOWED" response
        """
        # Send request
        response = self.client.get(reverse('wagtailreports:edit_multiple', args=(self.report.id, )))

        # Check response
        self.assertEqual(response.status_code, 405)

    def test_edit_post(self):
        """
        This tests that a POST request to the edit view edits the report
        """
        # Send request
        response = self.client.post(reverse('wagtailreports:edit_multiple', args=(self.report.id, )), {
            ('doc-%d-title' % self.report.id): "New title!",
            ('doc-%d-tags' % self.report.id): "",
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn('doc_id', response_json)
        self.assertNotIn('form', response_json)
        self.assertIn('success', response_json)
        self.assertEqual(response_json['doc_id'], self.report.id)
        self.assertTrue(response_json['success'])

    def test_edit_post_noajax(self):
        """
        This tests that a POST request to the edit view without AJAX returns a 400 response
        """
        # Send request
        response = self.client.post(reverse('wagtailreports:edit_multiple', args=(self.report.id, )), {
            ('doc-%d-title' % self.report.id): "New title!",
            ('doc-%d-tags' % self.report.id): "",
        })

        # Check response
        self.assertEqual(response.status_code, 400)

    def test_edit_post_validation_error(self):
        """
        This tests that a POST request to the edit page returns a json report with "success=False"
        and a form with the validation error indicated
        """
        # Send request
        response = self.client.post(reverse('wagtailreports:edit_multiple', args=(self.report.id, )), {
            ('doc-%d-title' % self.report.id): "",  # Required
            ('doc-%d-tags' % self.report.id): "",
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertTemplateUsed(response, 'wagtailreports/multiple/edit_form.html')

        # Check that a form error was raised
        self.assertFormError(response, 'form', 'title', "This field is required.")

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn('doc_id', response_json)
        self.assertIn('form', response_json)
        self.assertIn('success', response_json)
        self.assertEqual(response_json['doc_id'], self.report.id)
        self.assertFalse(response_json['success'])

    def test_delete_get(self):
        """
        This tests that a GET request to the delete view returns a 405 "METHOD NOT ALLOWED" response
        """
        # Send request
        response = self.client.get(reverse('wagtailreports:delete_multiple', args=(self.report.id, )))

        # Check response
        self.assertEqual(response.status_code, 405)

    def test_delete_post(self):
        """
        This tests that a POST request to the delete view deletes the report
        """
        # Send request
        response = self.client.post(reverse('wagtailreports:delete_multiple', args=(self.report.id, )), HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        # Make sure the report is deleted
        self.assertFalse(models.Report.objects.filter(id=self.report.id).exists())

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn('doc_id', response_json)
        self.assertIn('success', response_json)
        self.assertEqual(response_json['doc_id'], self.report.id)
        self.assertTrue(response_json['success'])

    def test_delete_post_noajax(self):
        """
        This tests that a POST request to the delete view without AJAX returns a 400 response
        """
        # Send request
        response = self.client.post(reverse('wagtailreports:delete_multiple', args=(self.report.id, )))

        # Check response
        self.assertEqual(response.status_code, 400)


class TestReportChooserView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.login()

    def test_simple(self):
        response = self.client.get(reverse('wagtailreports:chooser'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailreports/chooser/chooser.html')
        self.assertTemplateUsed(response, 'wagtailreports/chooser/chooser.js')

    def test_search(self):
        response = self.client.get(reverse('wagtailreports:chooser'), {'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query_string'], "Hello")

    def make_docs(self):
        for i in range(50):
            report = models.Report(title="Test " + str(i))
            report.save()

    def test_pagination(self):
        self.make_docs()

        response = self.client.get(reverse('wagtailreports:chooser'), {'p': 2})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailreports/reports/list.html')

        # Check that we got the correct page
        self.assertEqual(response.context['reports'].number, 2)

    def test_pagination_invalid(self):
        self.make_docs()

        response = self.client.get(reverse('wagtailreports:chooser'), {'p': 'Hello World!'})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailreports/reports/list.html')

        # Check that we got page one
        self.assertEqual(response.context['reports'].number, 1)

    def test_pagination_out_of_range(self):
        self.make_docs()

        response = self.client.get(reverse('wagtailreports:chooser'), {'p': 99999})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailreports/reports/list.html')

        # Check that we got the last page
        self.assertEqual(response.context['reports'].number, response.context['reports'].paginator.num_pages)

    def test_construct_queryset_hook_browse(self):
        report = models.Report.objects.create(
            title="Test report shown",
            created_by_user=self.user,
        )
        models.Report.objects.create(
            title="Test report not shown",
        )

        def filter_reports(reports, request):
            # Filter on `created_by_user` because it is
            # the only default FilterField in search_fields
            return reports.filter(created_by_user=self.user)

        with self.register_hook('construct_report_chooser_queryset', filter_reports):
            response = self.client.get(reverse('wagtailreports:chooser'))
        self.assertEqual(len(response.context['reports']), 1)
        self.assertEqual(response.context['reports'][0], report)

    def test_construct_queryset_hook_search(self):
        report = models.Report.objects.create(
            title="Test report shown",
            created_by_user=self.user,
        )
        models.Report.objects.create(
            title="Test report not shown",
        )

        def filter_reports(reports, request):
            # Filter on `created_by_user` because it is
            # the only default FilterField in search_fields
            return reports.filter(created_by_user=self.user)

        with self.register_hook('construct_report_chooser_queryset', filter_reports):
            response = self.client.get(reverse('wagtailreports:chooser'), {'q': 'Test'})
        self.assertEqual(len(response.context['reports']), 1)
        self.assertEqual(response.context['reports'][0], report)


class TestReportChooserChosenView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Create a report to choose
        self.report = models.Report.objects.create(title="Test report")

    def test_simple(self):
        response = self.client.get(reverse('wagtailreports:report_chosen', args=(self.report.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailreports/chooser/report_chosen.js')


class TestReportChooserUploadView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def test_simple(self):
        response = self.client.get(reverse('wagtailreports:chooser_upload'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailreports/chooser/chooser.html')
        self.assertTemplateUsed(response, 'wagtailreports/chooser/chooser.js')

    def test_post(self):
        # Build a fake file
        fake_file = ContentFile(b("A boring example report"))
        fake_file.name = 'test.txt'

        # Submit
        post_data = {
            'title': "Test report",
            'file': fake_file,
        }
        response = self.client.post(reverse('wagtailreports:chooser_upload'), post_data)

        # Check that the response is a javascript file saying the report was chosen
        self.assertTemplateUsed(response, 'wagtailreports/chooser/report_chosen.js')
        self.assertContains(response, "modal.respond('reportChosen'")

        # Report should be created
        self.assertTrue(models.Report.objects.filter(title="Test report").exists())


class TestReportChooserUploadViewWithLimitedPermissions(TestCase, WagtailTestUtils):
    def setUp(self):
        add_doc_permission = Permission.objects.get(
            content_type__app_label='wagtailreports', codename='add_report'
        )
        admin_permission = Permission.objects.get(
            content_type__app_label='wagtailadmin', codename='access_admin'
        )

        root_collection = Collection.get_first_root_node()
        self.evil_plans_collection = root_collection.add_child(name="Evil plans")

        conspirators_group = Group.objects.create(name="Evil conspirators")
        conspirators_group.permissions.add(admin_permission)
        GroupCollectionPermission.objects.create(
            group=conspirators_group,
            collection=self.evil_plans_collection,
            permission=add_doc_permission
        )

        user = get_user_model().objects.create_user(
            username='moriarty',
            email='moriarty@example.com',
            password='password'
        )
        user.groups.add(conspirators_group)

        self.client.login(username='moriarty', password='password')

    def test_simple(self):
        response = self.client.get(reverse('wagtailreports:chooser_upload'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailreports/chooser/chooser.html')
        self.assertTemplateUsed(response, 'wagtailreports/chooser/chooser.js')

        # user only has access to one collection -> should not see the collections field
        self.assertNotContains(response, 'id_collection')

    def test_chooser_view(self):
        # The main chooser view also includes the form, so need to test there too
        response = self.client.get(reverse('wagtailreports:chooser'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailreports/chooser/chooser.html')
        self.assertTemplateUsed(response, 'wagtailreports/chooser/chooser.js')

        # user only has access to one collection -> should not see the collections field
        self.assertNotContains(response, 'id_collection')

    def test_post(self):
        # Build a fake file
        fake_file = ContentFile(b("A boring example report"))
        fake_file.name = 'test.txt'

        # Submit
        post_data = {
            'title': "Test report",
            'file': fake_file,
        }
        response = self.client.post(reverse('wagtailreports:chooser_upload'), post_data)

        # Check that the response is a javascript file saying the report was chosen
        self.assertTemplateUsed(response, 'wagtailreports/chooser/report_chosen.js')
        self.assertContains(response, "modal.respond('reportChosen'")

        # Report should be created
        report = models.Report.objects.filter(title="Test report")
        self.assertTrue(report.exists())

        # Report should be in the 'evil plans' collection
        self.assertEqual(report.get().collection, self.evil_plans_collection)


class TestUsageCount(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.login()

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_unused_report_usage_count(self):
        report = models.Report.objects.get(id=1)
        self.assertEqual(report.get_usage().count(), 0)

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_used_report_usage_count(self):
        report = models.Report.objects.get(id=1)
        page = EventPage.objects.get(id=4)
        event_page_related_link = EventPageRelatedLink()
        event_page_related_link.page = page
        event_page_related_link.link_report = doc
        event_page_related_link.save()
        self.assertEqual(report.get_usage().count(), 1)

    def test_usage_count_does_not_appear(self):
        report = models.Report.objects.get(id=1)
        page = EventPage.objects.get(id=4)
        event_page_related_link = EventPageRelatedLink()
        event_page_related_link.page = page
        event_page_related_link.link_report = doc
        event_page_related_link.save()
        response = self.client.get(reverse('wagtailreports:edit',
                                           args=(1,)))
        self.assertNotContains(response, 'Used 1 time')

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_usage_count_appears(self):
        report = models.Report.objects.get(id=1)
        page = EventPage.objects.get(id=4)
        event_page_related_link = EventPageRelatedLink()
        event_page_related_link.page = page
        event_page_related_link.link_report = doc
        event_page_related_link.save()
        response = self.client.get(reverse('wagtailreports:edit',
                                           args=(1,)))
        self.assertContains(response, 'Used 1 time')

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_usage_count_zero_appears(self):
        response = self.client.get(reverse('wagtailreports:edit',
                                           args=(1,)))
        self.assertContains(response, 'Used 0 times')


class TestGetUsage(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.login()

    def test_report_get_usage_not_enabled(self):
        report = models.Report.objects.get(id=1)
        self.assertEqual(list(report.get_usage()), [])

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_unused_report_get_usage(self):
        report = models.Report.objects.get(id=1)
        self.assertEqual(list(report.get_usage()), [])

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_used_report_get_usage(self):
        report = models.Report.objects.get(id=1)
        page = EventPage.objects.get(id=4)
        event_page_related_link = EventPageRelatedLink()
        event_page_related_link.page = page
        event_page_related_link.link_report = doc
        event_page_related_link.save()
        self.assertTrue(issubclass(Page, type(report.get_usage()[0])))

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_usage_page(self):
        report = models.Report.objects.get(id=1)
        page = EventPage.objects.get(id=4)
        event_page_related_link = EventPageRelatedLink()
        event_page_related_link.page = page
        event_page_related_link.link_report = doc
        event_page_related_link.save()
        response = self.client.get(reverse('wagtailreports:report_usage',
                                           args=(1,)))
        self.assertContains(response, 'Christmas')

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_usage_page_no_usage(self):
        response = self.client.get(reverse('wagtailreports:report_usage',
                                           args=(1,)))
        # There's no usage so there should be no table rows
        self.assertRegex(response.content, b'<tbody>(\s|\n)*</tbody>')


class TestEditOnlyPermissions(TestCase, WagtailTestUtils):
    def setUp(self):
        # Build a fake file
        fake_file = ContentFile(b("A boring example report"))
        fake_file.name = 'test.txt'

        self.root_collection = Collection.get_first_root_node()
        self.evil_plans_collection = self.root_collection.add_child(name="Evil plans")
        self.nice_plans_collection = self.root_collection.add_child(name="Nice plans")

        # Create a report to edit
        self.report = models.Report.objects.create(
            title="Test report", file=fake_file, collection=self.nice_plans_collection
        )

        # Create a user with change_report permission but not add_report
        user = get_user_model().objects.create_user(
            username='changeonly',
            email='changeonly@example.com',
            password='password'
        )
        change_permission = Permission.objects.get(
            content_type__app_label='wagtailreports', codename='change_report'
        )
        admin_permission = Permission.objects.get(
            content_type__app_label='wagtailadmin', codename='access_admin'
        )
        self.changers_group = Group.objects.create(name='Report changers')
        GroupCollectionPermission.objects.create(
            group=self.changers_group, collection=self.root_collection,
            permission=change_permission
        )
        user.groups.add(self.changers_group)

        user.user_permissions.add(admin_permission)
        self.assertTrue(self.client.login(username='changeonly', password='password'))

    def test_get_index(self):
        response = self.client.get(reverse('wagtailreports:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailreports/reports/index.html')

        # user should not get an "Add a report" button
        self.assertNotContains(response, "Add a report")

        # user should be able to see reports not owned by them
        self.assertContains(response, "Test report")

    def test_search(self):
        response = self.client.get(reverse('wagtailreports:index'), {'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query_string'], "Hello")

    def test_get_add(self):
        response = self.client.get(reverse('wagtailreports:add'))
        # permission should be denied
        self.assertRedirects(response, reverse('wagtailadmin_home'))

    def test_get_edit(self):
        response = self.client.get(reverse('wagtailreports:edit', args=(self.report.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailreports/reports/edit.html')

        # reports can only be moved to collections you have add permission for,
        # so the 'collection' field is not available here
        self.assertNotContains(response, '<label for="id_collection">')

        # if the user has add permission on a different collection,
        # they should have option to move the report
        add_permission = Permission.objects.get(
            content_type__app_label='wagtailreports', codename='add_report'
        )
        GroupCollectionPermission.objects.create(
            group=self.changers_group, collection=self.evil_plans_collection,
            permission=add_permission
        )
        response = self.client.get(reverse('wagtailreports:edit', args=(self.report.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<label for="id_collection">')
        self.assertContains(response, 'Nice plans')
        self.assertContains(response, 'Evil plans')

    def test_post_edit(self):
        # Submit title change
        response = self.client.post(
            reverse('wagtailreports:edit', args=(self.report.id,)), {
                'title': "Test report changed!",
                'file': '',
            }
        )

        # User should be redirected back to the index
        self.assertRedirects(response, reverse('wagtailreports:index'))

        # Report title should be changed
        self.assertEqual(
            models.Report.objects.get(id=self.report.id).title,
            "Test report changed!"
        )

        # collection should be unchanged
        self.assertEqual(
            models.Report.objects.get(id=self.report.id).collection,
            self.nice_plans_collection
        )

        # if the user has add permission on a different collection,
        # they should have option to move the report
        add_permission = Permission.objects.get(
            content_type__app_label='wagtailreports', codename='add_report'
        )
        GroupCollectionPermission.objects.create(
            group=self.changers_group, collection=self.evil_plans_collection,
            permission=add_permission
        )
        response = self.client.post(
            reverse('wagtailreports:edit', args=(self.report.id,)), {
                'title': "Test report changed!",
                'collection': self.evil_plans_collection.id,
                'file': '',
            }
        )
        self.assertEqual(
            models.Report.objects.get(id=self.report.id).collection,
            self.evil_plans_collection
        )

    def test_get_delete(self):
        response = self.client.get(reverse('wagtailreports:delete', args=(self.report.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailreports/reports/confirm_delete.html')
