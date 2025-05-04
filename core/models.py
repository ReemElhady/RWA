from django.db import models
from django.utils.translation import gettext as _

# Create your models here.

class City(models.Model):
    name = models.CharField(max_length=254,verbose_name=_('City'))
    def __str__(self):
        return self.name

# Region Model (formerly Marqas)
class Region(models.Model):
    country = models.ForeignKey(City, related_name='regions', on_delete=models.CASCADE)
    name = models.CharField(max_length=100,verbose_name=_('Region'))
    
    def __str__(self):
        return self.name

# District Model (formerly Wahadat Mahalaya)
class District(models.Model):
    region = models.ForeignKey(Region, related_name='districts', on_delete=models.CASCADE)
    name = models.CharField(max_length=100,verbose_name=_('District'))
    
    def __str__(self):
        return self.name

# Town Model (formerly Qura)
class Town(models.Model):
    district = models.ForeignKey(District, related_name='towns', on_delete=models.CASCADE)
    name = models.CharField(max_length=100,verbose_name=_('Town'))
    
    def __str__(self):
        return self.name

# Neighborhood Model (formerly Izb/Kufur)
class Neighborhood(models.Model):
    town = models.ForeignKey(Town, related_name='neighborhoods', on_delete=models.CASCADE)
    name = models.CharField(max_length=100,verbose_name=_('Neighborhood'))
    
    def __str__(self):
        return self.name
    