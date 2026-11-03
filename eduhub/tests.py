import os
import tempfile
from datetime import timedelta

from django.conf import settings
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

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
                   TELEGRAM_BOT_TOKEN=None, LANGUAGE_CODE='ru', SECURE_SSL_REDIRECT=False,
                   SESSION_COOKIE_SECURE=False, CSRF_COOKIE_SECURE=False)
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
            'password1': PASSWORD, 'password2': PASSWORD, 'consent': 'on',
        })
        self.assertRedirects(response, reverse('verify_otp'))
        user = CustomUser.objects.get(username='newstudent')
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)

        code = EmailOTP.objects.get(user=user).otp_code
        self.client.post(reverse('verify_otp'), {'otp': '000000' if code != '000000' else '111111'})
        user.refresh_from_db()
        self.assertFalse(user.is_active)

        self.client.post(reverse('verify_otp'), {'otp': code})
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_verified)

    def test_duplicate_email_rejected(self):
        response = self.client.post(reverse('register'), {
            'username': 'x', 'email': 'student1@test.kg', 'role': 'student',
            'password1': PASSWORD, 'password2': PASSWORD, 'consent': 'on',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(username='x').exists())

    def test_employer_must_give_company_data(self):
        response = self.client.post(reverse('register'), {
            'username': 'comp', 'email': 'comp@test.kg', 'role': 'employer',
            'password1': PASSWORD, 'password2': PASSWORD, 'consent': 'on',
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
        self.login(self.employer)
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


class ConsentTests(BaseTestCase):
    def signup(self, **extra):
        data = {'username': 'cs', 'email': 'cs@test.kg', 'role': 'student',
                'password1': PASSWORD, 'password2': PASSWORD}
        data.update(extra)
        return self.client.post(reverse('register'), data)

    def test_registration_requires_consent(self):
        response = self.signup()
        self.assertEqual(response.status_code, 200)
        self.assertIn('consent', response.context['form'].errors)
        self.assertFalse(CustomUser.objects.filter(username='cs').exists())

    def test_consent_time_is_saved(self):
        self.signup(consent='on')
        self.assertIsNotNone(CustomUser.objects.get(username='cs').consent_at)

    def test_privacy_page_opens_in_both_languages(self):
        for language in ('ru', 'ky'):
            response = self.client.get(f'/{language}/privacy/')
            self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Купуялуулук саясаты')

    def test_unverified_employer_can_open_privacy(self):
        self.employer.is_verified = False
        self.employer.save()
        self.login(self.employer)
        self.assertTemplateUsed(self.client.get(reverse('privacy')), 'users/privacy.html')


class OtpLimitTests(BaseTestCase):
    def start_registration(self):
        self.client.post(reverse('register'), {
            'username': 'otpuser', 'email': 'otp@test.kg', 'role': 'student',
            'password1': PASSWORD, 'password2': PASSWORD, 'consent': 'on',
        })
        return CustomUser.objects.get(username='otpuser')

    def wrong(self, code):
        return '000000' if code != '000000' else '111111'

    def test_correct_code_rejected_after_too_many_attempts(self):
        user = self.start_registration()
        otp = EmailOTP.objects.get(user=user)
        for _ in range(settings.OTP_MAX_ATTEMPTS):
            self.client.post(reverse('verify_otp'), {'otp': self.wrong(otp.otp_code)})
        self.client.post(reverse('verify_otp'), {'otp': otp.otp_code})
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_resend_is_limited_then_resets_attempts(self):
        user = self.start_registration()
        first = EmailOTP.objects.get(user=user)
        self.client.post(reverse('verify_otp'), {'otp': self.wrong(first.otp_code)})
        self.client.get(reverse('resend_registration_otp'))
        self.assertEqual(len(mail.outbox), 1)

        EmailOTP.objects.filter(user=user).update(
            created_at=timezone.now() - timedelta(seconds=settings.OTP_RESEND_SECONDS + 1))
        self.client.get(reverse('resend_registration_otp'))
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(EmailOTP.objects.get(user=user).attempts, 0)

    def test_password_reset_code_locks_after_too_many_attempts(self):
        self.client.post(reverse('custom_reset_form'), {'email': self.student.email})
        code = self.client.session['reset_otp']
        for _ in range(settings.OTP_MAX_ATTEMPTS):
            self.client.post(reverse('custom_reset_otp'), {'otp_code': self.wrong(code)})
        response = self.client.post(reverse('custom_reset_otp'), {'otp_code': code})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.client.session['reset_verified'])

    def test_password_reset_correct_code_still_works(self):
        self.client.post(reverse('custom_reset_form'), {'email': self.student.email})
        code = self.client.session['reset_otp']
        self.client.post(reverse('custom_reset_otp'), {'otp_code': self.wrong(code)})
        response = self.client.post(reverse('custom_reset_otp'), {'otp_code': code})
        self.assertRedirects(response, reverse('custom_reset_new'))


class DeleteAccountTests(BaseTestCase):
    def test_wrong_password_keeps_account(self):
        self.login(self.student)
        self.client.post(reverse('delete_account'), {'password': 'wrong'})
        self.assertTrue(CustomUser.objects.filter(pk=self.student.pk).exists())

    def test_student_deletes_account_and_resume(self):
        Application.objects.create(vacancy=self.job, student=self.student, resume=self.resume)
        self.login(self.student)
        self.client.post(reverse('delete_account'), {'password': PASSWORD})
        self.assertFalse(CustomUser.objects.filter(pk=self.student.pk).exists())
        self.assertFalse(Resume.objects.filter(pk=self.resume.pk).exists())
        self.assertFalse(Application.objects.exists())
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_uploaded_photos_are_removed_from_disk(self):
        with tempfile.TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            self.resume.photo = SimpleUploadedFile('r.jpg', b'x')
            self.resume.save()
            self.student.profile_picture = SimpleUploadedFile('p.jpg', b'x')
            self.student.save()
            paths = [self.resume.photo.path, self.student.profile_picture.path]
            self.assertTrue(all(os.path.exists(path) for path in paths))

            self.login(self.student)
            self.client.post(reverse('delete_account'), {'password': PASSWORD})
            self.assertFalse(any(os.path.exists(path) for path in paths))

    def test_get_does_not_delete(self):
        self.login(self.student)
        self.assertEqual(self.client.get(reverse('delete_account')).status_code, 405)
        self.assertTrue(CustomUser.objects.filter(pk=self.student.pk).exists())

    def test_admin_cannot_delete_self_here(self):
        self.login(self.admin)
        self.client.post(reverse('delete_account'), {'password': PASSWORD})
        self.assertTrue(CustomUser.objects.filter(pk=self.admin.pk).exists())

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.post(reverse('delete_account'), {'password': PASSWORD})
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])


class HttpsTests(BaseTestCase):
    @override_settings(SECURE_SSL_REDIRECT=True, SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https'))
    def test_http_redirects_and_proxied_https_does_not(self):
        url = reverse('privacy')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 301)
        self.assertTrue(response['Location'].startswith('https://'))
        self.assertEqual(self.client.get(url, headers={'x-forwarded-proto': 'https'}).status_code, 200)
