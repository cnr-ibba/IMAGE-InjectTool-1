#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 24 15:49:23 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import logging
import ast
import re
from django.core.exceptions import ObjectDoesNotExist

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.views import View
from django.views.generic import (
    CreateView, DetailView, ListView, UpdateView, DeleteView)
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse

from common.constants import (
    WAITING, ERROR, SUBMITTED, NEED_REVISION, CRYOWEB_TYPE, CRB_ANIM_TYPE,
    TIME_UNITS, VALIDATION_MESSAGES_ATTRIBUTES, SAMPLE_STORAGE,
    SAMPLE_STORAGE_PROCESSING, ACCURACIES)
from common.helpers import get_deleted_objects, uid2biosample
from common.views import OwnerMixin
from crbanim.tasks import ImportCRBAnimTask
from cryoweb.tasks import import_from_cryoweb

from image_app.models import Submission, Name, Animal, Sample, DictUberon, \
    DictDevelStage, DictPhysioStage, DictSex
from excel.tasks import ImportTemplateTask

from validation.helpers import construct_validation_message
from validation.models import ValidationSummary
from animals.tasks import BatchUpdateAnimals
from samples.tasks import BatchUpdateSamples

from .forms import SubmissionForm, ReloadForm

# Get an instance of a logger
logger = logging.getLogger(__name__)


class CreateSubmissionView(LoginRequiredMixin, CreateView):
    form_class = SubmissionForm
    model = Submission

    # template name is derived from model position and views type.
    # in this case, ir will be 'image_app/submission_form.html' so
    # i need to clearly specify it
    template_name = "submissions/submission_form.html"

    def form_invalid(self, form):
        messages.error(
            self.request,
            message="Please correct the errors below",
            extra_tags="alert alert-dismissible alert-danger")

        return super(CreateSubmissionView, self).form_invalid(form)

    # add user to this object
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.owner = self.request.user

        # I will have a different loading function accordingly with data type
        if self.object.datasource_type == CRYOWEB_TYPE:
            # update object and force status
            self.object.message = "waiting for data loading"
            self.object.status = WAITING
            self.object.save()

            # a valid submission start a task
            res = import_from_cryoweb.delay(self.object.pk)
            logger.info(
                "Start cryoweb importing process with task %s" % res.task_id)

        # I will have a different loading function accordingly with data type
        elif self.object.datasource_type == CRB_ANIM_TYPE:
            # update object and force status
            self.object.message = "waiting for data loading"
            self.object.status = WAITING
            self.object.save()

            # create a task
            my_task = ImportCRBAnimTask()

            # a valid submission start a task
            res = my_task.delay(self.object.pk)
            logger.info(
                "Start crbanim importing process with task %s" % res.task_id)

        else:
            # update object and force status
            self.object.message = "waiting for data loading"
            self.object.status = WAITING
            self.object.save()

            # create a task
            my_task = ImportTemplateTask()

            # a valid submission start a task
            res = my_task.delay(self.object.pk)
            logger.info(
                "Start template importing process with task %s" % res.task_id)

        # a redirect to self.object.get_absolute_url()
        return HttpResponseRedirect(self.get_success_url())


class MessagesSubmissionMixin(object):
    """Display messages in SubmissionViews"""

    # https://stackoverflow.com/a/45696442
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        # get the submission message
        message = self.submission.message

        # check if data are loaded or not
        if self.submission.status in [WAITING, SUBMITTED]:
            messages.warning(
                request=self.request,
                message=message,
                extra_tags="alert alert-dismissible alert-warning")

        elif self.submission.status in [ERROR, NEED_REVISION]:
            messages.error(
                request=self.request,
                message=message,
                extra_tags="alert alert-dismissible alert-danger")

        elif message is not None and message != '':
            messages.info(
                request=self.request,
                message=message,
                extra_tags="alert alert-dismissible alert-info")

        return data


