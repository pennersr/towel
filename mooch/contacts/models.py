from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from countries.models import Country

from mooch.accounts.middleware import get_current_user
from mooch.abstract.models import BaseModel, CreateUpdateModel


class Contact(models.Model):
    first_name = models.CharField(_('first name'), max_length=100)
    last_name = models.CharField(_('last name'), max_length=100)
    manner_of_address = models.CharField(_('manner of address'), max_length=30,
        blank=True, default='', help_text=_('e.g. Mr., Ms., Dr.'))
    title = models.CharField(_('title/auxiliary'), max_length=100, blank=True,
        default='', help_text=_('e.g. MSc ETH'))
    email = models.EmailField(_('e-mail address'), blank=True)
    website = models.URLField(verify_exists=False, blank=True)
    function = models.TextField(_('function'), blank=True)
    phone = models.CharField(_('phone'), max_length=30, blank=True,
        help_text=_('Please include the country prefix, but no spaces, e.g. +41555111141'))
    fax = models.CharField(_('fax'), max_length=30, blank=True,
        help_text=_('Please include the country prefix, but no spaces, e.g. +41555111141'))
    mobile = models.CharField(_('mobile'), max_length=30, blank=True,
        help_text=_('Please include the country prefix, but no spaces, e.g. +41555111141'))
    address = models.TextField(_('address'), blank=True)

    zip_code = models.CharField(_('ZIP code'), max_length=30, blank=True)
    city = models.CharField(_('city'), max_length=30, blank=True)

    region = models.CharField(_('region'), max_length=30, blank=True)
    country = models.CharField(_('country'), max_length=30, blank=True,
        default='CH')

    sorting_field = models.CharField(_('sorting field'), max_length=50, blank=True,
        editable=False)

    class Meta:
        ordering = ('sorting_field',)
        verbose_name = _('contact')
        verbose_name_plural = _('contacts')

    def __unicode__(self):
        return self.fullname

    @property
    def fullname(self):
        return u'%s %s' % (self.first_name, self.last_name)

    def save(self, *args, **kwargs):
        """
        Fill up the sorting_field everytime we save the object.
        """

        self.sorting_field = u'%s %s' % (self.last_name, self.first_name)
        super(Contact, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return ('contacts_contact_detail', (self.pk,), {})
