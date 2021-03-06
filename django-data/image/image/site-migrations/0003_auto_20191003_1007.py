# -*- coding: utf-8 -*-
# Generated by Django 1.11.24 on 2019-10-03 08:07
from __future__ import unicode_literals

from django.db import migrations


cookie_policy_link = "/image/privacy/"


# This is the old banner content
OLD_BANNER = {
        "message": (
            "This website uses cookies to ensure you get the best "
            "experience on our website."),
        "button_text": "Got it!",
        "cookie_policy_link": cookie_policy_link,
        "cookie_policy_link_text": "Learn more",
        "banner_colour": "#2FA4E7",
        "banner_text_colour": "#ffffff",
        "button_colour": "#73A839",
        "button_text_colour": "#ffffff"
    }


# this will be NEW the banner content
BANNER = {
        "message": (
            "This website requires cookies, and the limited processing of "
            "your personal data in order to function. By using the site you "
            "are agreeing to this as outlined in our"),
        "button_text": "I agree, dismiss this banner",
        "cookie_policy_link": cookie_policy_link,
        "cookie_policy_link_text": "Data Privacy Notice",
        "banner_colour": "#2FA4E7",
        "banner_text_colour": "#ffffff",
        "button_colour": "#73A839",
        "button_text_colour": "#ffffff"
    }


def forwards_func(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version

    CookieConsentSettings = apps.get_model(
        "django_simple_cookie_consent",
        "CookieConsentSettings")

    db_alias = schema_editor.connection.alias

    # delete the old banner
    CookieConsentSettings.objects.using(db_alias).filter(**OLD_BANNER).delete()

    # create the new banner
    CookieConsentSettings.objects.using(db_alias).bulk_create([
        CookieConsentSettings(**BANNER),
    ])


def reverse_func(apps, schema_editor):

    CookieConsentSettings = apps.get_model(
        "django_simple_cookie_consent",
        "CookieConsentSettings")

    db_alias = schema_editor.connection.alias

    # delete the new banner
    CookieConsentSettings.objects.using(db_alias).filter(**BANNER).delete()

    # restore the old banner
    CookieConsentSettings.objects.using(db_alias).bulk_create([
        CookieConsentSettings(**OLD_BANNER),
    ])


class Migration(migrations.Migration):

    dependencies = [
        ('django_simple_cookie_consent', '0002_auto_20190416_1252'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
