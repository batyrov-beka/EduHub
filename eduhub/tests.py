"""
EduHub — автоматтык тесттер.
Иштетүү:  python manage.py test eduhub
"""
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from Dashboard.models import Notification
from forms.models import Application, Resume
from jobs.models import Job
from users.models import CustomUser, EmailOTP

PASSWORD = 'StrongPass123!'


def make_user(username, role, **extra):
    user = CustomUser.objects.create_user(username=username, email=f'{username}@test.kg', password=PASSWORD,
                                          role=role, is_verified=True, **extra)
    return user


def make_job(employer, **extra):
    data = dict(title='Python стажёр', company='Ош Софт', location='Ош', description='Описание',
                phone='+996700111222', salary=30000, category='it', job_type='Internship', posted_by=employer)
    data.update(extra)
    return Job.objects.create(**data)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
                   TELEGRAM_BOT_TOKEN=None, LANGUAGE_CODE='ru')
class BaseTestCase(TestCase):
    def setUp(self):
        self.student = make_user('student1', 'student', first_name='Айбек')
        self.employer = make_user('employer1', 'employer')
        self.other_employer = make_user('employer2', 'employer')
        self.admin = CustomUser.objects.create_superuser('admin', 'admin@test.kg', PASSWORD)
        self.job = make_job(self.employer)
        self.resume = Resume.objects.create(user=self.student, full_name='Айбек Токтогулов', phone='+996555000111',
                                            education='ОшМУ', experience='-', skills='Python, Django')

    def login(self, user):
        self.client.login(username=user.username, password=PASSWORD)


