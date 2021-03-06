#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 14 10:28:39 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

# --- import

import logging
import os
import shlex
import subprocess

from decouple import AutoConfig

from django.conf import settings

from common.constants import LOADED, ERROR, MISSING, UNKNOWN
from common.helpers import image_timedelta
from uid.helpers import get_or_create_obj, update_or_create_obj
from uid.models import (
    Animal, DictBreed, DictCountry, DictSex, DictSpecie, Sample,
    Submission, DictUberon)
from language.helpers import check_species_synonyms
from submissions.helpers import send_message
from validation.helpers import construct_validation_message
from validation.models import ValidationSummary

from .models import db_has_data as cryoweb_has_data
from .models import VAnimal, VBreedsSpecies, VVessels

# Get an instance of a logger
logger = logging.getLogger(__name__)


# --- check functions


# a function to detect if cryoweb species have synonyms or not
def check_species(country):
    """Check all cryoweb species for a synonym in a supplied language or
    the default one, ie: check_species(country). country is an
    uid.models.DictCountry.label"""

    # get all species using view
    words = VBreedsSpecies.get_all_species()

    # for logging purposes
    database_name = settings.DATABASES['cryoweb']['NAME']

    if len(words) == 0:
        raise CryoWebImportError(
            "You have no species in %s database" % database_name)

    # debug
    logger.debug("Got %s species from %s" % (words, database_name))

    # check if every word as a synonym (a specie)
    # (And create synonyms if don't exist)
    return check_species_synonyms(words, country, create=True)


# a function to test if I have all countries or not
def check_countries():
    """Check that all efabis countries have a dictionary object"""

    # get all countries
    countries = VBreedsSpecies.get_all_countries()

    countries_not_found = []

    for country in countries:
        if not DictCountry.objects.filter(label=country).exists():
            countries_not_found.append(country)

    return countries_not_found


# a function specific for cryoweb import path to ensure that all required
# fields in UID are present. There could be a function like this in others
# import paths
def check_UID(submission):
    """A function to ensure that UID is valid before data upload. Specific
    to the module where is called from"""

    logger.debug("Checking UID")

    # check that dict sex table contains data
    if len(DictSex.objects.all()) == 0:
        raise CryoWebImportError("You have to upload DictSex data")

    # test for specie synonyms in submission language or defaul one
    # otherwise, fill synonym table with new terms then throw exception
    if not check_species(submission.gene_bank_country):
        raise CryoWebImportError("Some species haven't a synonym!")

    # test for countries in UID
    countries_not_found = check_countries()

    if len(countries_not_found) > 0:
        raise CryoWebImportError(
            "Not all countries are loaded into database: "
            "check for '%s' in your dataset" % (countries_not_found)
        )

    # return a status
    return True


# A class to deal with cryoweb import errors
class CryoWebImportError(Exception):
    pass


# --- Upload data into cryoweb database
def upload_cryoweb(submission_id):
    """Imports backup into the cryoweb db

    This function uses the container's installation of psql to import a backup
    file into the "cryoweb" database. The imported backup file is
    the last inserted into the image's table uid_submission.

    :submission_id: the submission primary key
    """

    # define some useful variables
    database_name = settings.DATABASES['cryoweb']['NAME']

    # define a decouple config object
    config_dir = os.path.join(settings.BASE_DIR, 'image')
    config = AutoConfig(search_path=config_dir)

    # get a submission object
    submission = Submission.objects.get(pk=submission_id)

    # debug
    logger.info("Importing data into CryoWeb staging area")
    logger.debug("Got Submission %s" % (submission))

    # If cryoweb has data, update submission message and return exception:
    # maybe another process is running or there is another type of problem
    if cryoweb_has_data():
        logger.error("CryoWeb has data!")

        # update submission status
        submission.status = ERROR
        submission.message = "Error in importing data: Cryoweb has data"
        submission.save()

        # send async message
        send_message(submission)

        raise CryoWebImportError("Cryoweb has data!")

    # this is the full path in docker container
    fullpath = submission.get_uploaded_file_path()

    # define command line
    cmd_line = (
        "/usr/bin/psql -U {user} -h db {database} -v ON_ERROR_STOP=1".format(
            database=database_name, user='cryoweb_insert_only'))

    cmds = shlex.split(cmd_line)

    logger.debug("Executing: %s" % " ".join(cmds))

    try:
        result = subprocess.run(
            cmds,
            stdin=open(fullpath),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            env={'PGPASSWORD': config('CRYOWEB_INSERT_ONLY_PW')},
            encoding='utf8'
            )

    except Exception as exc:
        # save a message in database
        submission.status = ERROR
        submission.message = (
            "Error in importing data: Is '%s' a valid CryoWeb"
            " dump file?" % (
                os.path.split(submission.uploaded_file.name)[-1]))
        submission.save()

        # send async message
        send_message(submission)

        # debug
        logger.error("error in calling upload_cryoweb: %s" % (exc))

        return False

    n_of_statements = len(result.stdout.split("\n"))
    logger.debug("%s statement executed" % n_of_statements)

    if len(result.stderr) > 0:
        for line in result.stderr.split("\n"):
            logger.error(line)

    logger.info("{filename} uploaded into {database}".format(
        filename=submission.uploaded_file.name, database=database_name))

    return True


