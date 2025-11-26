# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_alter_organizationconfigurations_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationconfigurations',
            name='company_name',
            field=models.CharField(blank=True, help_text='Company name', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='organizationconfigurations',
            name='company_details',
            field=models.TextField(blank=True, help_text='Company description and details', null=True),
        ),
        migrations.AddField(
            model_name='organizationconfigurations',
            name='product_name',
            field=models.CharField(blank=True, help_text='Product/Service name', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='organizationconfigurations',
            name='product_description',
            field=models.TextField(blank=True, help_text='Product description and features', null=True),
        ),
    ]

