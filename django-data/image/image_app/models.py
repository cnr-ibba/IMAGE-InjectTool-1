from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class DictRole(models.Model):
    """A class to model roles defined as childs of
    http://www.ebi.ac.uk/efo/EFO_0002012"""

    # if not defined, this table will have an own primary key
    label = models.CharField(
            max_length=255,
            blank=False,
            help_text="Example: submitter")

    short_form = models.CharField(
            max_length=255,
            blank=False,
            help_text="Example: EFO_0001741")

    def __str__(self):
        return "{label} ({short_form})".format(
                label=self.label,
                short_form=self.short_form)

    class Meta:
        # db_table will be <app_name>_<classname>
        verbose_name = "role"
        unique_together = (("label", "short_form"),)


class DictBreed(models.Model):
    # id = models.IntegerField(primary_key=True)  # AutoField?
    db_breed = models.IntegerField(blank=True, null=True)
    description = models.CharField(max_length=255, blank=True)
    mapped_breed = models.CharField(max_length=255, blank=True, null=True)
    species = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    language = models.CharField(max_length=255, blank=True, null=True)
    api_url = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return str(self.description)

    class Meta:
        verbose_name = 'Breed'

        # HINT: would mapped_breed ba a better choice to define a unique key
        # using breed and species? in that case, mapped breed need to have a
        # default value, ex the descricption (breed_name)
        unique_together = (("description", "species"),)


class DictSex(models.Model):
    """A class to model sex as defined in PATO"""

    label = models.CharField(
            max_length=255,
            blank=False,
            unique=True,
            help_text="Example: male")

    short_form = models.CharField(
            max_length=255,
            blank=False,
            help_text="Example: PATO_0000384")

    # HINT: model translation in database?

    def __str__(self):
        return "{label} ({short_form})".format(
                label=self.label,
                short_form=self.short_form)

    class Meta:
        verbose_name = 'sex'
        verbose_name_plural = 'sex'


class Name(models.Model):
    """Model UID names: define a name (sample or animal) unique for each
    data submission"""

    # ???: Is cryoweb internal animal_id important?
    db_animal = models.IntegerField(blank=True, null=True)

    # two different animal may have the same name. Its unicity depens on
    # data source name and version
    name = models.CharField(
            max_length=255,
            blank=False,
            null=False)

    datasource = models.ForeignKey(
            'DataSource', db_index=True,
            related_name='%(class)s_datasource')

    def __str__(self):
        return "%s (%s)" % (self.name, self.datasource)

    class Meta:
        verbose_name = 'Animal name'
        unique_together = (("name", "datasource"),)


class Animal(models.Model):
    # id = models.IntegerField(primary_key=True)

    biosampleid = models.CharField(max_length=255, blank=True, null=True)

    # ???: need I the animal_id column for debugging purpose?

    # an animal name has a entry in name table
    name = models.OneToOneField(
            'Name',
            on_delete=models.PROTECT,
            related_name='%(class)s_name')

    alternative_id = models.CharField(max_length=255, blank=True, null=True)

    material = models.CharField(
            max_length=255,
            default="Organism",
            editable=False,
            null=True)

    breed = models.ForeignKey('DictBreed', db_index=True,
                              related_name='%(class)s_breed')

    # using a constraint for sex
    sex = models.ForeignKey('DictSex', db_index=True, blank=True, null=True,
                            default=-1, related_name='%(class)s_sex')

    # Need I check if animal father and mother are already present in
    # database? shuold I check relationship by constraints?
    father = models.ForeignKey(
            'Name',
            on_delete=models.PROTECT,
            related_name='%(class)s_father')

    mother = models.ForeignKey(
            'Name',
            on_delete=models.PROTECT,
            related_name='%(class)s_mother')

    # TODO: need to set this value? How?
    birth_location = models.CharField(
            max_length=255,
            blank=True,
            null=True)

    farm_latitude = models.FloatField(blank=True, null=True)
    farm_longitude = models.FloatField(blank=True, null=True)

    def __str__(self):
        return str(self.name)


class Sample(models.Model):
    biosampleid = models.CharField(max_length=255, blank=True, null=True)

    # a sample name has a entry in name table
    name = models.ForeignKey(
            'Name',
            on_delete=models.PROTECT,
            related_name='%(class)s_name')

    alternative_id = models.CharField(max_length=255, blank=True, null=True)

    material = models.CharField(
        max_length=255,
        default="Specimen from Organism",
        editable=False,
        null=True)

    animal = models.ForeignKey(
            'Animal',
            on_delete=models.PROTECT,
            related_name='%(class)s_animal')

    protocol = models.CharField(max_length=255, blank=True, null=True)

    collection_date = models.DateField(blank=True, null=True)
    collection_place_latitude = models.FloatField(blank=True, null=True)
    collection_place_longitude = models.FloatField(blank=True, null=True)
    collection_place = models.CharField(max_length=255, blank=True, null=True)
    organism_part = models.CharField(max_length=255, blank=True, null=True)
    developmental_stage = models.CharField(
            max_length=255,
            blank=True,
            null=True)
    physiological_stage = models.CharField(
            max_length=255,
            blank=True,
            null=True)
    animal_age_at_collection = models.IntegerField(null=True, blank=True)

    availability = models.CharField(max_length=255, blank=True, null=True)

    storage = models.CharField(max_length=255, blank=True, null=True)

    storage_processing = models.CharField(
            max_length=255,
            blank=True,
            null=True)

    preparation_interval = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return str(str(self.id) + ", " + str(self.name))


