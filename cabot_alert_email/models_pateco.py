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

email_template_haproxy = """Service {{ service.name }} {{ scheme }}://{{ host }}{% url 'service' pk=service.id %}{% if service.overall_status != service.PASSING_STATUS %}alerting with status: {{ service.overall_status }}{% else %}is back to normal{% endif %}.
{% if service.overall_status != service.PASSING_STATUS %}
CHECKS FAILING:{% for check in service.all_failing_checks %}
  SERVICE FAILING - {{ check.name }} - NODE: {{ check.last_result.error|safe }} {% endfor %}
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
        resp = "Hello World NA"
        c = Context({
            'service': service,
            'host': settings.WWW_HTTP_HOST,
            'scheme': settings.WWW_SCHEME,
            'resp': resp
        })
        if service.overall_status != service.PASSING_STATUS:
            for check in service.all_failing_checks():
                alltype += str(check.name)
                alltype += " | "
            if service.overall_status == service.CRITICAL_STATUS:
                emails += [u.email for u in users if u.email]
            # subject = '%s status for service: %s *** | %s ***' % (
            subject = '[Pateco Alerts] Service [%s] %s *** | %s *** ' % (
                service.name, service.overall_status, alltype)
        else:
            for check in service.all_passing_checks():
                alltype += str(check.name)
                alltype += " | "
            subject = '[Pateco Alerts] Service [%s] OK' % (service.name)

        if service.name == "HAProxy":
            t = Template(email_template_haproxy)
        else:        
            t = Template(email_template)
        send_mail(
            subject=subject,
            message=t.render(c),
            # from_email='Cabot <%s>' % env.get('CABOT_FROM_EMAIL'),
            from_email='Cabot PATECO',
            recipient_list=emails,
        )
