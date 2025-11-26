import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("campaigns", "0004_lead_website"),
    ]

    operations = [
        migrations.AddField(
            model_name="lead",
            name="last_contacted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="lead",
            name="status",
            field=models.CharField(
                choices=[("new", "New"), ("contacted", "Contacted"), ("replied", "Replied")],
                default="new",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="sequencestep",
            name="action",
            field=models.CharField(choices=[("send_email", "Send Email"), ("wait", "Wait")], max_length=20),
        ),
        migrations.CreateModel(
            name="LeadEmail",
            fields=[
                (
                    "id",
                    models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("subject", models.CharField(max_length=255)),
                ("body", models.TextField()),
                ("preview", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("draft", "Draft"), ("sent", "Sent"), ("failed", "Failed")],
                        default="draft",
                        max_length=20,
                    ),
                ),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("meta", models.JSONField(blank=True, default=dict)),
                (
                    "lead",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE, related_name="emails", to="campaigns.lead"
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]


