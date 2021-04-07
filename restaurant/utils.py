from django.conf import settings
from django.core.mail import EmailMessage
from django.forms.models import model_to_dict
from django.db.models import F


from .models import (
    InspectionRecords,
    Restaurant,
    YelpRestaurantDetails,
    UserQuestionnaire,
)

from user.models import (
    Review,
    Comment,
    Report_Ticket_Review,
    Report_Ticket_Comment,
)

import requests
import json
import logging
import pandas as pd
import io

logger = logging.getLogger(__name__)


def get_restaurant_info_yelp(business_id):
    access_token = settings.YELP_ACCESS_TOKEN_BUSINESS_ID
    headers = {"Authorization": "bearer %s" % access_token}
    url = settings.YELP_BUSINESS_API + business_id
    return requests.get(url, headers=headers)


def default_info_page(restaurant_name):
    return {
        "name": restaurant_name,
        "image_url": settings.DEFAULT_IMAGE,
        "rating": 0,
        "fake_info": True,
    }


def get_restaurant_info_yelp_local(business_id, restaurant_name):
    yelp_detail_set = YelpRestaurantDetails.objects.filter(business_id=business_id)[0:1]
    if yelp_detail_set.count() == 0:
        return json.loads(get_restaurant_info_yelp(business_id).content)
    yelp_detail = yelp_detail_set[0]
    yelp_dict = model_to_dict(yelp_detail) if yelp_detail else None
    if yelp_dict:
        # Format the info
        yelp_dict["rating"] = yelp_dict["rating"] if yelp_dict["rating"] else 0
        yelp_dict["price"] = yelp_dict["price"] if yelp_dict["price"] else ""
        yelp_dict["id"] = yelp_dict["business_id"]
        yelp_dict["name"] = restaurant_name
        yelp_dict["image_url"] = (
            yelp_dict["img_url"] if yelp_dict["img_url"] else settings.DEFAULT_IMAGE
        )
        category_list = []
        for category in yelp_dict["category"]:
            category_list.append({"title": category.parent_category})
        del yelp_dict["category"]
        yelp_dict["categories"] = category_list

    return yelp_dict


def get_restaurant_reviews_yelp(business_id):
    access_token = settings.YELP_ACCESS_TOKEN_REVIEW
    headers = {"Authorization": "bearer %s" % access_token}
    url = settings.YELP_BUSINESS_API + business_id + "/reviews"
    return requests.get(url, headers=headers)


def merge_yelp_info(restaurant_info, restaurant_reviews):
    yelp_info = json.loads(restaurant_info.content)
    yelp_info["rating"] = yelp_info["rating"] if "rating" in yelp_info else 0
    yelp_info["price"] = yelp_info["price"] if "price" in yelp_info else ""
    yelp_info["image_url"] = (
        yelp_info["image_url"] if "image_url" in yelp_info else settings.DEFAULT_IMAGE
    )
    return {
        "info": yelp_info,
        "reviews": json.loads(restaurant_reviews.content),
    }


def query_yelp(business_id):
    if not business_id:
        return None
    restaurant_info = get_restaurant_info_yelp(business_id)
    restaurant_reviews = get_restaurant_reviews_yelp(business_id)

    data = merge_yelp_info(restaurant_info, restaurant_reviews)
    return data


def get_latest_inspection_record(business_name, business_address, postcode):
    records = InspectionRecords.objects.filter(
        restaurant_name=business_name,
        business_address=business_address,
        postcode=postcode,
    ).order_by("-inspected_on")

    q = Restaurant.objects.get(
        restaurant_name=business_name, business_address=business_address
    )
    mopd_status = q.mopd_compliance_status

    if len(records) >= 1:
        record = model_to_dict(records[0])
        record["inspected_on"] = record["inspected_on"].strftime("%Y-%m-%d %I:%M %p")
        record["mopd_compliance"] = mopd_status
        return record

    return None