# --- Upload data from cryoweb to UID


def fill_uid_breeds(submission):
    """Fill UID DictBreed model. Require a submission instance"""

    logger.info("fill_uid_breeds() started")

    # get submission language
    language = submission.gene_bank_country.label

    for v_breed_specie in VBreedsSpecies.objects.all():
        # get specie. Since I need a dictionary tables, DictSpecie is
        # already filled
        specie = DictSpecie.get_by_synonym(
            synonym=v_breed_specie.ext_species,
            language=language)

        # get country for breeds. Ideally will be the same of submission,
        # since the Italian cryoweb is supposed to contains italian breeds.
        # however, it could be possible to store data from other contries
        country = DictCountry.objects.get(label=v_breed_specie.efabis_country)

        # create breed obj if necessary
        get_or_create_obj(
            DictBreed,
            supplied_breed=v_breed_specie.efabis_mcname,
            specie=specie,
            country=country)

    logger.info("fill_uid_breeds() completed")


def get_animal_specie_and_breed(v_animal, language):
    # get specie translated by dictionary
    specie = DictSpecie.get_by_synonym(
        synonym=v_animal.ext_species,
        language=language)

    logger.debug("Selected specie is %s" % (specie))

    # get breed name and country through VBreedsSpecies model
    efabis_mcname = v_animal.efabis_mcname
    efabis_country = v_animal.efabis_country

    # get a country object
    country = DictCountry.objects.get(label=efabis_country)

    # a breed could be specie/country specific
    breed = DictBreed.objects.get(
        supplied_breed=efabis_mcname,
        specie=specie,
        country=country)

    logger.debug("Selected breed is %s" % (breed))

    return specie, breed


def fill_uid_animals(submission):
    """Helper function to fill animal data in UID animal table"""

    # debug
    logger.info("called fill_uid_animals()")

    # get submission language
    language = submission.gene_bank_country.label

    # get male and female DictSex objects from database
    male = DictSex.objects.get(label="male")
    female = DictSex.objects.get(label="female")

    # cycle over animals
    for v_animal in VAnimal.objects.all():
        # getting specie and breed
        specie, breed = get_animal_specie_and_breed(v_animal, language)

        # get name for this animal and for mother and father
        logger.debug("Getting %s as my name" % (v_animal.ext_animal))

        logger.debug("Getting %s as father" % (v_animal.ext_sire))

        # get father or None
        father = Animal.objects.filter(
            name=v_animal.ext_sire,
            breed=breed,
            owner=submission.owner).first()

        logger.debug("Getting %s as mother" % (v_animal.ext_dam))

        # get mother or None
        mother = Animal.objects.filter(
            name=v_animal.ext_dam,
            breed=breed,
            owner=submission.owner).first()

        # determine sex. Check for values
        if v_animal.ext_sex == 'm':
            sex = male

        elif v_animal.ext_sex == 'f':
            sex = female

        else:
            raise CryoWebImportError(
                "Unknown sex '%s' for '%s'" % (v_animal.ext_sex, v_animal))

        # checking accuracy
        accuracy = MISSING

        # HINT: this will is not sufficent for validation, since we need also
        # birth location as a Text to have valid birth location. Cryoweb
        # with coordinates will always fail validation
        if v_animal.latitude and v_animal.longitude:
            accuracy = UNKNOWN

        # create a new object. Using defaults to avoid collisions when
        # updating data
        defaults = {
            'alternative_id': v_animal.db_animal,
            'sex': sex,
            'father': father,
            'mother': mother,
            'birth_date': v_animal.birth_dt,
            'birth_location_latitude': v_animal.latitude,
            'birth_location_longitude': v_animal.longitude,
            'birth_location_accuracy': accuracy,
            'description': v_animal.comment,
        }

        # Upate or create animal obj
        update_or_create_obj(
            Animal,
            name=v_animal.ext_animal,
            breed=breed,
            owner=submission.owner,
            submission=submission,
            defaults=defaults)

    # create a validation summary object and set all_count
    validation_summary = get_or_create_obj(
        ValidationSummary,
        submission=submission,
        type="animal")

    # reset counts
    validation_summary.reset_all_count()

    # debug
    logger.info("fill_uid_animals() completed")


