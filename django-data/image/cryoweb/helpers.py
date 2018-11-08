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

from django.conf import settings

from decouple import AutoConfig
from image_app.models import (
    Animal, DictBreed, DictCountry, DictSex, DictSpecie, Name, Sample,
    Submission, ACCURACIES, STATUSES)
from language.models import SpecieSynonim

from .models import db_has_data as cryoweb_has_data
from .models import VAnimal, VBreedsSpecies, VTransfer, VVessels

# Get an instance of a logger
logger = logging.getLogger(__name__)

# Set Submission statuses
LOADED = STATUSES.get_value('loaded')
ERROR = STATUSES.get_value('error')

# get accuracy levels
MISSING = ACCURACIES.get_value('missing')
UNKNOWN = ACCURACIES.get_value('unknown')


# --- check functions
# a function to detect if cryoweb species have synonims or not
def check_species(language):
    """Check specie for a language, ie: check_species(language='Germany').
    Language is image_app.models.DictCountry.label"""

    # get all species using view
    species = VBreedsSpecies.get_all_species()

    # for logging purposes
    database_name = settings.DATABASES['cryoweb']['NAME']

    if len(species) == 0:
        raise CryoWebImportError(
            "You have no species in %s database" % database_name)

    # debug
    logger.debug("Got %s species from %s" % (species, database_name))

    # get a language. Must be present in database (it shuld be, since I
    # select it through a dropdown list when creating a submission)
    country = DictCountry.objects.get(label=language)

    # get a queryset for each
    synonims = SpecieSynonim.objects.filter(
        word__in=species, language=country, dictspecie__isnull=False)

    # check that numbers are equal
    if len(species) == synonims.count():
        logger.debug("Each species has a synonim in %s language" % (language))
        return True

    elif len(species) > synonims.count():
        logger.warning(
            "Some species haven't a synonim for language: '%s'!" % (language))
        logger.debug("Following terms lack of synonim:")

        for specie in species:
            if not SpecieSynonim.objects.filter(
                    word=specie,
                    language=country,
                    dictspecie__isnull=False).exists():
                logger.debug("%s has no specie related" % (specie))

                # add specie in speciesynonym table
                synonym, created = SpecieSynonim.objects.get_or_create(
                    word=specie,
                    language=country)

                if created:
                    logger.debug("Added synonym %s" % (synonym))

        # check_specie fails, since there are words not related to species
        return False

    # may I see this case? For instance when filling synonims?
    else:
        raise NotImplementedError("Not implemented")


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

    # HINT: if I don't have a synonim, what I need to do?
    if not check_species(submission.gene_bank_country.label):
        raise CryoWebImportError("Some species haven't a synonim!")

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
    the last inserted into the image's table image_app_submission.

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
    logger.info("Importing data into cryoweb staging area")
    logger.debug("Got Submission %s" % (submission))

    # If cryoweb has data, update submission message and return exception:
    # maybe another process is running or there is another type of problem
    if cryoweb_has_data():
        logger.error("Cryoweb has data!")

        # update submission status
        submission.status = ERROR
        submission.message = "Error in importing data: Cryoweb has data"
        submission.save()

        raise CryoWebImportError("Cryoweb has data!")

    # this is the full path in docker container
    fullpath = submission.get_uploaded_file_path()

    # define command line
    cmd_line = "/usr/bin/psql -U {user} -h db {database}".format(
        database=database_name, user='cryoweb_insert_only')

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
        submission.message = "Error in importing data: %s" % (str(exc))
        submission.save()

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

    logger.debug("fill_uid_breeds() started")

    # get submission language
    language = submission.gene_bank_country.label

    for v_breed_specie in VBreedsSpecies.objects.all():
        # get specie. Since I need a dictionary tables, DictSpecie is
        # already filled
        specie = DictSpecie.get_by_synonim(
            synonim=v_breed_specie.ext_species,
            language=language)

        # get country. Maybe DictCountry will be related to dictionary table
        # for now, I can create an object or not
        # TODO: define if is a dictionary related term or not
        # use language for consistency with submission
        country, created = DictCountry.objects.get_or_create(
            label=language)

        if created:
            logger.info("Created %s" % country)

        else:
            logger.debug("Found %s" % country)

        breed, created = DictBreed.objects.get_or_create(
            supplied_breed=v_breed_specie.efabis_mcname,
            specie=specie,
            country=country)

        if created:
            logger.info("Created %s" % breed)

        else:
            logger.debug("Found %s" % breed)

    logger.debug("fill_uid_breeds() completed")