def query_inspection_record(business_name, business_address, postcode):
    records = InspectionRecords.objects.filter(
        restaurant_name=business_name,
        business_address=business_address,
        postcode=postcode,
    ).order_by("-inspected_on")
    q = Restaurant.objects.get(
        restaurant_name=business_name, business_address=business_address
    )
    mopd_status = q.mopd_compliance_status
    result = []
    for record in records:
        inspection_record = model_to_dict(record)
        inspection_record["inspected_on"] = inspection_record["inspected_on"].strftime(
            "%Y-%m-%d %I:%M %p"
        )
        inspection_record["mopd_compliance"] = mopd_status
        result.append(inspection_record)
    return result


def restaurants_to_dict(restaurants):
    result = []
    for restaurant in restaurants:
        restaurant_dict = model_to_dict(restaurant)
        restaurant_dict["yelp_info"] = (
            get_restaurant_info_yelp_local(
                restaurant.business_id, restaurant.restaurant_name
            )
            if restaurant.business_id
            else None
        )

        if not restaurant_dict["yelp_info"]:
            restaurant_dict["yelp_info"] = default_info_page(restaurant.restaurant_name)

        latest_inspection_record = get_latest_inspection_record(
            restaurant.restaurant_name, restaurant.business_address, restaurant.postcode
        )
        restaurant_dict["latest_record"] = latest_inspection_record
        result.append(restaurant_dict)
    return result


def get_total_restaurant_number(
    keyword=None,
    neighbourhoods_filter=None,
    categories_filter=None,
    price_filter=None,
    rating_filter=None,
    compliant_filter=None,
    sort_option=None,
    favorite_filter=None,
    user=None,
    user_geocode=None,
):
    if (
        keyword
        or neighbourhoods_filter
        or categories_filter
        or price_filter
        or rating_filter
        or compliant_filter
        or sort_option
        or favorite_filter
    ):
        restaurants = get_filtered_restaurants(
            keyword,
            price_filter,
            neighbourhoods_filter,
            rating_filter,
            categories_filter,
            compliant_filter,
            0,
            None,
            sort_option,
            favorite_filter,
            user,
            user_geocode,
        )
        return restaurants.count()

    return Restaurant.objects.filter(
        business_id__in=YelpRestaurantDetails.objects.all()
    ).count()


def get_restaurant_list(
    page=1,
    limit=6,
    keyword=None,
    neighbourhoods_filter=None,
    categories_filter=None,
    price_filter=None,
    rating_filter=None,
    compliant_filter=None,
    sort_option=None,
    favorite_filter=None,
    user=None,
    user_geocode=None,
):
    page = int(page) - 1
    offset = int(page) * int(limit)

    if (
        keyword
        or neighbourhoods_filter
        or categories_filter
        or price_filter
        or rating_filter
        or compliant_filter
        or sort_option
        or favorite_filter
    ):
        restaurants = get_filtered_restaurants(
            keyword,
            price_filter,
            neighbourhoods_filter,
            rating_filter,
            categories_filter,
            compliant_filter,
            page,
            limit,
            sort_option,
            favorite_filter,
            user,
            user_geocode,
        )
        return restaurants_to_dict(restaurants)
    else:
        restaurants = Restaurant.objects.filter(
            business_id__in=YelpRestaurantDetails.objects.all()
        )[
            offset : offset + int(limit)  # noqa: E203
        ]
        return restaurants_to_dict(restaurants)