def fill_uid_samples(submission):
    """Helper function to fill animal data in UID animal table"""

    # debug
    logger.info("called fill_uid_samples()")

    # get submission language
    language = submission.gene_bank_country.label

    for v_vessel in VVessels.objects.all():
        # get name for this sample
        name = v_vessel.ext_vessel

        # get the animal of this sample
        v_animal = v_vessel.get_animal()

        # getting specie and breed
        specie, breed = get_animal_specie_and_breed(v_animal, language)

        # get animal object using name
        animal = Animal.objects.get(
            name=v_animal.ext_animal,
            breed=breed,
            owner=submission.owner)

        # get a organism part. Organism parts need to be in lowercases
        organism_part = get_or_create_obj(
            DictUberon,
            label=v_vessel.get_organism_part().lower()
        )

        # derive animal age at collection. THis function deals with NULL valies
        animal_age_at_collection, time_units = image_timedelta(
            v_vessel.production_dt, v_animal.birth_dt)

        # create a new object. Using defaults to avoid collisions when
        # updating data
        defaults = {
            'alternative_id': v_vessel.db_vessel,
            'collection_date': v_vessel.production_dt,
            # 'protocol': v_vessel.get_protocol_name(),
            'organism_part': organism_part,
            'description': v_vessel.comment,
            'animal_age_at_collection': animal_age_at_collection,
            'animal_age_at_collection_units': time_units,
            # 'storage': v_vessel.ext_vessel_type,
        }

        update_or_create_obj(
            Sample,
            name=name,
            animal=animal,
            owner=submission.owner,
            submission=submission,
            defaults=defaults)

    # create a validation summary object and set all_count
    validation_summary = get_or_create_obj(
        ValidationSummary,
        submission=submission,
        type="sample")

    # reset counts
    validation_summary.reset_all_count()

    # debug
    logger.info("fill_uid_samples() completed")


def cryoweb_import(submission):
    """Import data from cryoweb stage database into UID

    :submission: a submission instance
    """

    # debug
    logger.info("Importing from cryoweb staging area")

    try:
        # check UID status. get an exception if database is not initialized
        check_UID(submission)

        # BREEDS
        fill_uid_breeds(submission)

        # ANIMALS
        fill_uid_animals(submission)

        # SAMPLES
        fill_uid_samples(submission)

    except Exception as exc:
        # save a message in database
        submission.status = ERROR
        submission.message = "Error in importing data: %s" % (str(exc))
        submission.save()

        # send async message
        send_message(submission)

        # debug
        logger.error("error in importing from cryoweb: %s" % (exc))
        logger.exception(exc)

        return False

    else:
        message = "Cryoweb import completed for submission: %s" % (
            submission.id)

        submission.message = message
        submission.status = LOADED
        submission.save()

        send_message(
            submission,
            validation_message=construct_validation_message(submission))

    logger.info("Import from staging area is complete")

    return True
