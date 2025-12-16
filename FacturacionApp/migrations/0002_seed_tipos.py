from django.db import migrations


def seed_tipos(apps, schema_editor):
    TipoTransaccion = apps.get_model("FacturacionApp", "TipoTransaccion")
    TipoDocumento = apps.get_model("FacturacionApp", "TipoDocumento")
    TipoPago = apps.get_model("FacturacionApp", "TipoPago")

    # Evitar duplicados si ya existen datos
    if not TipoTransaccion.objects.exists():
        TipoTransaccion.objects.bulk_create([
            TipoTransaccion(tipo_id=1, tipo_trans="INGRESO"),
            TipoTransaccion(tipo_id=2, tipo_trans="EGRESO"),
        ])

    if not TipoDocumento.objects.exists():
        TipoDocumento.objects.bulk_create([
            TipoDocumento(tidoc_id=1, tidoc_tipo="FACTURA"),
            TipoDocumento(tidoc_id=2, tidoc_tipo="BOLETA"),
            TipoDocumento(tidoc_id=3, tidoc_tipo="NOTA DE CREDITO"),
            TipoDocumento(tidoc_id=4, tidoc_tipo="ORDEN DE COMPRA"),
        ])

    if not TipoPago.objects.exists():
        TipoPago.objects.bulk_create([
            TipoPago(tpago_id=1, tpago_tipo="EFECTIVO"),
            TipoPago(tpago_id=2, tpago_tipo="TARJETA DE CREDITO"),
            TipoPago(tpago_id=3, tpago_tipo="TARJETA DEBITO"),
            TipoPago(tpago_id=4, tpago_tipo="TRANSFERENCIA BANCARIA"),
            TipoPago(tpago_id=5, tpago_tipo="CHEQUE"),
            TipoPago(tpago_id=6, tpago_tipo="PAGARE"),
            TipoPago(tpago_id=7, tpago_tipo="MIXTO"),
        ])


class Migration(migrations.Migration):

    dependencies = [
        # ⚠️ Cambia esto por tu última migración real anterior
        ("FacturacionApp", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_tipos),
    ]
