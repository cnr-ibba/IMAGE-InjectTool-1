#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 21 16:04:02 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>

inspired from A Complete Beginner's Guide to Django - Part 4

https://simpleisbetterthancomplex.com/series/2017/09/25/a-complete-beginners-guide-to-django-part-4.html

"""

from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.generic import CreateView
from django.urls import reverse_lazy

from .forms import (
    PersonForm, UserForm, SignUpForm)


class SignUpView(CreateView):
    # import a multiform object
    form_class = SignUpForm
    success_url = reverse_lazy('index')
    template_name = 'accounts/signup.html'

    # add the request to the kwargs
    # https://chriskief.com/2012/12/18/django-modelform-formview-and-the-request-object/
    def get_form_kwargs(self):
        kwargs = super(SignUpView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        # Save the user first, because the profile needs a user before it
        # can be saved. When I save user, I save also person since is related
        # to user
        user = form['user'].save()

        # I re-initialize the form with user.username (from database)
        # maybe I can use get_or_create to get a person object then update it
        form = SignUpForm(
            self.request.POST,
            instance={
                'user': user,
                'person': user.person,
            }
        )
        form.save()

        # Auto connect after registration
        auth_login(self.request, user)

        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(
            self.request,
            message="Please correct the errors below",
            extra_tags="alert alert-dismissible alert-danger")

        return super(SignUpView, self).form_invalid(form)


@login_required
@transaction.atomic
def update_profile(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        person_form = PersonForm(request.POST, instance=request.user.person)

        if user_form.is_valid() and person_form.is_valid():
            user_form.save()
            person_form.save()

            messages.success(
                request,
                message="Your profile was successfully updated!",
                extra_tags="alert alert-dismissible alert-success")

            return redirect('image_app:dashboard')

        else:
            messages.error(
                request,
                message="Please correct the errors below",
                extra_tags="alert alert-dismissible alert-danger")

    # method GET
    else:
        user_form = UserForm(instance=request.user)
        person_form = PersonForm(instance=request.user.person)

        # pass only a object in context
        form_list = [user_form, person_form]

    return render(request, 'accounts/update_user.html', {
        'form_list': form_list
    })
