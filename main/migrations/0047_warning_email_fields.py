from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0046_user_preferred_language'),
    ]

    operations = [
        migrations.AddField(
            model_name='warning',
            name='email_subject',
            field=models.CharField(blank=True, default='', max_length=500, verbose_name="Objet de l'email"),
        ),
        migrations.AddField(
            model_name='warning',
            name='email_to',
            field=models.TextField(blank=True, default='', verbose_name='Destinataires (À)'),
        ),
        migrations.AddField(
            model_name='warning',
            name='email_cc',
            field=models.TextField(blank=True, default='', verbose_name='Copie (CC)'),
        ),
        migrations.AddField(
            model_name='warning',
            name='email_bcc',
            field=models.TextField(blank=True, default='', verbose_name='Copie cachée (BCC)'),
        ),
        migrations.AddField(
            model_name='warning',
            name='email_sent',
            field=models.BooleanField(db_index=True, default=False, verbose_name='Email envoyé'),
        ),
        migrations.AddField(
            model_name='warning',
            name='email_sent_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name="Date d'envoi"),
        ),
    ]
