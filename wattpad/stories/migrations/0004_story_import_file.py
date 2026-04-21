import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stories', '0003_polls_story_meta'),
    ]

    operations = [
        migrations.AddField(
            model_name='story',
            name='import_file',
            field=models.FileField(
                blank=True,
                help_text='Upload .txt or .pdf to generate chapters on save (replaces existing chapters).',
                null=True,
                upload_to='story_imports/',
                validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['txt', 'pdf'])],
            ),
        ),
    ]