class DetailSubmissionView(MessagesSubmissionMixin, OwnerMixin, DetailView):
    model = Submission
    template_name = "submissions/submission_detail.html"

    def get_context_data(self, **kwargs):
        # pass self.object to a new submission attribute in order to call
        # MessagesSubmissionMixin.get_context_data()
        self.submission = self.object

        # Call the base implementation first to get a context
        context = super(DetailSubmissionView, self).get_context_data(**kwargs)

        # add submission report to context
        validation_summary = construct_validation_message(self.submission)

        # HINT: is this computational intensive?
        context["validation_summary"] = validation_summary

        return context


class SubmissionValidationSummaryView(OwnerMixin, DetailView):
    model = Submission
    template_name = "submissions/submission_validation_summary.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        summary_type = self.kwargs['type']
        try:
            validation_summary = self.object.validationsummary_set\
                .get(type=summary_type)
            context['validation_summary'] = validation_summary
            editable = list()
            for message in validation_summary.messages:
                message = ast.literal_eval(message)
                if uid2biosample(message['offending_column']) in \
                        [val for sublist in VALIDATION_MESSAGES_ATTRIBUTES for
                         val in sublist]:
                    editable.append(True)
                else:
                    editable.append(False)
            context['editable'] = editable
        except ObjectDoesNotExist:
            context['validation_summary'] = None
        context['submission'] = Submission.objects.get(pk=self.kwargs['pk'])
        return context


class SubmissionValidationSummaryFixErrorsView(OwnerMixin, ListView):
    template_name = "submissions/submission_validation_summary_fix_errors.html"

    def get_queryset(self):
        self.summary_type = self.kwargs['type']
        self.submission = Submission.objects.get(pk=self.kwargs['pk'])
        self.validation_summary = ValidationSummary.objects.get(
            submission=self.submission, type=self.summary_type)
        self.message = ast.literal_eval(self.validation_summary.messages[
                                            int(self.kwargs['message_counter'])
                                        ])
        self.offending_column = uid2biosample(
            self.message['offending_column'])
        if re.search(".* for field .* is not in the valid units list (.*)",
                     self.message['message']) or re.search(
            "One of .* need to be present for the field .*",
            self.message['message']):
            self.show_units = True
            if self.offending_column == 'animal_age_at_collection_units':
                self.offending_column += "_units"
                self.units = [unit.name for unit in TIME_UNITS]
            elif self.offending_column == 'preparation_interval_units':
                self.units = [unit.name for unit in TIME_UNITS]
        elif re.search(".* of field .* is not in the valid values list .*",
                       self.message['message']):
            self.show_units = True
            if self.offending_column == 'storage':
                self.units = [unit.name for unit in SAMPLE_STORAGE]
            elif self.offending_column == 'storage_processing':
                self.units = [unit.name for unit in SAMPLE_STORAGE_PROCESSING]
            elif self.offending_column == 'collection_place_accuracy':
                self.units = [unit.name for unit in ACCURACIES]
            elif self.offending_column == 'birth_location_accuracy':
                self.units = [unit.name for unit in ACCURACIES]
        elif re.search("Not valid ontology term .* in field .*",
                       self.message['message']):
            self.show_units = False
            self.units = None
            if self.offending_column == 'organism_part':
                self.offending_column = 'term'
                self.summary_type = 'dictuberon'
                return DictUberon.objects.filter(id__in=[Sample.objects.get(
                    pk=self.message['ids'][0]).organism_part_id])
            elif self.offending_column == 'developmental_stage':
                self.offending_column = 'term'
                self.summary_type = 'dictdevelstage'
                return DictDevelStage.objects.filter(id__in=[Sample.objects.get(
                    pk=self.message['ids'][0]).developmental_stage_id])
            elif self.offending_column == 'physiological_stage':
                self.offending_column = 'term'
                self.summary_type = 'dictphysiostage'
                return DictPhysioStage.objects.filter(id__in=[
                    Sample.objects.get(
                        pk=self.message['ids'][0]).physiological_stage_id])
            elif self.offending_column == 'sex':
                self.offending_column = 'term'
                self.summary_type = 'dictsex'
                return DictSex.objects.filter(id__in=[Animal.objects.get(
                    pk=self.message['ids'][0]).sex_id])
        else:
            self.show_units = False
            self.units = None
        if self.summary_type == 'animal':
            return Animal.objects.filter(id__in=self.message['ids'])
        elif self.summary_type == 'sample':
            return Sample.objects.filter(id__in=self.message['ids'])

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(
            SubmissionValidationSummaryFixErrorsView, self
        ).get_context_data(**kwargs)

        # add submission to context
        context["message"] = self.message
        context["type"] = self.summary_type
        context['attribute_to_edit'] = self.offending_column
        for attributes in VALIDATION_MESSAGES_ATTRIBUTES:
            if self.offending_column in attributes:
                context['attributes_to_show'] = [
                    attr for attr in attributes if attr != self.offending_column
                ]
        context['submission'] = self.submission
        context['error_type'] = 'coordinate_check'
        context['show_units'] = self.show_units
        if self.units:
            context['units'] = self.units
        return context


