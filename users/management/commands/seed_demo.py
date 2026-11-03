import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from Dashboard.models import Notification
from forms.models import Application, Resume
from forum.models import Answer, Question
from jobs.models import Job

User = get_user_model()
PASSWORD = 'demo12345'

EMPLOYERS = [
    ('osh_soft', 'Ош Софт', 'hr@oshsoft.kg', '+996700111222'),
    ('alai_market', 'Алай Маркет', 'job@alaimarket.kg', '+996555333444'),
    ('nur_design', 'Нур Дизайн Студио', 'team@nurdesign.kg', '+996777555666'),
    ('bilim_center', 'Билим Окуу Борбору', 'info@bilim-center.kg', '+996502777888'),
]

STUDENTS = [
    ('aibek', 'Айбек', 'Токтогулов', 'aibek@student.oshsu.kg', 'Python, Django, SQL, Git, HTML, CSS',
     'ОшМУ, Математика жана информатика факультети, 4-курс', 'Студенттик долбоорлор: онлайн китепкана (Django).'),
    ('aizada', 'Айзада', 'Мамытова', 'aizada@student.oshsu.kg', 'Figma, Photoshop, UI/UX, Illustrator',
     'ОшМУ, Дизайн бөлүмү, 3-курс', 'Фриланс: 10дон ашык логотип жана баннер.'),
    ('nurlan', 'Нурлан', 'Абдыкадыров', 'nurlan@student.oshsu.kg', 'SMM, Marketing, Excel, Canva',
     'ОшМУ, Экономика факультети, 4-курс', 'Instagram баракчаларын жүргүзүү тажрыйбасы — 1 жыл.'),
    ('meerim', 'Мээрим', 'Жээнбекова', 'meerim@student.oshsu.kg', 'JavaScript, React, HTML, CSS, Python',
     'ОшМУ, Колдонмо информатика, 3-курс', 'Хакатондун катышуучусу, React менен портфолио сайт.'),
    ('bektur', 'Бектур', 'Сапаров', 'bektur@student.oshsu.kg', 'Excel, 1C, Word, Администрирование',
     'ОшМУ, Бизнес жана башкаруу, 4-курс', 'Окуу практикасы: банктын филиалында ассистент.'),
]

JOBS = [
    # (employer_index, title, category, job_type, salary, location, description)
    (0, 'Junior Python/Django разработчик', 'it', 'Full-time', 45000, 'Ош',
     'Ищем начинающего разработчика в команду веб-проектов.\n\nТребования:\n— знание Python и Django\n'
     '— базовый SQL, Git\n— желание учиться\n\nУсловия: наставник, гибкий график, официальное оформление.'),
    (0, 'Стажёр Frontend (React)', 'it', 'Internship', 20000, 'Ош',
     'Стажировка 3 месяца с возможностью трудоустройства.\n\nТребования: HTML, CSS, JavaScript, основы React.'),
    (0, 'QA-тестировщик (стажировка)', 'it', 'Internship', 15000, 'Ош',
     'Ручное тестирование веб и мобильных приложений, составление баг-репортов. Обучим с нуля.'),
    (0, 'Python-разработчик (удалённо)', 'it', 'Remote', 60000, 'Удалённо',
     'Разработка внутренних сервисов на Django REST Framework. Опыт от 6 месяцев или сильное портфолио.'),
    (1, 'SMM-специалист', 'marketing', 'Part-time', 25000, 'Ош',
     'Ведение Instagram и TikTok сети магазинов: контент-план, съёмка, сторис, реклама.'),
    (1, 'Помощник маркетолога', 'marketing', 'Internship', 15000, 'Ош',
     'Анализ конкурентов, подготовка акций, работа с отзывами покупателей. Подходит студентам 3–4 курса.'),
    (1, 'Администратор магазина', 'admin', 'Full-time', 30000, 'Ош',
     'Контроль работы зала, работа с кассой и 1С, ведение отчётности. График 5/2.'),
    (2, 'Графический дизайнер', 'design', 'Part-time', 30000, 'Ош',
     'Создание баннеров, логотипов и макетов для соцсетей. Обязательно портфолио (Behance, Dribbble).'),
    (2, 'UI/UX дизайнер (стажировка)', 'design', 'Internship', 18000, 'Ош',
     'Проектирование интерфейсов мобильных приложений в Figma под руководством арт-директора.'),
    (2, 'Motion-дизайнер', 'design', 'Remote', 40000, 'Удалённо',
     'Анимация рекламных роликов (After Effects). Оплата по результатам тестового задания.'),
    (3, 'Преподаватель программирования для детей', 'it', 'Part-time', 28000, 'Ош',
     'Проведение занятий по Scratch и Python для школьников 10–15 лет. 3 раза в неделю, вечером.'),
    (3, 'Офис-менеджер', 'admin', 'Full-time', 27000, 'Ош',
     'Приём звонков, запись учеников, ведение документации и базы клиентов в Excel.'),
    (3, 'Менеджер по работе с клиентами', 'other', 'Full-time', 32000, 'Жалал-Абад',
     'Консультации родителей и учеников, продажа курсов, работа с CRM. Обучение за счёт компании.'),
    (1, 'Курьер (гибкий график)', 'other', 'Part-time', None, 'Ош',
     'Доставка заказов по городу. Оплата договорная, подходит для совмещения с учёбой.'),
]

