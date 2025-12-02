from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ProductoServicioApp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='productoservicio',
            name='produ_vigencia_fin',
            field=models.DateField(
                blank=True,
                help_text=(
                    'Fecha máxima permitida para emitir o reclamar documentos asociados a este producto.'
                ),
                null=True,
                verbose_name='Vigencia hasta'
            ),
        ),
        migrations.AddField(
            model_name='productoservicio',
            name='produ_vigencia_inicio',
            field=models.DateField(
                blank=True,
                help_text=(
                    'Fecha mínima permitida para emitir o reclamar documentos asociados a este producto.'
                ),
                null=True,
                verbose_name='Vigencia desde'
            ),
        ),
    ]