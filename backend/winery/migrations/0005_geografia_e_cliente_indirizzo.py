# Generated migration for geographic models (FASE 1)

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('winery', '0004_agente_cliente_alter_movimentomagazzino_tipo_ordine_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Paese',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=120, unique=True)),
                ('codice_iso', models.CharField(blank=True, default='', max_length=3, help_text='Codice ISO 3166-1 alpha-2 o alpha-3')),
            ],
            options={
                'verbose_name_plural': 'Paesi',
                'ordering': ['nome'],
            },
        ),
        migrations.CreateModel(
            name='Regione',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=120)),
                ('codice_istat', models.CharField(blank=True, default='', max_length=10)),
                ('paese', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='regioni', to='winery.paese')),
            ],
            options={
                'verbose_name_plural': 'Regioni',
                'ordering': ['nome'],
                'unique_together': {('paese', 'nome')},
            },
        ),
        migrations.CreateModel(
            name='Provincia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=120)),
                ('sigla', models.CharField(blank=True, default='', max_length=5)),
                ('codice_istat', models.CharField(blank=True, default='', max_length=10)),
                ('regione', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='province', to='winery.regione')),
            ],
            options={
                'verbose_name_plural': 'Province',
                'ordering': ['nome'],
                'unique_together': {('regione', 'nome')},
            },
        ),
        migrations.CreateModel(
            name='Citta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=200)),
                ('codice_istat', models.CharField(blank=True, default='', max_length=10)),
                ('codice_catastale', models.CharField(blank=True, default='', max_length=10)),
                ('cap_list', models.JSONField(default=list, help_text='Lista CAP disponibili per la città')),
                ('provincia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='citta', to='winery.provincia')),
            ],
            options={
                'verbose_name_plural': 'Città',
                'ordering': ['nome'],
                'unique_together': {('provincia', 'nome')},
            },
        ),
        migrations.RenameField(
            model_name='cliente',
            old_name='via',
            new_name='legacy_indirizzo',
        ),
        migrations.AlterField(
            model_name='cliente',
            name='legacy_indirizzo',
            field=models.CharField(blank=True, default='', help_text='Indirizzo legacy (per dati pre-migrazione geografica)', max_length=300),
        ),
        migrations.AddField(
            model_name='cliente',
            name='paese',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='clienti', to='winery.paese'),
        ),
        migrations.AddField(
            model_name='cliente',
            name='regione',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='clienti', to='winery.regione'),
        ),
        migrations.AddField(
            model_name='cliente',
            name='provincia',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='clienti', to='winery.provincia'),
        ),
        migrations.AddField(
            model_name='cliente',
            name='citta',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='clienti', to='winery.citta'),
        ),
        migrations.AddField(
            model_name='cliente',
            name='cap',
            field=models.CharField(blank=True, default='', max_length=10),
        ),
        migrations.AddField(
            model_name='cliente',
            name='via',
            field=models.CharField(blank=True, default='', help_text='Via, numero civico', max_length=300),
        ),
    ]