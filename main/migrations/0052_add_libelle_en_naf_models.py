from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0051_mailinboxconfig_multirecord'),
    ]

    operations = [
        migrations.AddField(
            model_name='categorynafcode',
            name='libelle_en',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Libellé EN'),
        ),
        migrations.AddField(
            model_name='subcategorynafcode',
            name='libelle_en',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Libellé EN'),
        ),
    ]
