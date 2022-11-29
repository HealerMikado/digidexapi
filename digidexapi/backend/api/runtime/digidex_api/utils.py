import logging
import os

import boto3
import schemas
from botocore.exceptions import ClientError


def create_presigned_url(digimon_name: str, thumbnail: bool, expiration=3600):
    """Generate a presigned URL to share an S3 object

    :param digimon_name: a digimon name. It's image file's name has
    the same name.
    :type digimon_name: str
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """

    # Generate a presigned URL for the S3 object
    s3_client = boto3.client("s3")
    if thumbnail:
        object_name = f"digimon-thumbnail/{digimon_name.replace(' ', '_')}.png"
    else:
        object_name = f"digimon-image/{digimon_name.replace(' ', '_')}.png"

    try:
        bucket = os.getenv("S3_IMAGE_BUCKET")

        response = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": object_name},
            ExpiresIn=expiration,
        )
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response


def create_page_url_digimon(path, page_size, page, page_size_actual, **kwarg):
    url_element = []
    if page < 1 or page_size_actual < page_size:
        return ""
    else:
        url_element.append(f"page={page}")
    url_element.append(f"page_size={page_size}")
    for key, value in kwarg.items():
        if value is not None:
            url_element.append(f"{key}={value}")

    return f"{path}{'&'.join(url_element)}"


def create_page_url_other(path, page_size, page, page_elements):
    url_element = []
    if page < 1 or page_elements < page_size:
        return ""
    else:
        url_element.append(f"page={page}")
    if page_size != 100:
        url_element.append(f"page_size={page_size}")
    return f"{path}{'&'.join(url_element)}"


def paginaton(path, count_levels, page, page_size, page_elements, **kwargs):
    next_page = create_page_url_digimon(
        path, page_size, page + 1, page_elements, **kwargs
    )
    previous_page = create_page_url_digimon(
        path, page_size, page - 1, page_elements, **kwargs
    )
    total_page = count_levels // page_size + 1
    pagination = schemas.Pagination(
        next_page=next_page,
        previous_page=previous_page,
        page_size=min(page_size, page_elements),
        total_page=total_page,
    )
    return pagination
