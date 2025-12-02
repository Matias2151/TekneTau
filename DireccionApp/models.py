# DireccionesApp/models.py
from django.db import models

class Region(models.Model):
    regi_id = models.AutoField(primary_key=True)
    regi_nom = models.CharField(max_length=50)

    class Meta:
        db_table = 'REGION'
        managed = False  
        ordering = ['regi_nom']

    def __str__(self):
        return self.regi_nom


class Ciudad(models.Model):
    ciuda_id = models.AutoField(primary_key=True)
    ciuda_nom = models.CharField(max_length=50)
    regi = models.ForeignKey(Region, on_delete=models.DO_NOTHING, db_column='REGI_ID', related_name='ciudades')

    class Meta:
        db_table = 'CIUDAD'
        managed = False
        ordering = ['ciuda_nom']

    def __str__(self):
        return self.ciuda_nom


class Comuna(models.Model):
    comun_id = models.AutoField(primary_key=True)
    comun_nom = models.CharField(max_length=50)
    ciuda = models.ForeignKey(Ciudad, on_delete=models.DO_NOTHING, db_column='CIUDA_ID', related_name='comunas')

    class Meta:
        db_table = 'COMUNA'
        managed = False
        ordering = ['comun_nom']

    def __str__(self):
        return self.comun_nom


class Direccion(models.Model):
    dire_id = models.AutoField(primary_key=True)
    dire_calle = models.CharField(max_length=100)
    dire_num = models.IntegerField()
    dire_otros = models.CharField(max_length=50, blank=True, null=True)
    dire_cod_postal = models.CharField(
        max_length=10, blank=True, null=True, verbose_name="Código Postal"
    )
    regi = models.ForeignKey(Region, on_delete=models.DO_NOTHING, db_column='REGI_ID')
    ciuda = models.ForeignKey(Ciudad, on_delete=models.DO_NOTHING, db_column='CIUDA_ID')
    comun = models.ForeignKey(Comuna, on_delete=models.DO_NOTHING, db_column='COMUN_ID')

    class Meta:
        db_table = 'DIRECCION'
        managed = False 
        ordering = ['dire_id']

    def __str__(self):
        try:
            return f"{self.dire_calle} {self.dire_num}, {self.comun.comun_nom}"
        except:
            return f"{self.dire_calle} {self.dire_num}"
