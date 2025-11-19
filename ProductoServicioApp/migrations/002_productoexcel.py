from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('ProductoServicioApp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductoExcel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('archivo', models.FileField(upload_to='productos_excel/')),
                ('valor_neto', models.PositiveIntegerField(default=0)),
                ('valor_iva', models.PositiveIntegerField(default=0)),
                ('valor_bruto', models.PositiveIntegerField(default=0)),
                ('descuento', models.PositiveIntegerField(default=0)),
                ('creado_en', models.DateTimeField(default=django.utils.timezone.now)),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='archivos_excel', to='ProductoServicioApp.productoservicio')),
            ],
            options={
                'db_table': 'PRODUCTO_EXCEL',
                'ordering': ['-creado_en'],
            },
        ),
    ]