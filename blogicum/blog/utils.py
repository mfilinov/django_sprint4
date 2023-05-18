from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Post


def get_post_data(kwargs):
    return get_object_or_404(
        Post,
        pk=kwargs['post_id'],
        pub_date__lte=timezone.now(),
        is_published=True,
        category__is_published=True,
    )