QUESTIONS = [
    ('Как подготовиться к первому собеседованию на Junior?', 'python карьера собеседование',
     'Скоро первое собеседование на позицию Junior Python. Какие вопросы обычно задают и что повторить?',
     ['Повторите ООП, типы данных, работу со списками и словарями. Обязательно расскажите о своих проектах.',
      'Подготовьте GitHub с 2–3 проектами. Работодатели часто смотрят код больше, чем диплом.']),
    ('Стоит ли идти на неоплачиваемую стажировку?', 'стажировка карьера',
     'Предлагают стажировку без оплаты на 2 месяца. Есть ли смысл соглашаться?',
     ['Если компания даёт наставника и реальные задачи — опыт того стоит. Уточните условия трудоустройства после.']),
    ('Какой формат резюме лучше для дизайнера?', 'дизайн резюме',
     'Делать резюме в виде PDF или ссылку на портфолио?', []),
]


class Command(BaseCommand):
    help = "Демо-маалыматтарды түзүү (коргоо үчүн)"

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true',
                            help='Мурунку вакансияларды, арыздарды жана форумду өчүрүү')

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(42)
        now = timezone.now()

        if options['reset']:
            Application.objects.all().delete()
            Job.objects.all().delete()
            Question.objects.all().delete()
            Notification.objects.all().delete()
            self.stdout.write(self.style.WARNING('Мурунку маалыматтар өчүрүлдү.'))

        employers = []
        for username, company, email, phone in EMPLOYERS:
            user, created = User.objects.get_or_create(username=username, defaults={
                'email': email, 'role': 'employer', 'is_verified': True, 'phone': phone,
                'first_name': company, 'verification_data': f'ИНН 0{random.randint(10**12, 10**13 - 1)}',
            })
            if created:
                user.set_password(PASSWORD)
                user.save()
            employers.append((user, company, phone))

        students = []
        for username, first, last, email, skills, edu, exp in STUDENTS:
            user, created = User.objects.get_or_create(username=username, defaults={
                'email': email, 'role': 'student', 'is_verified': True, 'first_name': first,
                'last_name': last, 'university': 'Ошский государственный университет',
                'phone': f'+99670{random.randint(1000000, 9999999)}',
            })
            if created:
                user.set_password(PASSWORD)
                user.save()
            Resume.objects.update_or_create(user=user, defaults={
                'full_name': f'{first} {last}', 'phone': user.phone, 'education': edu,
                'experience': exp, 'skills': skills,
                'about_me': 'Ответственный, быстро обучаюсь, ищу первую работу или стажировку по специальности.',
            })
            students.append(user)

        jobs = []
        for i, (emp_idx, title, cat, jtype, salary, loc, desc) in enumerate(JOBS):
            employer, company, phone = employers[emp_idx]
            job, _ = Job.objects.get_or_create(title=title, posted_by=employer, defaults={
                'company': company, 'phone': phone, 'category': cat, 'job_type': jtype,
                'salary': salary, 'location': loc, 'description': desc,
            })
            Job.objects.filter(pk=job.pk).update(created_at=now - timedelta(days=i, hours=random.randint(0, 20)))
            jobs.append(job)

        statuses = ['pending', 'pending', 'accepted', 'rejected']
        created_apps = 0
        for student in students:
            resume = student.resume
            for job in random.sample(jobs, 3):
                app, created = Application.objects.get_or_create(vacancy=job, student=student, defaults={
                    'resume': resume, 'status': random.choice(statuses),
                    'cover_letter': 'Здравствуйте! Меня заинтересовала ваша вакансия, готов(а) пройти собеседование.',
                })
                if created:
                    Application.objects.filter(pk=app.pk).update(
                        created_at=now - timedelta(days=random.randint(0, 13), hours=random.randint(0, 23)))
                    created_apps += 1

        for title, tags, content, answers in QUESTIONS:
            author = random.choice(students)
            q, created = Question.objects.get_or_create(title=title, defaults={
                'author': author, 'tags': tags, 'content': content})
            if created:
                for text in answers:
                    a = Answer.objects.create(question=q, author=random.choice(employers)[0], content=text)
                    a.likes.add(*random.sample(students, 2))

        self.stdout.write(self.style.SUCCESS(
            f'Даяр! Иш берүүчүлөр: {len(employers)}, студенттер: {len(students)}, '
            f'вакансиялар: {len(jobs)}, жаңы арыздар: {created_apps}. Сырсөз: {PASSWORD}'
        ))
