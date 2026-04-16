from django.test import TestCase

# Create your tests here.
import requests
token = "8671398522:AAF2pivRcTTAm6Ytl-77EExSFrxheNWZIt4"
chat_id = "@eduhub_kg_jobs"
url = f"https://api.telegram.org/bot{token}/sendMessage"
r = requests.post(url, data={'chat_id': chat_id, 'text': 'Тест билдирүү'})
print(r.text)