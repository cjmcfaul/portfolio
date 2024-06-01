from config import celery_app

from apps.upwork.models import JobFeed
from apps.upwork.utils import RSSJobFeed


@celery_app.task(name="Update a job feed")
def update_feed(feed_id):
    try:
        feed = JobFeed.objects.get(
            id=feed_id,
        )
    except JobFeed.DoesNotExist:
        return f"Unable to find a feed with ID - {feed_id}"

    success = RSSJobFeed(job_feed=feed).update()
    return success


@celery_app.task(name="Update all active job feeds")
def update_all_active_feeds():
    feeds = JobFeed.objects.filter(
        active=True,
    )
    for feed in feeds:
        update_feed.delay(feed.id)
