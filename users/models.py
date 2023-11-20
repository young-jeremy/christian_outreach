from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from PIL import Image
from django.utils.text import slugify
from videos.models import Channel, Video
# from videos.models import Video,  LikedVideo, FavoriteVideo, WatchedVideo
import stripe
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import \
    BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _


CHANNEL_VERIFIED_CHOICES = [
    ('VERIFIED', 'verified'),
    ('NOT_VERIFIED', 'not_verified')
]


class CustomUserManager(BaseUserManager):
    def create_user(self, email, date_of_birth,  username, first_name, last_name, name, phone, country, state, city, address, age, registration_date, verification_code=None, password=None):
        if not email:
            raise ValueError('Please provide an email')
        user = self.model(
            name=name,
            email=self.normalize_email(email),
            date_of_birth=date_of_birth,
            username=username,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            country=country,
            state=state,
            city=city,
            address=address,
            age=age,
            registration_date=registration_date,
            verification_code=self.make_random_password(),


        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, date_of_birth, username, first_name, last_name, name, phone, country, state, city, address, age, registration_date, password):
        user = self.create_user(
            email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            name=name,
            password=password,
            date_of_birth=date_of_birth,
            phone=phone,
            country=country,
            state=state,
            city=city,
            address=address,
            age=age,
            registration_date=registration_date,

        )
        user.is_admin = True
        user.is_active = True
        user.save(using=self._db)
        return user


class CustomUser(AbstractBaseUser):

    status = (
        ('1', 'Verified'),
        ('0', 'Unverified'),
    )
    email = models.EmailField(verbose_name='email', max_length=254, unique=True)
    name = models.CharField(max_length=1024, blank=True)
    username = models.CharField(max_length=100, null=True, blank=True)
    password = models.CharField(max_length=1024, blank=True)
    phone = models.CharField(max_length=1024, blank=True)
    country = models.CharField(max_length=50, blank=True)
    state = models.CharField(max_length=1024, blank=True)
    city = models.CharField(max_length=1024, blank=True)
    address = models.CharField(max_length=1024, blank=True)
    age = models.CharField(max_length=1024, null=True)
    verified = models.CharField(max_length=1, default=0)
    # avatar = models.ImageField(upload_to='upload_user_image', blank=True, null=True, default='default_avatar.png')
    bio = models.TextField(max_length=1024, null=True, blank=True)
    # registration_date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    # slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)
    verification_code = models.CharField(max_length=1024, null=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    date_of_birth = models.DateField(auto_now_add=True)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    favorites = models.ManyToManyField('self', related_name='favorite_videos', symmetrical=False)

    objects = CustomUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', ]

    def __str__(self):
        return str(self.email)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(CustomUser, self).save(*args, **kwargs)

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name

    def has_perm(self, obj=None):
        # "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        # "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        # "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin

    def get_username(self):
        return super().get_username()

    def set_password(self, raw_password):
        return super().set_password(raw_password)

    def check_password(self, raw_password):
        return super().check_password(raw_password)

    def normalize_username(self, username):
        return super().normalize_username(username)


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    avatar = models.ImageField(default='static/images/profile_pictures/runda.jpg', upload_to='profile_pictures')
    username = models.CharField(max_length=100, null=True)
    # first_name = models.CharField(max_length=100, null=True)
    # last_name = models.CharField(max_length=100, null=True)
    phone_number = models.CharField(max_length=54, unique=True, blank=True)
    national_security_number = models.IntegerField(unique=True, null=True)
    date_joined = models.DateTimeField(auto_now=True)
    # favorite_videos = models.ManyToManyField(Video, related_name='favourite_by', blank=True)
    activity = models.TextField(blank=True)
    # browsing_history = models.ManyToManyField(Video)
    church_affiliation_or_denomination = models.CharField(max_length=200, blank=True, null=True)
    channel_name = models.CharField(max_length=100, unique=True, choices=CHANNEL_VERIFIED_CHOICES, default='not_verified', null=True, blank=True)
    channel_description = models.TextField(blank=True, null=True)
    channel_cover_image = models.ImageField(upload_to='channel_covers', blank=True)
    bio = models.TextField(blank=True, null=True)
    favorite_videos = models.ManyToManyField(Video)

    def __str__(self):
        return self.user.username


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    description = models.TextField()
    stripe_plan_id = models.CharField(max_length=100)


class Community(models.Model):
    church_logo = models.ImageField(default='static/imag/sa.jpg')
    name = models.CharField(max_length=100, blank=True, null=True)
    description = models.CharField(max_length=100, blank=True, null=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='community_members')

    def __str__(self):
        return self.name


class RevenueSharingRule(models.Model):
    user = models.ForeignKey(CustomUser, models.CASCADE)
    percentage_share = models.DecimalField(max_digits=5, decimal_places=2)


class Report (models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()
    reason = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.content_type)


class Notifications(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    # video = models.ForeignKey(Video, on_delete=models.CASCADE, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return self.content


class Subscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, null=True, blank=True)
    subscribe_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        unique_together = ('user', 'channel')

    def __str__(self):
        return f'{self.user.username} subscribed to {self.channel.name}'


class AccountSettings(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    receive_email_notifications = models.BooleanField(default=True)
    profile_visibility = models.CharField(max_length=100, choices=[('public', 'Public'), ('private', 'Private')], default='public')


class SubChannel(models.Model):
    title = models.CharField(max_length=150, unique=True, null=True)
    description = models.CharField(max_length=150, null=True)
    subd = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='subd')