def get_filtered_restaurants(
    keyword=None,
    price=None,
    neighborhood=None,
    rating=None,
    category=None,
    compliant=None,
    page=0,
    limit=None,
    sort_option=None,
    favorite_filter=None,
    user=None,
    user_geocode=None,
):
    filters = {}

    if not limit:
        limit = Restaurant.objects.all().count()

    offset = page * int(limit)
    if price:
        filters["price__in"] = price
    if neighborhood:
        filters["neighborhood__iregex"] = r"^(" + "|".join(neighborhood) + ")$"
    if rating:
        filters["rating__in"] = rating
    if category:
        filters["category__parent_category__iregex"] = r"^(" + "|".join(category) + ")$"

    keyword_filter = {}
    if keyword:
        keyword_filter["restaurant_name__icontains"] = keyword

    if compliant:
        if "COVIDCompliant" in compliant:
            keyword_filter["compliant_status__iexact"] = "Compliant"
        if "MOPDCompliant" in compliant:
            keyword_filter["mopd_compliance_status__iexact"] = "Compliant"

    value = None
    user_lat, user_lng = None, None
    if sort_option:
        if sort_option == "ratedhigh":
            value = "-yelp_detail__rating"
        elif sort_option == "ratedlow":
            value = "yelp_detail__rating"
        elif sort_option == "pricehigh":
            value = "-yelp_detail__price"
        elif sort_option == "pricelow":
            value = "yelp_detail__price"
        elif sort_option == "distance":
            loc = user_geocode.split(",")
            user_lat = float(loc[0])
            user_lng = float(loc[1])

    if user and user.is_authenticated and sort_option == "recommended":
        preferred_categories = []
        keyword_filter["compliant_status__iexact"] = "Compliant"
        if not user.preferences.all():
            restaurants = (
                Restaurant.objects.filter(
                    business_id__in=YelpRestaurantDetails.objects.all()
                )
                .distinct()
                .filter(**keyword_filter)
                .order_by("-yelp_detail__rating")[offset : offset + int(limit)]
            )
            return restaurants

        for c in user.preferences.all():
            preferred_categories.append(c.parent_category)

        filters["category__parent_category__in"] = preferred_categories

        value = "-yelp_detail__rating"
        if favorite_filter:
            filtered_restaurants = user.favorite_restaurants.all()
            filtered_restaurants = (
                filtered_restaurants.filter(
                    business_id__in=YelpRestaurantDetails.objects.filter(**filters)
                )
                .distinct()
                .filter(**keyword_filter)
                .order_by(value)[offset : offset + int(limit)]
            )
        else:
            filtered_restaurants = (
                Restaurant.objects.filter(
                    business_id__in=YelpRestaurantDetails.objects.filter(**filters)
                )
                .distinct()
                .filter(**keyword_filter)
                .order_by(value)[offset : offset + int(limit)]
            )

        return filtered_restaurants

    if favorite_filter:
        if user.is_authenticated:
            if value:
                filtered_restaurants = user.favorite_restaurants.all()
                filtered_restaurants = (
                    filtered_restaurants.filter(
                        business_id__in=YelpRestaurantDetails.objects.filter(**filters)
                    )
                    .order_by(value)
                    .distinct()
                    .filter(**keyword_filter)[offset : offset + int(limit)]
                )
            elif user_lat and user_lng:
                filtered_restaurants = user.favorite_restaurants.all()
                filtered_restaurants = (
                    filtered_restaurants.filter(
                        business_id__in=YelpRestaurantDetails.objects.filter(**filters)
                    )
                    .order_by(
                        (user_lat - F("yelp_detail__latitude")) ** 2
                        + (user_lng - F("yelp_detail__longitude")) ** 2
                    )
                    .distinct()
                    .filter(**keyword_filter)[offset : offset + int(limit)]
                )
            else:
                filtered_restaurants = user.favorite_restaurants.all()
                filtered_restaurants = (
                    filtered_restaurants.filter(
                        business_id__in=YelpRestaurantDetails.objects.filter(**filters)
                    )
                    .distinct()
                    .filter(**keyword_filter)
                    .order_by("-id")[offset : offset + int(limit)]
                )

    elif value:
        filtered_restaurants = (
            Restaurant.objects.filter(
                business_id__in=YelpRestaurantDetails.objects.filter(**filters)
            )
            .order_by(value)
            .distinct()
            .filter(**keyword_filter)[offset : offset + int(limit)]
        )
    elif user_lat and user_lng:
        filtered_restaurants = (
            Restaurant.objects.filter(
                business_id__in=YelpRestaurantDetails.objects.filter(**filters)
            )
            .order_by(
                (user_lat - F("yelp_detail__latitude")) ** 2
                + (user_lng - F("yelp_detail__longitude")) ** 2
            )
            .distinct()
            .filter(**keyword_filter)[offset : offset + int(limit)]
        )
    else:
        filtered_restaurants = (
            Restaurant.objects.filter(
                business_id__in=YelpRestaurantDetails.objects.filter(**filters)
            )
            .distinct()
            .filter(**keyword_filter)
            .order_by("-id")[offset : offset + int(limit)]
        )

    return filtered_restaurants


