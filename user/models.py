from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from restaurant.models import Restaurant, Categories
from phonenumber_field.modelfields import PhoneNumberField
from datetime import datetime


class Preferences(models.Model):
    preference_type = models.CharField(max_length=200, default="")
    value = models.CharField(max_length=200, default="")
    display_value = models.CharField(max_length=200, default="")

    def __str__(self):
        return "{}: {}".format(self.preference_type, self.value)


class DineSafelyUser(AbstractUser):
    favorite_restaurants = models.ManyToManyField(Restaurant, blank=True)
    preferences = models.ManyToManyField(Preferences, blank=True)
    current_location = models.CharField(
        max_length=200, default=None, blank=True, null=True
    )
    current_geocode = models.CharField(
        max_length=200, default=None, blank=True, null=True
    )


class User_Profile(models.Model):
    STATE_CHOICES = [
        ("Alabama", "Alabama"),
        ("Alaska", "Alaska"),
        ("Arizona", "Arizona"),
        ("Arkansas", "Arkansas"),
        ("California", "California"),
        ("Colorado", "Colorado"),
        ("Connecticut", "Connecticut"),
        ("Delaware", "Delaware"),
        ("District of Columbia", "District of Columbia"),
        ("Florida", "Florida"),
        ("Georgia", "Georgia"),
        ("Hawaii", "Hawaii"),
        ("Idaho", "Idaho"),
        ("Illinois", "Illinois"),
        ("Indiana", "Indiana"),
        ("Iowa", "Iowa"),
        ("Kansas", "Kansas"),
        ("Kentucky", "Kentucky"),
        ("Louisiana", "Louisiana"),
        ("Maine", "Maine"),
        ("Montana", "Montana"),
        ("Nebraska", "Nebraska"),
        ("Nevada", "Nevada"),
        ("New Hampshire", "New Hampshire"),
        ("New Jersey", "New Jersey"),
        ("New Mexico", "New Mexico"),
        ("New York", "New York"),
        ("North Carolina", "North Carolina"),
        ("North Dakota", "North Dakota"),
        ("Ohio", "Ohio"),
        ("Oklahoma", "Oklahoma"),
        ("Oregon", "Oregon"),
        ("Maryland", "Maryland"),
        ("Massachusetts", "Massachusetts"),
        ("Michigan", "Michigan"),
        ("Minnesota", "Minnesota"),
        ("Mississippi", "Mississippi"),
        ("Missouri", "Missouri"),
        ("Pennsylvania", "Pennsylvania"),
        ("Rhode Island", "Rhode Island"),
        ("South Carolina", "South Carolina"),
        ("South Dakota", "South Dakota"),
        ("Tennessee", "Tennessee"),
        ("Texas", "Texas"),
        ("Utah", "Utah"),
        ("Vermont", "Vermont"),
        ("Virginia", "Virginia"),
        ("Washington", "Washington"),
        ("West Virginia", "West Virginia"),
        ("Wisconsin", "Wisconsin"),
        ("Wyoming", "Wyoming"),
    ]

    AUTH_STATUS_CHOICES = [
        ("certified", "Certified"),
        ("pending", "Pending"),
        ("uncertified", "Uncertified"),
    ]

    user = models.OneToOneField(
        DineSafelyUser, on_delete=models.CASCADE, null=True, related_name="user_profile"
    )
    photo = models.CharField("Profile Picture", max_length=150, null=True)
    phone = PhoneNumberField(null=True, blank=True, unique=False)
    address1 = models.CharField("Address line 1", max_length=128, blank=True)
    address2 = models.CharField("Address line 2", max_length=128, blank=True)
    city = models.CharField("City", max_length=64, blank=True)
    zip_code = models.CharField("ZIP / Postal code", max_length=10)
    state = models.CharField(max_length=128, choices=STATE_CHOICES, default="None")

    auth_status = models.CharField(
        "Authentication Status",
        max_length=16,
        choices=AUTH_STATUS_CHOICES,
        default="uncertified",
    )

    def __str__(self):
        return f"{self.user.username}_user_profile"


