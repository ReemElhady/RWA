from django.db import models
from django.utils.translation import gettext as _

# Create your models here.

class City(models.Model):
    name = models.CharField(max_length=254,verbose_name=_('City'))
    def __str__(self):
        return self.name

class Area(models.Model):
    # Area == Site
    city = models.ForeignKey(City , on_delete=models.CASCADE,verbose_name=_('City'), related_name='areas')
    name = models.CharField(max_length=254, verbose_name=_('Area'))
    def __str__(self):
        return self.name

class Neighborhood(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE,verbose_name=_('City') ,related_name='neighborhood')
    area = models.ForeignKey(Area, on_delete=models.CASCADE,verbose_name=_('Area') ,related_name='neighborhood')
    name = models.CharField(max_length=254, verbose_name=_('Village'))
    def __str__(self):
        return self.name