class Submission(models.Model):
    # id = models.IntegerField(primary_key=True)  # AutoField?
    project = models.CharField(
            max_length=25,
            default="IMAGE",
            editable=False)

    title = models.CharField(
            max_length=255,
            help_text='Example: Roslin Sheep Atlas')

    # Assigned by BioSample. Not specified in ruleset
    identifier = models.CharField(
            max_length=255, blank=True, null=True,
            help_text='Must be blank if not assigned ' +
                      'by BioSamples Database')

    description = models.CharField(
            max_length=255,
            help_text='Example: The Roslin Institute ' +
                      'Sheep Gene Expression Atlas Project')

    # Not specified in ruleset
    version = models.CharField(
            max_length=255, blank=True, null=True,
            default=1.2)

    reference_layer = models.CharField(
            max_length=255, blank=True, null=True,
            help_text=('If this submission is part of the reference layer, '
                       'this will be "true". Otherwise it will be "false"'))

    update_date = models.DateField(
            blank=True, null=True,
            help_text="Date this submission was last modified")

    release_date = models.DateField(
            blank=True, null=True,
            help_text=("Date to be made public on. If blank, it will be "
                       "public immediately"))

    def __str__(self):
        return str(str(self.id) + ", " + str(self.title))


class Person(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    initials = models.CharField(max_length=255, blank=True, null=True)
    affiliation = models.CharField(max_length=255, blank=True, null=True)

    # last_name, first_name and email comes from User model

    role = models.ForeignKey(
            'DictRole',
            on_delete=models.PROTECT,
            related_name='%(class)s_role',
            null=True)

    def __str__(self):
        return "{name} {surname} ({affiliation})".format(
                name=self.user.first_name,
                surname=self.user.last_name,
                affiliation=self.affiliation)


# https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html#onetoone
# we will now define signals so our Person model will be automatically
# created/updated when we create/update User instances.
# Basically we are hooking the create_user_person and save_user_person
# methods to the User model, whenever a save event occurs. This kind of signal
# is called post_save.
@receiver(post_save, sender=User)
def create_user_person(sender, instance, created, **kwargs):
    if created:
        Person.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_person(sender, instance, **kwargs):
    instance.person.save()


class Organization(models.Model):
    # id = models.IntegerField(primary_key=True)  # AutoField?
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255, blank=True, null=True,
                               help_text='One line, comma separated')
    country = models.CharField(max_length=255, blank=True, null=True)
    URI = models.URLField(max_length=500, blank=True, null=True,
                          help_text='Web site')

    role = models.ForeignKey(
            'DictRole',
            on_delete=models.PROTECT,
            related_name='%(class)s_role')

    users = models.ManyToManyField(User)

    def __str__(self):
        return self.name


class Database(models.Model):
    # id = models.IntegerField(primary_key=True)  # AutoField?
    name = models.CharField(max_length=255)
    DB_ID = models.CharField(max_length=255)
    URI = models.URLField(max_length=500, blank=True, null=True,
                          help_text='Database URI for this entry, ' +
                          'typically a web page.')

    def __str__(self):
        return str(str(self.id) + ", " + str(self.name))


class Publication(models.Model):
    # id = models.IntegerField(primary_key=True)  # AutoField?
    pubmed_id = models.CharField(max_length=255,
                                 help_text='Valid PubMed ID, numeric only')
    doi = models.CharField(max_length=255,
                           help_text='Valid Digital Object Identifier')

    def __str__(self):
        return str(str(self.id) + ", " + str(self.pubmed_id))


class Term_source(models.Model):
    # id = models.IntegerField(primary_key=True)  # AutoField?
    name = models.CharField(max_length=255,
                            help_text='Each value must be unique')
    URI = models.URLField(max_length=500, blank=True, null=True,
                          help_text='Each value must be unique ' +
                          'and with a valid URL')
    version = models.CharField(max_length=255, blank=True, null=True,
                               help_text='If version is unknown, ' +
                               'then last access date should be provided. ' +
                               'If no date is provided, one will be assigned' +
                               ' at submission.')

    def __str__(self):
        return str(str(self.id) + ", " + str(self.name))


class DataSource(models.Model):
    upload_dir = 'data_source/'
    uploaded_file = models.FileField(upload_to=upload_dir)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # TODO: find a Biosample Key for this column
    name = models.CharField(
            max_length=255,
            blank=False,
            null=False,
            help_text='example: Cryoweb IBBA')

    # TODO: find a Biosample Key for this column
    version = models.CharField(
            max_length=255,
            blank=False,
            null=False,
            help_text='examples: 2017-04, version 1.1')

    def __str__(self):
        return "%s, %s" % (self.name, self.version)

    class Meta:
        # HINT: can I put two files for my cryoweb instance? May they have two
        # different version
        unique_together = (("name", "version"),)
