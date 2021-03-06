#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  5 11:39:34 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormView
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect

from common.constants import WAITING
from uid.models import Submission

from .forms import ValidateForm
from .tasks import ValidateTask

# Get an instance of a logger
logger = logging.getLogger(__name__)


class ValidateView(LoginRequiredMixin, FormView):
    form_class = ValidateForm
    template_name = 'validation/validate.html'
    submission_id = None

    def get_success_url(self):
        return reverse('submissions:detail', kwargs={
            'pk': self.submission_id})

    def form_valid(self, form):
        submission_id = form.cleaned_data['submission_id']
        submission = get_object_or_404(
            Submission,
            pk=submission_id,
            owner=self.request.user)

        # track submission id in order to render page
        self.submission_id = submission_id

        # check if I can validate object (statuses)
        if not submission.can_validate():
            # return super method (which calls get_success_url)
            logger.error(
                "Can't validate submission %s: current status is %s" % (
                    submission, submission.get_status_display()))

            return HttpResponseRedirect(self.get_success_url())

        submission.message = "waiting for data validation"
        submission.status = WAITING
        submission.save()

        # a valid submission start a task
        my_task = ValidateTask()
        res = my_task.delay(submission_id)
        logger.info(
            "Start validation process for %s with task %s" % (
                submission,
                res.task_id))

        return super(ValidateView, self).form_valid(form)