# a detail view since I need to operate on a submission object
# HINT: rename to a more informative name?
class EditSubmissionView(MessagesSubmissionMixin, OwnerMixin, ListView):
    template_name = "submissions/submission_edit.html"
    paginate_by = 10

    def get_queryset(self):
        """Subsetting names relying submission id"""
        self.submission = get_object_or_404(
            Submission,
            pk=self.kwargs['pk'],
            owner=self.request.user)

        # unknown animals should be removed from a submission. They have no
        # data in animal table nor sample
        return Name.objects.select_related(
                "validationresult",
                "animal",
                "sample").filter(
            Q(submission=self.submission) & (
                Q(animal__isnull=False) | Q(sample__isnull=False))
            ).order_by('id')

    def dispatch(self, request, *args, **kwargs):
        handler = super(EditSubmissionView, self).dispatch(
                request, *args, **kwargs)

        # here I've done get_queryset. Check for submission status
        if hasattr(self, "submission") and not self.submission.can_edit():
            message = "Cannot edit submission: current status is: %s" % (
                    self.submission.get_status_display())

            logger.warning(message)
            messages.warning(
                request=self.request,
                message=message,
                extra_tags="alert alert-dismissible alert-warning")

            return redirect(self.submission.get_absolute_url())

        return handler

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(EditSubmissionView, self).get_context_data(**kwargs)

        # add submission to context
        context["submission"] = self.submission

        return context


class ListSubmissionsView(OwnerMixin, ListView):
    model = Submission
    template_name = "submissions/submission_list.html"
    ordering = ['-created_at']
    paginate_by = 10


class ReloadSubmissionView(OwnerMixin, UpdateView):
    form_class = ReloadForm
    model = Submission
    template_name = 'submissions/submission_reload.html'

    def form_invalid(self, form):
        messages.error(
            self.request,
            message="Please correct the errors below",
            extra_tags="alert alert-dismissible alert-danger")

        return super(ReloadSubmissionView, self).form_invalid(form)

    def form_valid(self, form):
        self.object = form.save(commit=False)

        # update object and force status
        self.object.message = "waiting for data loading"
        self.object.status = WAITING
        self.object.save()

        # HINT: can I change datasource type?

        # call the proper method
        if self.object.datasource_type == CRYOWEB_TYPE:
            # a valid submission start a task
            res = import_from_cryoweb.delay(self.object.pk)
            logger.info(
                "Start cryoweb reload process with task %s" % res.task_id)

        elif self.object.datasource_type == CRB_ANIM_TYPE:
            # a valid submission start a task
            my_task = ImportCRBAnimTask()

            # a valid submission start a task
            res = my_task.delay(self.object.pk)
            logger.info(
                "Start crbanim reload process with task %s" % res.task_id)

        else:
            # a valid submission start a task
            my_task = ImportTemplateTask()

            # a valid submission start a task
            res = my_task.delay(self.object.pk)
            logger.info(
                "Start template reload process with task %s" % res.task_id)

        # a redirect to self.object.get_absolute_url()
        return HttpResponseRedirect(self.get_success_url())


