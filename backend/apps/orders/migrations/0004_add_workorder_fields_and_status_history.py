# Generated manually for WorkOrder model updates

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_alter_workorderdownloadlink_purpose'),
        ('core', '0001_initial'),
    ]

    operations = [
        # Add new fields to WorkOrder
        migrations.AddField(
            model_name='workorder',
            name='title',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='workorder',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='workorder',
            name='priority',
            field=models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')], default='medium', max_length=20),
        ),
        migrations.AddField(
            model_name='workorder',
            name='due_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='workorder',
            name='location',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='workorder',
            name='notes',
            field=models.TextField(blank=True),
        ),
        # Make assigned_to nullable
        migrations.AlterField(
            model_name='workorder',
            name='assigned_to',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='assigned_orders', to='core.technician'),
        ),
        # Set default status
        migrations.AlterField(
            model_name='workorder',
            name='status',
            field=models.CharField(default='pending', max_length=50),
        ),
        # Create WorkOrderStatusHistory model
        migrations.CreateModel(
            name='WorkOrderStatusHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(max_length=50)),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.technician')),
                ('work_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workorderstatushistory_set', to='orders.workorder')),
            ],
            options={
                'verbose_name': 'Work Order Status History',
                'verbose_name_plural': 'Work Order Status Histories',
                'ordering': ['-created_at'],
            },
        ),
    ]