def check_user_location(user, form_location, form_geocode):
    default_location = "Central Park North, New York, NY, USA"
    default_geocode = "40.7992147,-73.954758"

    if user.is_authenticated:
        if form_location and form_geocode:
            user.current_location = form_location
            user.current_geocode = form_geocode
            user.save()
            return user.current_location, user.current_geocode
        elif user.current_location and user.current_geocode:
            return user.current_location, user.current_geocode
        else:
            return default_location, default_geocode
    else:
        if form_location and form_geocode:
            return form_location, form_geocode
        else:
            return default_location, default_geocode


def get_latest_feedback(business_id):
    all_feedback_list = UserQuestionnaire.objects.filter(
        restaurant_business_id=business_id,
    ).order_by("-saved_on")
    if len(all_feedback_list) >= 1:
        latest_feedback = model_to_dict(all_feedback_list[0])
        return latest_feedback

    return None


def get_average_safety_rating(business_id):
    all_feedback_list = UserQuestionnaire.objects.filter(
        restaurant_business_id=business_id,
    )
    if len(all_feedback_list) >= 1:
        total = 0
        for feedback in all_feedback_list:
            total += int(feedback.safety_level)
        average_safety_rating = str(round(total / len(all_feedback_list), 2))
        return average_safety_rating
    return None


def get_csv_from_github():
    url = "https://raw.githubusercontent.com/nychealth/coronavirus-data/master/latest/last7days-by-modzcta.csv"  # noqa: E501
    download = requests.get(url).content
    return pd.read_csv(io.StringIO(download.decode("utf-8")))


def check_restaurant_saved(user, restaurant_id):
    return len(user.favorite_restaurants.all().filter(id=restaurant_id)) > 0


def questionnaire_report(restaurant_business_id):
    inspection_results = list(
        InspectionRecords.objects.filter(business_id=restaurant_business_id).order_by(
            "inspected_on"
        )
    )
    if len(inspection_results) >= 1:
        latest_inspection = inspection_results[0]
        latest_inspection_time = latest_inspection.inspected_on
        latest_inspection_status = latest_inspection.is_roadway_compliant

        valuable_questionnaire_list = list(
            UserQuestionnaire.objects.filter(
                restaurant_business_id=restaurant_business_id,
                saved_on__gte=latest_inspection_time,
            ).order_by("saved_on")
        )

        return latest_inspection_status, valuable_questionnaire_list
    return None


def questionnaire_statistics(restaurant_business_id):
    if questionnaire_report(restaurant_business_id):
        latest_inspection_status, valuable_questionnaire_list = questionnaire_report(
            restaurant_business_id
        )
        total_valuable_count = len(valuable_questionnaire_list)
        if total_valuable_count >= 1:
            total_safety_rating = 0
            temp_check_true = 0
            contact_info_required_true = 0
            employee_mask_true = 0
            capacity_compliant_true = 0
            distance_compliant_true = 0

            for questionnaire in valuable_questionnaire_list:
                total_safety_rating += int(questionnaire.safety_level)
                temp_check_true += (
                    1 if questionnaire.temperature_required.__contains__("true") else 0
                )
                contact_info_required_true += (
                    1 if questionnaire.contact_info_required.__contains__("true") else 0
                )
                employee_mask_true += (
                    1 if questionnaire.employee_mask.__contains__("true") else 0
                )
                capacity_compliant_true += (
                    1 if questionnaire.capacity_compliant.__contains__("true") else 0
                )
                distance_compliant_true += (
                    1 if questionnaire.distance_compliant.__contains__("true") else 0
                )
            valuable_avg_safety_rating = str(
                round(total_safety_rating / total_valuable_count, 2)
            )

            statistics_dict = {
                "valuable_avg_safety_rating": valuable_avg_safety_rating,
                "temp_check_true": temp_check_true,
                "temp_check_false": total_valuable_count - temp_check_true,
                "contact_info_required_true": contact_info_required_true,
                "contact_info_required_false": total_valuable_count
                - contact_info_required_true,
                "employee_mask_true": employee_mask_true,
                "employee_mask_false": total_valuable_count - employee_mask_true,
                "capacity_compliant_true": capacity_compliant_true,
                "capacity_compliant_false": total_valuable_count
                - capacity_compliant_true,
                "distance_compliant_true": distance_compliant_true,
                "distance_compliant_false": total_valuable_count
                - distance_compliant_true,
            }

            return statistics_dict
    statistics_dict = {
        "valuable_avg_safety_rating": 0,
        "temp_check_true": 0,
        "temp_check_false": 0,
        "contact_info_required_true": 0,
        "contact_info_required_false": 0,
        "employee_mask_true": 0,
        "employee_mask_false": 0,
        "capacity_compliant_true": 0,
        "capacity_compliant_false": 0,
        "distance_compliant_true": 0,
        "distance_compliant_false": 0,
    }

    return statistics_dict


