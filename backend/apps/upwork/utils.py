import re
import time
import feedparser
from datetime import datetime
from openai import OpenAI

from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string


class UpworkJobAssistant:

    def __init__(self, job_feed, api_key=None, project_id=None):
        self.job_feed = job_feed
        self.api_key = api_key or settings.OPEN_AI_API_KEY
        self.project_id = project_id or settings.OPEN_AI_PROJECT_ID
        self.client = OpenAI(
            api_key=self.api_key,
            project=self.project_id,
        )
        self.assistant = self.get_or_create_assistant()

    def get_or_create_assistant(self):
        if self.job_feed.assistant_id:
            return self.get_assistant()

        assistant = self.create_assistant()
        self.job_feed.assistant_id = assistant.id
        return assistant

    def create_assistant(self):
        return self.client.beta.assistants.create(
            instructions=self.job_feed.assistant_instructions,
            name=f"{self.job_feed.name} Assistant",
            model="gpt-3.5-turbo",
        )

    def get_assistant(self):
        return self.client.beta.assistants.retrieve(
            self.job_feed.assistant_id
        )

    def create_thread(self):
        return self.client.beta.threads.create()

    def create_message(self, thread, content):
        return self.client.beta.threads.messages.create(
            thread.id,
            role="user",
            content=content,
        )

    def create_thread_and_run(self, content):
        my_run = self.client.beta.threads.create_and_run(
            assistant_id=self.assistant.id,
            thread={
                "messages": [
                    {
                        "role": "user",
                        "content": content
                    }
                ]
            },
            max_completion_tokens=50,
        )
        success = False
        while my_run.status in ["queued", "in_progress"]:
            keep_retrieving_run = self.client.beta.threads.runs.retrieve(
                thread_id=my_run.thread_id,
                run_id=my_run.id
            )

            if keep_retrieving_run.status == "completed":

                # Step 6: Retrieve the Messages added by the Assistant to the Thread
                all_messages = self.client.beta.threads.messages.list(
                    thread_id=my_run.thread_id
                )

                assistant_rep = all_messages.data[0].content[0].text.value
                print(assistant_rep)
                if assistant_rep != 'no':
                    success = True
                break
            elif keep_retrieving_run.status == "queued" or keep_retrieving_run.status == "in_progress":
                pass
            else:
                break
        return success


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

    def validate_with_open_ai(self, job_data):
        if settings.OPEN_AI_API_KEY:
            assistant = UpworkJobAssistant(job_feed=self.job_feed)
            content = f"Reply 'no' if I do not meet the qualifications for this job.\n\n {job_data['content']}"
            return assistant.create_thread_and_run(content=content)
        return True

    def job_posting_is_valid(self, job_data):
        if job_data.get('hourly_high'):
            if job_data['hourly_high'] < 60:
                return False
        if job_data.get('budget'):
            if job_data['budget'] < 3000:
                return False

        ai_valid = self.validate_with_open_ai(job_data=job_data)
        print(ai_valid)
        if not ai_valid:
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
        formatted_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        subject = f"{self.job_feed.name} - {formatted_time }"
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
            self.job_feed.save()
            return True

        return False
