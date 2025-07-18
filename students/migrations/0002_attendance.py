# Generated by Django 5.2.4 on 2025-07-14 00:29

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("students", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Attendance",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date", models.DateField(default=django.utils.timezone.now)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("Present", "Present"),
                            ("Absent", "Absent"),
                            ("Late", "Late"),
                            ("Excused", "Excused"),
                        ],
                        max_length=10,
                    ),
                ),
                (
                    "student",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attendance_records",
                        to="students.student",
                    ),
                ),
            ],
            options={
                "ordering": ["-date", "student__full_name"],
                "unique_together": {("student", "date")},
            },
        ),
    ]
