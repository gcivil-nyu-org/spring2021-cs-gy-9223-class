
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AccessibilityRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('restaurant_name', models.CharField(max_length=200)),
                ('compliant', models.BooleanField(default=False)),
                ('business_address', models.CharField(max_length=200)),
                ('street_number', models.CharField(max_length=200)),
                ('street_name', models.CharField(max_length=200)),
                ('city', models.CharField(max_length=200)),
                ('postcode', models.CharField(blank=True, max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Categories',
            fields=[
                ('category', models.CharField(max_length=200, primary_key=True, serialize=False)),
                ('parent_category', models.CharField(default=None, max_length=200, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='FAQ',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.CharField(max_length=200)),
                ('answer', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='InspectionRecords',
            fields=[
                ('restaurant_inspection_id', models.CharField(max_length=200, primary_key=True, serialize=False)),
                ('restaurant_name', models.CharField(max_length=200)),
                ('postcode', models.CharField(max_length=200)),
                ('business_address', models.CharField(max_length=200)),
                ('is_roadway_compliant', models.CharField(max_length=200)),
                ('skipped_reason', models.CharField(max_length=200)),
                ('inspected_on', models.DateTimeField()),
                ('business_id', models.CharField(blank=True, default=None, max_length=200, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='UserQuestionnaire',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('restaurant_business_id', models.CharField(max_length=200)),
                ('user_id', models.CharField(default='', max_length=200)),
                ('safety_level', models.CharField(max_length=1)),
                ('saved_on', models.DateTimeField(blank=True, default=django.utils.timezone.now)),
                ('temperature_required', models.CharField(default='False', max_length=5)),
                ('contact_info_required', models.CharField(default='False', max_length=5)),
                ('employee_mask', models.CharField(default='False', max_length=5)),
                ('capacity_compliant', models.CharField(default='False', max_length=5)),
                ('distance_compliant', models.CharField(default='False', max_length=5)),
            ],
        ),
        migrations.CreateModel(
            name='Zipcodes',
            fields=[
                ('zipcode', models.CharField(max_length=200, primary_key=True, serialize=False)),
                ('borough', models.CharField(default=None, max_length=200, null=True)),
                ('neighborhood', models.CharField(default=None, max_length=200, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='YelpRestaurantDetails',
            fields=[
                ('business_id', models.CharField(max_length=200, primary_key=True, serialize=False)),
                ('neighborhood', models.CharField(default=None, max_length=200, null=True)),
                ('price', models.CharField(default=None, max_length=200, null=True)),
                ('rating', models.FloatField(blank=True, default=0.0, null=True)),
                ('img_url', models.CharField(default=None, max_length=200, null=True)),
                ('latitude', models.DecimalField(blank=True, decimal_places=14, default=0, max_digits=17)),
                ('longitude', models.DecimalField(blank=True, decimal_places=14, default=0, max_digits=17)),
                ('category', models.ManyToManyField(blank=True, to='restaurant.Categories')),
            ],
        ),
        migrations.CreateModel(
            name='Restaurant',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('restaurant_name', models.CharField(max_length=200)),
                ('business_address', models.CharField(max_length=200)),
                ('postcode', models.CharField(max_length=200)),
                ('business_id', models.CharField(blank=True, default=None, max_length=200, null=True, unique=True)),
                ('compliant_status', models.CharField(blank=True, default=None, max_length=200, null=True)),
                ('mopd_compliance_status', models.CharField(blank=True, default=None, max_length=200, null=True)),
                ('yelp_detail', models.ForeignKey(blank=True, default=1, max_length=200, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, to='restaurant.yelprestaurantdetails', unique=True)),
            ],
            options={
                'unique_together': {('restaurant_name', 'business_address', 'postcode')},
            },
        ),
    ]
