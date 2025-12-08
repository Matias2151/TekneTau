# EmpresaPersonaApp/models.py
from django.db import models, transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver
from DireccionApp.models import Direccion


class EmpresaPersona(models.Model):
    """
    Modelo principal para Empresas / Personas.
    Representa tanto clientes como proveedores (o ambos).
    """
    # 🔑 Identificador interno
    emppe_id = models.AutoField(primary_key=True)

    # 🧾 Datos básicos
    emppe_rut = models.CharField(
        max_length=11,
        unique=True,
        verbose_name="RUT"
    )
    emppe_nom = models.CharField(
        max_length=100,
        verbose_name="Nombre o Razón Social"
    )
    emppe_alias = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Alias Comercial"
    )

    # ☎️ Contacto
    emppe_fono1 = models.CharField(
        max_length=15,
        verbose_name="Teléfono principal"
    )
    emppe_fono2 = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name="Teléfono secundario"
    )
    emppe_mail1 = models.EmailField(
        max_length=100,
        verbose_name="Correo principal"
    )
    emppe_mail2 = models.EmailField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Correo secundario"
    )

    # ⚙️ Estado y tipo de relación
    # emppe_est = True  -> habilitado / activo
    # emppe_est = False -> inhabilitado / inactivo
    emppe_est = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )
    emppe_sit = models.CharField(
        max_length=20,
        choices=[
            ('cliente', 'Cliente'),
            ('proveedor', 'Proveedor'),
            ('ambos', 'Cliente y Proveedor'),
        ],
        default='cliente',
        verbose_name="Situación"
    )

    # 📍 Relación con DIRECCION
    emppe_dire = models.ForeignKey(
        Direccion,
        on_delete=models.PROTECT,   # Evita borrar direcciones si hay empresas que la usan
        db_column='DIRE_ID',
        related_name='personas',
        null=True,
        blank=True,
        verbose_name="Dirección"
    )

    class Meta:
        db_table = 'EMPRESAPERSONA'
        managed = True
        verbose_name = "Empresa o Persona"
        verbose_name_plural = "Empresas y Personas"
        ordering = ['emppe_nom']

    def __str__(self):
        return f"{self.emppe_nom} ({self.emppe_rut})"


# 🧹 SIGNAL: eliminación de dirección no referenciada
@receiver(post_delete, sender=EmpresaPersona)
def borrar_direccion_asociada(sender, instance: EmpresaPersona, **kwargs):
    """
    Al eliminar una EmpresaPersona, si su dirección no está siendo usada
    por nadie más, se borra automáticamente.
    (OJO: en tu caso ya no borras EmpresaPersona desde la app, sino que
    la inhabilitas cambiando emppe_est a False. De todas maneras,
    este signal queda por si se borra desde el admin o por scripts.)
    """
    dire = instance.emppe_dire
    if dire and dire.personas.count() == 0:
        with transaction.atomic():
            dire.delete()
