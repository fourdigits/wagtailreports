from __future__ import absolute_import, unicode_literals

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils.encoding import force_text
from django.views.decorators.http import require_POST
from django.views.decorators.vary import vary_on_headers

from wagtail.wagtailadmin.utils import PermissionPolicyChecker
from wagtail.wagtailsearch.backends import get_search_backends

from ..forms import get_report_form
from ..models import get_report_model
from ..permissions import permission_policy

permission_checker = PermissionPolicyChecker(permission_policy)


@permission_checker.require('add')
@vary_on_headers('X-Requested-With')
def add(request):
    Report = get_report_model()
    ReportForm = get_report_form(Report)

    if request.method == 'POST':
        if not request.is_ajax():
            return HttpResponseBadRequest("Cannot POST to this view without AJAX")

        # Build a form for validation
        form = ReportForm(request.POST, user=request.user)

        if form.is_valid():
            # Save it
            report = form.save(commit=False)
            report.created_by_user = request.user
            report.save()

            # Success! Send back an edit form for this report to the user
            return JsonResponse({
                'success': True,
                'report_id': int(report.id),
                'form': render_to_string('wagtailreports/multiple/edit_form.html', {
                    'report': report,
                    'form': ReportMultiForm(
                        instance=report, prefix='report-%d' % report.id, user=request.user
                    ),
                }, request=request),
            })
        else:
            # Validation error
            return JsonResponse({
                'success': False,

                # https://github.com/django/django/blob/stable/1.6.x/django/forms/util.py#L45
                'error_message': '\n'.join(['\n'.join([force_text(i) for i in v]) for k, v in form.errors.items()]),
            })
    else:
        form = ReportForm(user=request.user)

    return render(request, 'wagtailreports/multiple/add.html', {
        'help_text': form.fields['file'].help_text,
    })


@require_POST
def edit(request, report_id, callback=None):
    Report = get_report_model()
    ReportForm = get_report_form(Report)

    report = get_object_or_404(Report, id=report_id)

    if not request.is_ajax():
        return HttpResponseBadRequest("Cannot POST to this view without AJAX")

    if not permission_policy.user_has_permission_for_instance(request.user, 'change', report):
        raise PermissionDenied

    form = ReportForm(request.POST, instance=report, user=request.user)

    if form.is_valid():
        form.save()

        # Reindex the report to make sure all tags are indexed
        for backend in get_search_backends():
            backend.add(report)

        return JsonResponse({
            'success': True,
            'report_id': int(report_id),
        })
    else:
        return JsonResponse({
            'success': False,
            'report_id': int(report_id),
            'form': render_to_string('wagtailreports/multiple/edit_form.html', {
                'report': report,
                'form': form,
            }, request=request),
        })


@require_POST
def delete(request, report_id):
    Report = get_report_model()

    report = get_object_or_404(Report, id=report_id)

    if not request.is_ajax():
        return HttpResponseBadRequest("Cannot POST to this view without AJAX")

    if not permission_policy.user_has_permission_for_instance(request.user, 'delete', report):
        raise PermissionDenied

    report.delete()

    return JsonResponse({
        'success': True,
        'report_id': int(report_id),
    })
