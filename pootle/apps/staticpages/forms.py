#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


from django import forms
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from .models import Agreement

def agreement_form_factory(pages, user, base_class=forms.Form):
    """Factory that builds an agreement form.

    :param pages: Legal pages that need to be accepted by users.
    :param user: User bound to the agreement form.
    :param base_class: Base class for this form to inherit from.
    :return: An `AgreementForm` class with `pages` as required checkboxes.
    """
    class AgreementForm(base_class):

        def __init__(self, *args, **kwargs):
            super(AgreementForm, self).__init__(*args, **kwargs)

            self._pages = pages
            self._user = user

            for page in self._pages:
                self.add_page_field(page)

        def save(self):
            """Saves user agreements."""
            if hasattr(super(AgreementForm, self), 'save'):
                # HACKISH: This is tightly coupled with `RegistrationForm`
                # which returns the newly-registered user in its form's
                # `save`. We should listen to the `user_registered` signal
                # instead.
                self._user = super(AgreementForm, self).save()

            for page in self._pages:
                agreement, created = Agreement.objects.get_or_create(
                    user=self._user, document=page,
                )
                agreement.save()

        def legal_fields(self):
            """Returns any fields added by legal pages."""
            return [field for field in self
                    if field.name.startswith('legal_')]

        def add_page_field(self, page):
            """Adds `page` as a required field to this form."""
            url = page.url and page.url or reverse('staticpages.display',
                                                   args=[page.virtual_path])
            anchor = u'href="%s" class="fancybox"' % url
            # Translators: The second '%s' is the title of a document
            label = mark_safe(_("I have read and accept: <a %s>%s</a>",
                                (anchor, page.title,)))

            field_name = 'legal_%d' % page.pk
            self.fields[field_name] = forms.BooleanField(label=label,
                                                         required=True)
            self.fields[field_name].widget.attrs['class'] = 'js-legalfield'

    return AgreementForm