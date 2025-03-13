# Generated by Django 5.1.4 on 2025-03-13 08:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0003_remove_journalentry_tags'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='moodentry',
            name='sentiment_score',
        ),
        migrations.AddField(
            model_name='moodentry',
            name='mood',
            field=models.CharField(choices=[('happy', 'Happy'), ('excited', 'Excited'), ('grateful', 'Grateful'), ('content', 'Content'), ('hopeful', 'Hopeful'), ('proud', 'Proud'), ('relaxed', 'Relaxed'), ('loved', 'Loved'), ('confident', 'Confident'), ('energetic', 'Energetic'), ('optimistic', 'Optimistic'), ('relieved', 'Relieved'), ('sad', 'Sad'), ('angry', 'Angry'), ('stressed', 'Stressed'), ('frustrated', 'Frustrated'), ('anxious', 'Anxious'), ('guilty', 'Guilty'), ('lonely', 'Lonely'), ('hopeless', 'Hopeless'), ('overwhelmed', 'Overwhelmed'), ('disappointed', 'Disappointed'), ('calm', 'Calm'), ('bored', 'Bored'), ('indifferent', 'Indifferent'), ('tired', 'Tired'), ('okay', 'Okay'), ('apathetic', 'Apathetic'), ('unsure', 'Unsure'), ('blank', 'Blank')], default='neutral', max_length=20),
        ),
        migrations.AddField(
            model_name='moodentry',
            name='mood_category',
            field=models.CharField(choices=[('positive', 'Positive'), ('negative', 'Negative'), ('neutral', 'Neutral')], default='neutral', max_length=10),
        ),
        migrations.AlterField(
            model_name='moodentry',
            name='mood_score',
            field=models.IntegerField(default=0),
        ),
    ]
