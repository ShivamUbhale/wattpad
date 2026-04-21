# Generated manually for Poll / Vote / Story meta

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('stories', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='story',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='story',
            name='is_featured',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterModelOptions(
            name='story',
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='Poll',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chapter_label', models.CharField(blank=True, help_text='e.g. CHAPTER IV: THE THRESHOLD', max_length=120)),
                ('prompt_heading', models.CharField(max_length=500)),
                ('souls_footer_note', models.CharField(blank=True, default='', max_length=200)),
                ('disclaimer', models.TextField(blank=True)),
                ('chapter', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='poll', to='stories.chapter')),
            ],
        ),
        migrations.CreateModel(
            name='PollOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=200)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('theme', models.CharField(default='lavender', help_text='lavender | peach | crimson', max_length=32)),
                ('sort_order', models.PositiveSmallIntegerField(default=0)),
                ('poll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='stories.poll')),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('option', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='votes', to='stories.polloption')),
                ('poll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='votes', to='stories.poll')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='story_votes', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name='vote',
            constraint=models.UniqueConstraint(fields=('user', 'poll'), name='unique_user_vote_per_poll'),
        ),
    ]
