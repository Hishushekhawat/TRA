from django.db import models


# Create your models here.



#Lead source details
class Sources(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=150, null=True, blank=True)

    class Meta:
        db_table='leads_file_Source'
        
    def __str__(self):
        return str(self.name)


#Lead file details
class Leads_File(models.Model):
    id = models.AutoField(primary_key=True)
    file = models.FileField(upload_to='files')
    file_name = models.CharField(max_length = 150, null=True, blank=True)
    source = models.ForeignKey(Sources, on_delete=models.DO_NOTHING)

    class Meta:
        db_table = 'leads_file'


#Leads data
class Leads(models.Model):
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=150,null=True, blank=True)
    last_name = models.CharField(max_length = 150, null=True, blank=True)   
    city = models.CharField(max_length = 150, null=True, blank=True)
    state = models.CharField(max_length = 150, null=True, blank=True)
    address = models.CharField(max_length = 150, null=True, blank=True)
    debt_amount = models.CharField(max_length = 150, null=True, blank=True)
    phone = models.CharField(max_length = 150, null=True, blank=True)
    email = models.CharField(max_length = 150, null=True, blank=True)
    opt_in_ip = models.CharField(max_length = 150, null=True, blank=True)
    cost = models.CharField(max_length = 150, null=True, blank=True) 
    purchase_date =  models.DateField( null=True, blank=True)
    import_date = models.DateField(auto_now=True)
    source = models.ForeignKey(Sources, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'leads_data'

class Redundant_data(models.Model):
    id = models.AutoField(primary_key=True)
    email = models.CharField(max_length = 150, null=True, blank=True)
    redund_count = models.PositiveIntegerField()
    file = models.ForeignKey(Leads_File, on_delete=models.DO_NOTHING)
    source = models.ForeignKey(Sources, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Redundant_data'

class user_profile(models.Model):
    objects = None
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=150, null=True, blank=True)
    last_name = models.CharField(max_length=150, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True) 
    phone = models.CharField(null=True, blank=True, unique=True,  max_length=16)
    status = models.CharField(max_length=10)
    password = models.CharField(max_length=200, null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profile'

class User_Otp(models.Model):
    objects = None
    id = models.AutoField(primary_key=True)
    otp = models.PositiveIntegerField()
    user = models.OneToOneField(user_profile, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_otp"