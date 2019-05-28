#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 19 16:15:35 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import re
import logging

from django.db.models import Q
from django.utils.text import Truncator

from image_validation import validation
from image_validation.static_parameters import ruleset_filename as \
    IMAGE_RULESET

from image_app.models import Name

# Get an instance of a logger
logger = logging.getLogger(__name__)


class MetaDataValidation():
    """A class to deal with IMAGE-ValidationTool ruleset objects"""

    ruleset = None

    def __init__(self, ruleset_filename=IMAGE_RULESET):
        self.read_in_ruleset(ruleset_filename)

    def read_in_ruleset(self, ruleset_filename):
        self.ruleset = validation.read_in_ruleset(ruleset_filename)

    def check_usi_structure(self, record):
        """Check data against USI rules"""

        # this function need its input as a list
        return validation.check_usi_structure(record)

    def check_ruleset(self):
        """Check ruleset"""

        return validation.check_ruleset(self.ruleset)

    def check_duplicates(self, record):
        """Check duplicates in data"""

        return validation.check_duplicates(record)

    def validate(self, record):
        """Check attributes for record"""

        # this validated in general way
        result = self.ruleset.validate(record)

        # this validate context (attributes that depends on another one)
        # TODO: context validation changed. Now it can evaluate relationships
        # see validation.context_validation for more help
        result = validation.context_validation(record, result, [])

        return result


class ValidationSummary():
    """A class to deal with error messages and submission"""

    def __init__(self, submission_obj):
        """Istantiate a report object from Submission"""

        # get all names belonging to this submission
        self.names = Name.objects.select_related(
                "validationresult",
                "animal",
                "sample").filter(
                    submission=submission_obj)

        # here I will have 5 queries, each one executed when calling count
        # or when iterating queryset

        # count animal and samples
        self.n_animals = self.names.filter(animal__isnull=False).count()
        self.n_samples = self.names.filter(sample__isnull=False).count()

        logger.debug("Got %s animal and %s samples in total" % (
            self.n_animals, self.n_samples))

        # count animal and samples with unknown validation
        self.n_animal_unknown = self.names.filter(
            animal__isnull=False, validationresult__isnull=True).count()
        self.n_sample_unknown = self.names.filter(
            sample__isnull=False, validationresult__isnull=True).count()

        logger.debug("Got %s animal and %s samples with unknown validation" % (
            self.n_animal_unknown, self.n_sample_unknown))

        # filter names which have errors
        self.errors = self.names.exclude(
            Q(validationresult__status="Pass") |
            Q(validationresult__isnull=True)
        )

        # count animal and samples with issues
        self.n_animal_issues = self.errors.filter(animal__isnull=False).count()
        self.n_sample_issues = self.errors.filter(sample__isnull=False).count()

        logger.debug("Got %s animal and %s samples with issues" % (
            self.n_animal_issues, self.n_sample_issues))

        # setting patterns
        self.pattern1 = re.compile(
            r"<([^>]*)> of field (.*) \bis \b(.*) for Record")

        self.pattern2 = re.compile(
            r"(.*) for the field (.*) \which \b(.*) for Record")

        self.pattern3 = re.compile(
            r"Provided value (.*) (does not match to the provided ontology)")

        # setting report dictionary
        self.report = {}

    def process_errors(self):
        """Process errors and gives hints"""

        # resetting report dictionary
        self.report = {}

        # TODO: track passed objects in report
        for error in self.errors:
            if not hasattr(error, 'validationresult'):
                logger.debug("Ignoring %s" % (error))
                continue

            for message in error.validationresult.messages:
                if (self.parse1(message, error.id) or
                        self.parse2(message, error.id) or
                        self.parse3(message, error.id)):
                    logger.debug("Processed message: %s" % (message))
                else:
                    logger.error("Cannot parse: '%s'" % message)

                    # assign those values to report
                    key = ("unmanaged", Truncator(message).words(10))
                    self.__update_report(key, error.id)

            # block error message

        return self.report

    def parse1(self, message, error_id):
        match = re.search(self.pattern1, message)

        if match:
            value, field, reason = match.groups()
            logger.debug("parse1: Got '{}','{}' and '{}'".format(
                    value, field, reason))

            key = (field, reason)
            self.__update_report(key, error_id)

            return True

        else:
            return False

    def parse2(self, message, error_id):
        match = re.search(self.pattern2, message)

        if match:
            reason, field, field_type = match.groups()
            logger.debug("parse2: Got '{}','{}' and '{}'".format(
                    reason, field, field_type))

            key = (field, reason)
            self.__update_report(key, error_id)

            return True

        else:
            return False

    def parse3(self, message, error_id):
        match = re.search(self.pattern3, message)

        if match:
            value, reason = match.groups()
            logger.debug("parse3: Got '{}' and '{}'".format(
                    value, reason))

            key = (value, reason)
            self.__update_report(key, error_id)

            return True

        else:
            return False

    def __update_report(self, key, error_id):
        if key in self.report:
            self.report[key]['count'] += 1
            self.report[key]['ids'] += [error_id]

        else:
            self.report[key] = {'count': 1, 'ids': [error_id]}
