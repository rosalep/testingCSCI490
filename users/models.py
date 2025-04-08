from django.db import models
import bcrypt
from django.db.models.signals import post_save


def hash_password(password): # might reimplement later to make from scratch
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def normalize_email(email): # make everything after @ lowercase
    try:
        email_name, domain_part = email.strip().split('@', 1)
    except ValueError:
        return email.strip()
    return '@'.join([email_name, domain_part.lower()])

class CustomUserManager(models.Manager):
    def create_user(self, username, email, password, **extra_fields):
        if not username:
            raise ValueError("Username cannot be blank")
        if not email:
            raise ValueError("Email cannot be blank")
        if not password:
            raise ValueError("Password cannot be blank")

        email = normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.password = hash_password(password)  # Hash the password
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password, **extra_fields):
        user = self.create_user(username, email, password) #create the user without extra fields.
        user.is_staff = True #set the staff and superuser fields.
        user.is_superuser = True
        user.is_active = True
        user.save(using=self._db) #save the user.
        return user
    
    def get_by_natural_key(self, username): # part of django user manager
        return self.get(username=username)

class CustomUser(models.Model):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=30, unique=True, default='', blank=True)
    avatar = models.ImageField(upload_to='media/', default='media/default-avatar.png', blank=True, null=True) # not needed upon creation
    email = models.EmailField(max_length=255, unique=True, default='', blank=True)
    password = models.CharField(max_length=128, blank=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(blank=True, null=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = CustomUserManager()  # Assign the manager

    def get_username(self):
        return self.username

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser

    def __str__(self):
        return self.username
    
    # part of django user
    @property
    def is_anonymous(self):
        return False
    
    # part of django user
    @property
    def is_authenticated(self):
        return True

    def check_password(self, password_input):
        # convert to bytes
        input_bytes = password_input.encode('utf-8')
        hash = self.password.encode('utf-8')
        if bcrypt.checkpw(input_bytes, hash):
            return True
        return False
    

# class Profile(models.Model):
#     user=models.OneToOneField(CustomUser,on_delete=models.CASCADE) # user deleted, profile deleted
#     bio = models.TextField(default='Hello, world!')
     
#     def __str__(self):
#         return str(self.user)

# def make_profile(sender,instance,created,**kwargs):
#     if created:
#         Profile.objects.create(user=instance)
        
# post_save.connect(make_profile,sender=CustomUser)