class Review(models.Model):
    # Basic info
    user = models.ForeignKey(
        DineSafelyUser, on_delete=models.CASCADE, related_name="reviews"
    )
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, related_name="reviews"
    )
    time = models.DateTimeField(default=datetime.now, editable=False, db_index=True)
    content = models.TextField()
    hidden = models.BooleanField(default=False)

    # Ratings
    rating = models.PositiveIntegerField(default=0)
    rating_safety = models.PositiveIntegerField(default=0)
    # Accessibility Ratings
    rating_entry = models.PositiveIntegerField(default=0)
    rating_door = models.PositiveIntegerField(default=0)
    rating_table = models.PositiveIntegerField(default=0)
    rating_bathroom = models.PositiveIntegerField(default=0)
    rating_path = models.PositiveIntegerField(default=0)

    # Images
    image1 = models.ImageField(null=True, blank=True, upload_to="review_images/")
    image2 = models.ImageField(null=True, blank=True, upload_to="review_images/")
    image3 = models.ImageField(null=True, blank=True, upload_to="review_images/")

    # Like
    likes = models.ManyToManyField(DineSafelyUser, blank=True)

    def __str__(self):
        return f"{self.user.username} review on {self.restaurant.restaurant_name}"

    def total_likes(self):
        return self.likes.count()


class Comment(models.Model):
    user = models.ForeignKey(
        DineSafelyUser, on_delete=models.CASCADE, related_name="comments"
    )
    review = models.ForeignKey(
        Review, on_delete=models.CASCADE, related_name="comments"
    )
    text = models.CharField(max_length=512)
    time = models.DateTimeField(auto_now_add=True)
    hidden = models.BooleanField(default=False)

    class Meta:
        ordering = ["-time"]

    def __str__(self):
        comment_user = self.user.username
        reviewer = self.review.user.username
        restaurant = self.review.restaurant.restaurant_name
        return f"{comment_user} comment on {reviewer}'s review for {restaurant}"


class Report_Ticket_Review(models.Model):
    user = models.ForeignKey(
        DineSafelyUser, on_delete=models.CASCADE, related_name="report_reviews"
    )
    review = models.ForeignKey(
        Review, on_delete=models.CASCADE, related_name="report_tickets"
    )
    reason = models.CharField(max_length=512)
    time = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-time"]

    def __str__(self):
        reporter = self.user.username
        reported_user = self.review.user.username
        return f"{reporter}'s report ticket on {reported_user}'s review"


class Report_Ticket_Comment(models.Model):
    user = models.ForeignKey(
        DineSafelyUser, on_delete=models.CASCADE, related_name="report_comments"
    )
    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, related_name="report_tickets"
    )
    reason = models.CharField(max_length=512)
    time = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-time"]

    def __str__(self):
        reporter = self.user.username
        reported_user = self.comment.user.username
        return f"{reporter}'s report ticket on {reported_user}'s comment"


class RestaurantQuestion(models.Model):
    user = models.ForeignKey(
        DineSafelyUser, on_delete=models.CASCADE, related_name="questions"
    )
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, related_name="questions"
    )
    time = models.DateTimeField(default=datetime.now, editable=False, db_index=True)
    question = models.TextField()

    def __str__(self):
        return f"{self.user.username} question for {self.restaurant.restaurant_name}"


class RestaurantAnswer(models.Model):
    user = models.ForeignKey(
        DineSafelyUser, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(
        RestaurantQuestion, on_delete=models.CASCADE, related_name="answers"
    )
    text = models.CharField(max_length=512)
    time = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-time"]

    def __str__(self):
        answer_user = self.user.username
        question_user = self.question.user.username
        restaurant = self.question.restaurant.restaurant_name
        return f"{answer_user} answered {question_user}'s question for {restaurant}"


class UserActivityLog(models.Model):
    user = models.ForeignKey(
        DineSafelyUser, on_delete=models.CASCADE, related_name="activity_log"
    )
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, related_name="activity_log"
    )
    visits = models.PositiveIntegerField(default=1)
    last_visit = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_visit"]

    def __str__(self):
        user = self.user.username
        restaurant = self.restaurant.restaurant_name
        return (
            f"{user} viewed {restaurant} {self.visits} times, "
            + f"last visited at {self.last_visit}"
        )


class Email(models.Model):
    user = models.ForeignKey(
        DineSafelyUser, on_delete=models.CASCADE, related_name="other_emails"
    )
    email = models.EmailField()
    active = models.BooleanField(default=False)

    def __str__(self):
        if self.active:
            return f"{self.user} {self.email} is active"
        else:
            return f"{self.user} {self.email} is not active"
