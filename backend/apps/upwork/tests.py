from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.upwork.models import JobFeed
from apps.upwork.utils import RSSJobFeed


class UpworkTestCase(TestCase):

    def setUp(self):
        last_polled = timezone.now() - timedelta(hours=1)
        self.job_feed = JobFeed.objects.create(
            name="Full Stack Developer",
            url="https://www.upwork.com/ab/feed/jobs/rss?amount=3000-&contractor_tier=1%2C2%2C3&hourly_rate=70-&paging=NaN-undefined&q=full%20stack%20developer&sort=recency&subcategory2_uid=1737190722360750082%2C531770282589057026%2C531770282589057032%2C531770282589057030%2C531770282589057031%2C531770282589057028%2C531770282584862733&t=0%2C1&api_params=1&securityToken=214a8bfc69cf536a3269bbe551d87b9d9b5811812d1a24f3a3d08228c63d7386390e7873df86eff795747ea4229b6222b53e43fd0c0eafdcbe04f7486cc32c22&userUid=493655010797502464&orgUid=493655010810085377",
            last_polled=last_polled,
        )

    def test_read_feed(self):
        new_jobs = RSSJobFeed(self.job_feed).update()
        print(new_jobs)
        assert True is False
