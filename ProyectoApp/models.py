# ProyectoApp/models.py
from django.db import models

from EmpresaPersonaApp.models import EmpresaPersona

class Proyecto(models.Model):
    ESTADOS = [
        ("Pendiente", "Pendiente"),
        ("En Progreso", "En Progreso"),
        ("Terminado", "Terminado"),
        ("Cancelado", "Cancelado"),
    ]

    proye_idt = models.AutoField(primary_key=True)
    proye_idp = models.CharField(max_length=20)
    proye_desc = models.CharField(max_length=200)
    proye_obs = models.TextField(blank=True, null=True)
    proye_estado = models.CharField(max_length=20, choices=ESTADOS)
    proye_fecha_sol = models.DateField()
    proye_fecha_ter = models.DateField(blank=True, null=True)
    proye_cost = models.IntegerField(default=0)

    cliente = models.ForeignKey(
        EmpresaPersona,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="proyectos"
    )

    class Meta:
        db_table = "proyecto"

    def __str__(self):
        return f"{self.proye_desc} ({self.proye_estado})"
