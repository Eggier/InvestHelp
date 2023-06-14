from django.db import models


class Statistic(models.Model):
    name = models.TextField()
    date = models.DateField()
    expense = models.IntegerField()
    income = models.IntegerField()