class DeleteSubmissionView(OwnerMixin, DeleteView):
    model = Submission
    template_name = "submissions/submission_confirm_delete.html"
    success_url = reverse_lazy('image_app:dashboard')

    def dispatch(self, request, *args, **kwargs):
        handler = super(DeleteSubmissionView, self).dispatch(
                request, *args, **kwargs)

        # here I've done get_queryset. Check for submission status
        if hasattr(self, "object") and not self.object.can_edit():
            message = "Cannot delete %s: submission status is: %s" % (
                    self.object, self.object.get_status_display())

            logger.warning(message)
            messages.warning(
                request=self.request,
                message=message,
                extra_tags="alert alert-dismissible alert-warning")

            return redirect(self.object.get_absolute_url())

        return handler

    # https://stackoverflow.com/a/39533619/4385116
    def get_context_data(self, **kwargs):
        # determining related objects
        # TODO: move this to a custom AJAX call
        context = super().get_context_data(**kwargs)

        deletable_objects, model_count, protected = get_deleted_objects(
            [self.object])

        # get only sample and animals from model_count
        info_deleted = {}

        items = ['animals', 'samples']

        for item in items:
            if item in model_count:
                info_deleted[item] = model_count[item]

        # add info to context
        context['info_deleted'] = dict(info_deleted).items()

        return context

    # https://ccbv.co.uk/projects/Django/1.11/django.views.generic.edit/DeleteView/#delete
    def delete(self, request, *args, **kwargs):
        """
        Add a message after calling base delete method
        """

        httpresponseredirect = super().delete(request, *args, **kwargs)

        message = "Submission %s was successfully deleted" % self.object.title
        logger.info(message)

        messages.info(
            request=self.request,
            message=message,
            extra_tags="alert alert-dismissible alert-info")

        return httpresponseredirect


class FixValidation(View, OwnerMixin):
    def post(self, request, **kwargs):
        # Fetch all required ids from input names and use it as keys
        keys_to_fix = dict()
        for key_to_fix in request.POST:
            if 'to_edit' in key_to_fix:
                keys_to_fix[
                    int(re.search('to_edit(.*)', key_to_fix).groups()[0])] \
                    = request.POST[key_to_fix]

        pk = self.kwargs['pk']
        record_type = self.kwargs['record_type']
        attribute_to_edit = self.kwargs['attribute_to_edit']

        submission = Submission.objects.get(pk=pk)
        submission.message = "waiting for data updating"
        submission.status = WAITING
        submission.save()

        # Update validation summary
        if record_type == 'dictuberon' or record_type == 'dictdevelstage' or \
                record_type == 'dictphysiostage':
            validation_summary_type = 'sample'
        elif record_type == 'dictsex':
            validation_summary_type = 'animal'
        else:
            validation_summary_type = record_type
        summary_obj, created = ValidationSummary.objects.get_or_create(
            submission=submission, type=validation_summary_type)
        summary_obj.submission = submission
        summary_obj.reset()

        # create a task
        if record_type == 'animal' or record_type == 'dictsex':
            my_task = BatchUpdateAnimals()
        elif record_type == 'sample' or record_type == 'dictuberon' or \
                record_type == 'dictdevelstage' or \
                record_type == 'dictphysiostage':
            my_task = BatchUpdateSamples()
        else:
            return HttpResponseRedirect(
                reverse('submissions:detail', args=(pk,)))

        # a valid submission start a task
        res = my_task.delay(pk, keys_to_fix, attribute_to_edit, record_type)
        logger.info(
            "Start fix validation process with task %s" % res.task_id)
        return HttpResponseRedirect(reverse('submissions:detail', args=(pk,)))
