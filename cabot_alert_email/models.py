from os import environ as env

from django.conf import settings
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.template import Context, Template

from cabot.cabotapp.alert import AlertPlugin

import requests
import logging

email_template = """Service: {{ service.name }} ({{ scheme }}://{{ host }}{% url 'service' pk=service.id %}) {% if service.overall_status != service.PASSING_STATUS %}alerting with status: {{ service.overall_status }}{% else %}is back to normal{% endif %}.
{% if service.overall_status != service.PASSING_STATUS %}
CHECKS FAILING:{% for check in service.all_failing_checks %}
  FAILING - {{ check.name }} - Metric: {{ check.metric }} - Value:  {{ check.last_result.error|safe }} {% endfor %}
{% if service.all_passing_checks %}
PASSING CHECKS:{% for check in service.all_passing_checks %}
  PASSING - {{ check.name }} - Metric: {{ check.metric }} - Value: {{ check.last_result.error|safe }} - OK {% endfor %}
{% endif %}
{% endif %}
"""


class EmailAlert(AlertPlugin):
    name = "Email"
    author = "Jonathan Balls"

    def send_alert(self, service, users, duty_officers):
        alltype = ""
        emails = [u.email for u in users if u.email]
        if not emails:
            return
        c = Context({
            'service': service,
            'host': settings.WWW_HTTP_HOST,
            'scheme': settings.WWW_SCHEME,
        })
        if service.overall_status == service.PASSING_STATUS:
            subject = '[OK] %s' % (service.name)
        else:
            subject = '[%s] %s' % (service.overall_status, service.name)
    
        t = Template(email_template)
        
        send_mail(
            subject=subject,
            message=t.render(c),
            # from_email='Cabot <%s>' % env.get('CABOT_FROM_EMAIL'),
            from_email='Cabot UIZA',
            recipient_list=emails,
        )
