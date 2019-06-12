#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 19 16:15:35 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import json
import logging
import requests

from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from image_validation import validation, ValidationResult
from image_validation.static_parameters import ruleset_filename as \
    IMAGE_RULESET

from common.constants import BIOSAMPLE_URL
from image_app.models import Name
from biosample.helpers import parse_image_alias, get_model_object

# Get an instance of a logger
logger = logging.getLogger(__name__)


# a class to deal with temporary issues from EBI servers
class OntologyCacheError(Exception):
    """Identifies temporary issues with EBI servers and
    image_validation.use_ontology.OntologyCache objects"""


# a class to deal with errors in ruleset (that are not user errors but
# errors within InjectTool and image_validation library)
class RulesetError(Exception):
    """Indentifies errors in ruleset"""


class MetaDataValidation():
    """A class to deal with IMAGE-ValidationTool ruleset objects"""

    ruleset = None

    def __init__(self, ruleset_filename=IMAGE_RULESET):
        self.read_in_ruleset(ruleset_filename)

        # check validation rules
        ruleset_errors = self.check_ruleset()

        if ruleset_errors != []:
            raise RulesetError(
                "Error with ruleset: %s" % "; ".join(ruleset_errors))

    def read_in_ruleset(self, ruleset_filename):
        try:
            self.ruleset = validation.read_in_ruleset(ruleset_filename)

        except json.JSONDecodeError as message:
            logger.error(
                "Error with 'https://www.ebi.ac.uk/ols/api/': %s" % (
                    str(message)))

            raise OntologyCacheError(
                "Issue with 'https://www.ebi.ac.uk/ols/api/'")

    def check_usi_structure(self, record: object) -> object:
        """Check data against USI rules"""

        # this function need its input as a list
        return validation.check_usi_structure(record)

    def check_ruleset(self):
        """Check ruleset"""

        return validation.check_ruleset(self.ruleset)

    def check_duplicates(self, record):
        """Check duplicates in data"""

        return validation.check_duplicates(record)

    def check_biosample_id_target(
            self, biosample_id, record_id, record_result):

        """
        Check if a target biosample_id exists or not. If it is present, ok.
        Otherwise a ValidationResultColumn with a warning

        Args:
            biosample_id (str): the desidered biosample id
            record_id (str): is the name of the object in the original data
                source
            record_result (ValidationResult.ValidationResultRecord):
                an image_validation result object

        Returns:
            ValidationResult.ValidationResultRecord: an updated
            image_validation object
        """

        url = f"{BIOSAMPLE_URL}/{biosample_id}"
        response = requests.get(url)
        status = response.status_code
        if status != 200:
            record_result.add_validation_result_column(
                ValidationResult.ValidationResultColumn(
                    "Warning",
                    f"Fail to retrieve record {biosample_id} from "
                    f"BioSamples as required in the relationship",
                    record_id,
                    'sampleRelationships'))

        return record_result

    def check_relationship(self, record, record_result):
        """
        Check relationship for an Animal/Sample record and return a list
        of dictionaries (to_biosample() objects) of related object

        Args:
            record (dict): An Animal/Sample.to_biosample() dictionary object
            record_result (ValidationResult.ValidationResultRecord):
                an image_validation result object

        Returns:
            list: a list of dictionaries of relate objects
            ValidationResult.ValidationResultRecord: an updated
            image_validation object
        """

        # get relationship from a to_biosample() dictionary object
        relationships = record.get('sampleRelationships', [])

        # as described in image_validation.Submission.Submission
        # same as record["title"], is the original name of the object id DS
        record_id = record['attributes']["Data source ID"][0]['value']

        # related objects (from UID goes here)
        related = []

        for relationship in relationships:
            if 'accession' in relationship:
                target = relationship['accession']

                # check biosample target and update record_result if necessary
                record_result = self.check_biosample_id_target(
                    target, record_id, record_result)

            # HINT: should I check aliases? they came from PK and are related
            # in the same submission. I can't have a sample without an animal
            # since animal is a foreign key of sample (which doesn't tolerate
            # NULL). Even mother and father are related through keys. If
            # missing, no information about mother and father could be
            # determined
            else:
                # could be a parent relationship for an animal, or the animal
                # where this sample comes from
                target = relationship['alias']

                # test for object existence in db. Use biosample.helpers
                # method to derive a model object from database, then get
                # its related data
                try:
                    material_obj = get_model_object(
                        *parse_image_alias(target))
                    related.append(material_obj.to_biosample())

                except ObjectDoesNotExist:
                    record_result.add_validation_result_column(
                        ValidationResult.ValidationResultColumn(
                            "Error",
                            f"Could not locate the referenced record {target}",
                            record_id, 'sampleRelationships'))

        return related, record_result

    def validate(self, record):
        """
        Check attributes for record by calling image_validation methods

        Args:
            record (dict): An Animal/Sample.to_biosample() dictionary object

        Returns:
            ValidationResult.ValidationResultRecord: an image_validation
            object
        """

        # this validated in general way
        result = self.ruleset.validate(record)

        # as defined in image_valdiation.Submission, I will skip further
        # validation check
        if result.get_overall_status() == "Error":
            logger.warning(
                "record: %s has errors. Skipping context validation" % (
                        record["title"]))

        else:
            # context validation evaluate relationships. Get them
            related, result = self.check_relationship(record, result)

            # this validate context (attributes that depends on another one)
            result = validation.context_validation(record, result, related)

        return result


class ValidationSummary:
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