def fill_uid_names(submission):
    """Read VTransfer Views and fill name table"""

    # debug
    logger.info("called fill_uid_names()")

    # get all Vtransfer object
    for v_tranfer in VTransfer.objects.all():
        # no name manipulation. If two objects are indentical, there's no
        # duplicates.
        # HINT: The ramon example will be a issue in validation step
        name, created = Name.objects.get_or_create(
            name=v_tranfer.get_fullname(),
            submission=submission,
            owner=submission.owner)

        if created:
            logger.info("Created %s" % name)

        else:
            logger.debug("Found %s" % name)

    logger.info("fill_uid_names() completed")


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
        # get specie translated by dictionary
        specie = DictSpecie.get_by_synonim(
            synonim=v_animal.ext_species,
            language=language)

        # get breed name through VBreedsSpecies model
        efabis_mcname = v_animal.efabis_mcname
        breed = DictBreed.objects.get(
            supplied_breed=efabis_mcname,
            specie=specie)

        # get name for this animal and for mother and father
        logger.debug("Getting %s as my name" % (v_animal.ext_animal))
        name = Name.objects.get(
            name=v_animal.ext_animal, submission=submission)

        logger.debug("Getting %s as father" % (v_animal.ext_sire))
        father = Name.objects.get(
            name=v_animal.ext_sire, submission=submission)

        logger.debug("Getting %s as mother" % (v_animal.ext_dam))
        mother = Name.objects.get(
            name=v_animal.ext_dam, submission=submission)

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

        if v_animal.latitude and v_animal.longitude:
            accuracy = UNKNOWN

        # create a new object. Using defaults to avoid collisions when
        # updating data
        defaults = {
            'alternative_id': v_animal.db_animal,
            'breed': breed,
            'sex': sex,
            'father': father,
            'mother': mother,
            'birth_location_latitude': v_animal.latitude,
            'birth_location_longitude': v_animal.longitude,
            'birth_location_accuracy': accuracy,
            'description': v_animal.comment,
            'owner': submission.owner
        }

        animal, created = Animal.objects.update_or_create(
            name=name,
            defaults=defaults)

        if created:
            logger.info("Created %s" % animal)

        else:
            logger.debug("Updating %s" % animal)

    # debug
    logger.info("fill_uid_animals() completed")


def fill_uid_samples(submission):
    """Helper function to fill animal data in UID animal table"""

    # debug
    logger.info("called fill_uid_samples()")

    for v_vessel in VVessels.objects.all():
        # get name for this sample. Need to insert it
        name, created = Name.objects.get_or_create(
            name=v_vessel.ext_vessel,
            submission=submission,
            owner=submission.owner)

        if created:
            logger.info("Created %s" % name)

        else:
            logger.debug("Found %s" % name)

        # get animal object using name
        animal = Animal.objects.get(
            name__name=v_vessel.ext_animal,
            name__submission=submission)

        # create a new object. Using defaults to avoid collisions when
        # updating data
        defaults = {
            'alternative_id': v_vessel.db_vessel,
            'collection_date': v_vessel.production_dt,
            'protocol': v_vessel.get_protocol_name(),
            'organism_part': v_vessel.get_organism_part(),
            'animal': animal,
            'description': v_vessel.comment,
            'owner': submission.owner
        }

        sample, created = Sample.objects.update_or_create(
            name=name,
            defaults=defaults)

        if created:
            logger.info("Created %s" % sample)

        else:
            logger.debug("Updating %s" % sample)

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

        # NAME
        fill_uid_names(submission)

        # ANIMALS
        fill_uid_animals(submission)

        # SAMPLES
        fill_uid_samples(submission)

    except Exception as exc:
        # save a message in database
        submission.status = ERROR
        submission.message = "Error in importing data: %s" % (str(exc))
        submission.save()

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

    logger.info("Import from staging area is complete")

    return True
