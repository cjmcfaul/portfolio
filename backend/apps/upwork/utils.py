import re

import feedparser
from datetime import datetime

from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string


class RSSJobFeed:

    def __init__(self, job_feed):
        self.job_feed = job_feed
        self.new_jobs = []

    def parse_payment_details(self, content):
        low_rate, high_rate, budget = None, None, None
        # Search for Hourly Rate
        match = re.search(r"Hourly Range</b>:\s*\$([0-9,]+\.\d{2})-\$([0-9,]+\.\d{2})", content)
        if match:
            low_rate = int(float(match.group(1).replace(",", "")))
            high_rate = int(float(match.group(2).replace(",", "")))
        else:
            match = re.search(r"<b>Budget</b>:\s*\$([0-9]+)", content)
            if match:
                budget = int(match.group(1))

        return {
            "budget": budget,
            "hourly_low": low_rate,
            "hourly_high": high_rate,
        }

    def parse_skills(self, content):
        matches = re.findall(r"<b>Skills</b>:\s*([^<]+)", content)

        skills = []
        for match in matches:
            skills.extend(skill.strip() for skill in match.split(','))

        # Remove duplicates and sort the skills
        skills = sorted(set(skills))
        return {
            "skills": skills
        }

    def parse_country(self, content):
        country = None
        match = re.search(r"<b>Country</b>:\s*([^<]+)", content)
        if match:
            country = match.group(1).strip()
        return {
            "country": country
        }

    def parse_job_data(self, entry):
        content = entry['summary']
        return {
            "title": entry['title'],
            "url": entry['link'],
            "content": entry['summary'],
            **self.parse_payment_details(content),
            **self.parse_skills(content),
            **self.parse_country(content)
        }

    def job_posting_is_valid(self, job_data):
        if job_data.get('hourly_high'):
            if job_data['hourly_high'] < 60:
                return False
        if job_data.get('budget'):
            if job_data['budget'] < 3000:
                return False

        return True

    def read_feed(self):
        try:
            response = feedparser.parse(self.job_feed.url)
        except Exception as e:
            print(str(e))
            return

        return response.entries

    def send_jobs_email(self):
        subject = f"{self.job_feed.name}"
        data = {
            "feed": self.job_feed,
            "jobs": self.new_jobs,
        }
        text_content = render_to_string('emails/upwork/text/new_job_postings.txt', data)
        html_content = render_to_string('emails/upwork/html/new_job_postings.html', data)
        send_mail(
            subject=subject,
            from_email="hi@colinmcfaul.com",
            recipient_list=[self.job_feed.recipients],
            message=text_content,
            html_message=html_content,
        )

    def update(self):
        entries = self.read_feed()
        if not entries:
            return False

        for job in entries:
            parsed_date = datetime.strptime(job.published, "%a, %d %b %Y %H:%M:%S %z")
            if parsed_date > self.job_feed.last_polled:
                new_job = self.parse_job_data(job)
                if self.job_posting_is_valid(new_job):
                    self.new_jobs.append(new_job)

        if len(self.new_jobs) > 0:
            self.send_jobs_email()
            self.job_feed.last_polled = timezone.now()
            return True

        return False