class RegistrationTests(BaseTestCase):
    def test_student_registration_with_otp(self):
        response = self.client.post(reverse('register'), {
            'username': 'newstudent', 'email': 'new@test.kg', 'role': 'student',
            'password1': PASSWORD, 'password2': PASSWORD,
        })
        self.assertRedirects(response, reverse('verify_otp'))
        user = CustomUser.objects.get(username='newstudent')
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)

        code = EmailOTP.objects.get(user=user).otp_code
        self.client.post(reverse('verify_otp'), {'otp': '000000' if code != '000000' else '111111'})
        user.refresh_from_db()
        self.assertFalse(user.is_active)  # туура эмес код

        self.client.post(reverse('verify_otp'), {'otp': code})
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_verified)

    def test_duplicate_email_rejected(self):
        response = self.client.post(reverse('register'), {
            'username': 'x', 'email': 'student1@test.kg', 'role': 'student',
            'password1': PASSWORD, 'password2': PASSWORD,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(username='x').exists())

    def test_employer_must_give_company_data(self):
        response = self.client.post(reverse('register'), {
            'username': 'comp', 'email': 'comp@test.kg', 'role': 'employer',
            'password1': PASSWORD, 'password2': PASSWORD,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(username='comp').exists())

    def test_blocked_user_cannot_login(self):
        self.student.is_blocked = True
        self.student.save()
        self.client.post(reverse('login'), {'username': 'student1', 'password': PASSWORD})
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_by_email(self):
        self.client.post(reverse('login'), {'username': 'student1@test.kg', 'password': PASSWORD})
        self.assertIn('_auth_user_id', self.client.session)


class JobTests(BaseTestCase):
    def test_list_and_filters(self):
        make_job(self.employer, title='Дизайнер', category='design', salary=50000)
        make_job(self.employer, title='Закрытая', is_active=False)
        url = reverse('vacancy_list')
        self.assertContains(self.client.get(url), 'Python стажёр')
        self.assertNotContains(self.client.get(url), 'Закрытая')
        response = self.client.get(url, {'category': 'design'})
        self.assertContains(response, 'Дизайнер')
        self.assertNotContains(response, 'Python стажёр')
        response = self.client.get(url, {'salary_min': 40000})
        self.assertContains(response, 'Дизайнер')
        self.assertNotContains(response, 'Python стажёр')

    def test_student_cannot_post_job(self):
        self.login(self.student)
        self.client.post(reverse('post_job'), {'title': 'Hack'})
        self.assertFalse(Job.objects.filter(title='Hack').exists())

    def test_employer_posts_job(self):
        self.login(self.employer)
        response = self.client.post(reverse('post_job'), {
            'title': 'Junior Django', 'company': 'Ош Софт', 'category': 'it', 'job_type': 'Full-time',
            'location': 'Ош', 'salary': 40000, 'phone': '+996700111222', 'description': 'Текст',
        })
        self.assertRedirects(response, reverse('profile'))
        self.assertTrue(Job.objects.filter(title='Junior Django', posted_by=self.employer).exists())

    def test_only_owner_or_admin_can_delete(self):
        self.login(self.other_employer)
        self.client.post(reverse('delete_job', args=[self.job.pk]))
        self.assertTrue(Job.objects.filter(pk=self.job.pk).exists())
        self.login(self.admin)
        self.client.post(reverse('delete_job', args=[self.job.pk]))
        self.assertFalse(Job.objects.filter(pk=self.job.pk).exists())

    def test_other_employer_cannot_edit(self):
        self.login(self.other_employer)
        self.assertEqual(self.client.get(reverse('edit_vacancy', args=[self.job.pk])).status_code, 404)


class ApplicationTests(BaseTestCase):
    def apply(self):
        self.login(self.student)
        return self.client.post(reverse('apply_to_vacancy', args=[self.job.pk]), {'cover_letter': 'Здравствуйте'})

    def test_apply_creates_application_and_notifies(self):
        self.apply()
        self.assertEqual(Application.objects.filter(vacancy=self.job, student=self.student).count(), 1)
        self.assertTrue(Notification.objects.filter(user=self.employer).exists())
        self.assertEqual(len(mail.outbox), 1)

    def test_cannot_apply_twice(self):
        self.apply()
        self.apply()
        self.assertEqual(Application.objects.filter(vacancy=self.job, student=self.student).count(), 1)

    def test_cannot_apply_to_closed_job(self):
        self.job.is_active = False
        self.job.save()
        self.apply()
        self.assertFalse(Application.objects.exists())

    def test_employer_changes_status(self):
        self.apply()
        app = Application.objects.get()
        self.login(self.employer)
        self.client.post(reverse('update_status', args=[app.pk, 'accepted']))
        app.refresh_from_db()
        self.assertEqual(app.status, 'accepted')
        self.assertTrue(Notification.objects.filter(user=self.student).exists())

    def test_invalid_status_and_foreign_employer(self):
        self.apply()
        app = Application.objects.get()
        self.login(self.employer)
        self.client.post(reverse('update_status', args=[app.pk, 'hacked']))
        self.login(self.other_employer)
        self.client.post(reverse('update_status', args=[app.pk, 'rejected']))
        app.refresh_from_db()
        self.assertEqual(app.status, 'pending')

    def test_resume_privacy(self):
        url = reverse('view_student_resume', args=[self.resume.pk])
        self.login(self.other_employer)
        self.assertRedirects(self.client.get(url), reverse('home'))
        self.apply()
        self.login(self.employer)  # арыз алган иш берүүчү көрө алат
        self.assertContains(self.client.get(url), 'Айбек Токтогулов')


class AdminTests(BaseTestCase):
    def test_dashboard_requires_superuser(self):
        self.login(self.student)
        self.assertNotEqual(self.client.get(reverse('admin_control')).status_code, 200)
        self.login(self.admin)
        self.assertEqual(self.client.get(reverse('admin_control')).status_code, 200)

    def test_csv_export(self):
        self.login(self.admin)
        for kind in ('students', 'jobs', 'applications'):
            response = self.client.get(reverse('export_csv', args=[kind]))
            self.assertEqual(response.status_code, 200)
            self.assertIn('text/csv', response['Content-Type'])

    def test_unverified_employer_sees_waiting_page(self):
        pending = make_user('newcompany', 'employer')
        pending.is_verified = False
        pending.save()
        self.login(pending)
        self.assertContains(self.client.get(reverse('vacancy_list')), 'На проверке')
        self.login(self.admin)
        self.client.post(reverse('approve_user', args=[pending.pk]))
        pending.refresh_from_db()
        self.assertTrue(pending.is_verified)

    def test_broadcast(self):
        self.login(self.admin)
        self.client.post(reverse('send_broadcast'), {'message': 'Ярмарка вакансий', 'audience': 'student'})
        self.assertTrue(Notification.objects.filter(user=self.student, message='Ярмарка вакансий').exists())
        self.assertFalse(Notification.objects.filter(user=self.employer, message='Ярмарка вакансий').exists())


class PagesSmokeTests(BaseTestCase):
    def test_public_pages_open(self):
        for name in ('home', 'vacancy_list', 'material_list', 'question_list', 'login', 'register'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        self.assertEqual(self.client.get(reverse('vacancy_detail', args=[self.job.pk])).status_code, 200)

    def test_cabinets_open(self):
        self.login(self.student)
        for name in ('student_applications', 'view_resume', 'my_resume', 'notifications', 'account_settings'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        self.login(self.employer)
        for name in ('profile', 'employer_dashboard', 'post_job'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
