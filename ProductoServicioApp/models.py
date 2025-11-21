# ProductoServicioApp/models.py
from django.db import models
from django.core.validators import MinValueValidator, RegexValidator
from EmpresaPersonaApp.models import EmpresaPersona
from django.utils import timezone
import os


class ProductoServicio(models.Model):
    # --- Validadores reutilizables ---
    texto_validator = RegexValidator(
        regex=r'^[A-Za-z0-9ÁÉÍÓÚáéíóúÑñ .]+$',
        message='Solo se permiten letras, números, espacios y puntos.'
    )

    # --- Campos principales ---
    produ_id = models.AutoField(primary_key=True)
    produ_nom = models.CharField(
        max_length=50,
        validators=[texto_validator],
        verbose_name="Nombre del producto/servicio"
    )
    produ_desc = models.CharField(
        max_length=200,
        validators=[texto_validator],
        verbose_name="Descripción",
        blank=True,
        null=True
    )
    produ_bruto = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Valor Bruto"
    )
    produ_neto = models.PositiveIntegerField(
        default=0,
        verbose_name="Valor Neto"
    )
    produ_iva = models.PositiveIntegerField(
        default=0,
        verbose_name="IVA (19%)"
    )
    produ_dscto = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Descuento"
    )

    # --- Nueva relación con EmpresaPersona (proveedores) ---
    proveedores = models.ManyToManyField(
        EmpresaPersona,
        through='Abastecimiento',
        related_name='productos_servicios',
        verbose_name="Proveedores asociados"
    )

    class Meta:
        db_table = 'PRODUCTOS_SERVICIOS'
        verbose_name = "Producto o Servicio"
        verbose_name_plural = "Productos y Servicios"

    def __str__(self):
        return f"{self.produ_nom} - Bruto: ${self.produ_bruto} | Neto: ${self.produ_neto}"


class Abastecimiento(models.Model):
    emppe = models.ForeignKey(
        EmpresaPersona,
        on_delete=models.CASCADE,
        db_column='EMPPE_ID',
        related_name='abastecimientos'
    )
    produ = models.ForeignKey(
        ProductoServicio,
        on_delete=models.CASCADE,
        db_column='PRODU_ID',
        related_name='abastecimientos'
    )

    class Meta:
        db_table = 'ABASTECIMIENTO'
        unique_together = ('emppe', 'produ')
        verbose_name = "Abastecimiento"
        verbose_name_plural = "Abastecimientos"

    def __str__(self):
        return f"{self.emppe.emppe_nom} ↔ {self.produ.produ_nom}"
    
class ProductoExcel(models.Model):
    producto = models.ForeignKey(
        ProductoServicio,
        related_name="archivos_excel",
        on_delete=models.CASCADE,
    )
    archivo = models.FileField(upload_to="productos_excel/")
    valor_neto = models.PositiveIntegerField(default=0)
    valor_iva = models.PositiveIntegerField(default=0)
    valor_bruto = models.PositiveIntegerField(default=0)
    descuento = models.PositiveIntegerField(default=0)
    creado_en = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "PRODUCTO_EXCEL"
        ordering = ["-creado_en"]

    @property
    def nombre_archivo(self):
        return os.path.basename(self.archivo.name)

    def _str_(self):
        return f"Excel {self.nombre_archivo} para {self.producto.produ_nom}"