def get_compliant_restaurant_list(
    page=1,
    limit=6,
    rating_filter=None,
    compliant_filter=None,
):
    page = int(page) - 1
    offset = int(page) * int(limit)
    inspections = InspectionRecords.objects.order_by("-inspected_on").distinct()

    latest_restaurants = list()
    c = 0
    for ir in inspections:
        if (
            ir.is_roadway_compliant == "Compliant"
            and ir.business_id not in latest_restaurants
            and c <= limit
        ):
            latest_restaurants.append(ir.business_id)
            c += 1
        elif c > limit:
            break

    filters = {}

    filters["business_id__in"] = latest_restaurants
    filters["rating__in"] = rating_filter

    restaurants = Restaurant.objects.filter(
        business_id__in=YelpRestaurantDetails.objects.filter(**filters)
    )[
        offset : offset + int(limit)  # noqa: E203
    ]
    return restaurants_to_dict(restaurants)


def get_reviews_stats(reviews):
    ratings, distribution = [], [0] * 6
    for review in reviews:
        rating = int(review["rating"])
        ratings.append(rating)
        distribution[rating] += 1

    count, total = len(ratings), sum(ratings)
    ratings_avg = 0 if count == 0 else round(total / count, 2)

    if count != 0:
        for i in range(6):
            distribution[i] = round(distribution[i] / count, 2) * 100

    return count, ratings_avg, distribution


def remove_reports_review(review_id):
    try:
        review = Review.objects.get(pk=review_id)
        report_tickets = list(Report_Ticket_Review.objects.filter(review=review))
        for report_ticket in report_tickets:
            report_ticket.delete()
        return True
    except Review.DoesNotExist:
        logger.warning("Review ID could not be found: {}".format(review_id))
        return False


def remove_reports_comment(comment_id):
    try:
        comment = Comment.objects.get(pk=comment_id)
        report_tickets = list(Report_Ticket_Comment.objects.filter(comment=comment))
        for report_ticket in report_tickets:
            report_ticket.delete()
        return True
    except Comment.DoesNotExist:
        logger.warning("Comment ID could not be found: {}".format(comment_id))
        return False

def send_moderate_notification_email(request, user, restaurant, subject, event):
    """
    Send a notification email to user's email address

    :param request: HTTP request
    :param model user: user object
    :param model restaurant: restaurant object
    :param str subject: review/comment issue to notify user
    :param str event: report/hide/delete event
    :return: list of recipients, which contains target user only
    """
    host_name = request.get_host()
    # TODO: currently using public facing page as redirect page
    base_url = host_name + "/user/facing_page/" + str(user.id)
    if str(host_name).startswith("127.0.0.1"):
        # For local tests
        base_url = "http://" + base_url
    else:
        base_url = "https://" + base_url

    email_subject = "Your " + subject + "is "
    message = (
        "Hi "
        + user.username
        + ", \n\n"
        + "Your "
        + subject
        + " on Dineline's restaurant, "
        + restaurant.restaurant_name
        + ",  is "
    )

    operations = {
        "report": "reported by other user!",
        "hide": "hidden by admin!",
        "delete": "deleted by admin!",
    }
    operation = operations[event]
    email_subject += operation
    message += operation

    message += " \n\nPlease checkout link below for more details:\n\n" + base_url
    email = EmailMessage(email_subject, message, to=[user.email])
    logger.info("Send email to: %s", user.email)
    return email.send()
