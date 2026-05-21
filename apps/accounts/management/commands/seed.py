from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Subject
from apps.catalog.services import courses as course_service
from apps.content.services import structure
from apps.enrollment.services import enrolling
from apps.forums.services import discussions
from apps.progress.services import tracking
from apps.reviews.services import upsert_review
from core.enums import PricingModel, ProgressionMode, Role

User = get_user_model()
PASSWORD = "Test1234!pw"

SUBJECTS = [
    "Backend Engineering",
    "Frontend Engineering",
    "Data & Machine Learning",
    "Product Design",
    "DevOps & Cloud",
]

COURSES = [
    ("Production Django Patterns", "Backend Engineering", PricingModel.FREE, 0),
    ("Scaling PostgreSQL", "Backend Engineering", PricingModel.ONE_TIME, 79),
    ("Modern HTMX Interfaces", "Frontend Engineering", PricingModel.ONE_TIME, 49),
    ("Applied ML for Engineers", "Data & Machine Learning", PricingModel.SUBSCRIPTION, 0),
    ("Design Systems in Practice", "Product Design", PricingModel.FREE, 0),
    ("Kubernetes for Teams", "DevOps & Cloud", PricingModel.ONE_TIME, 99),
]

MODULES = ["Foundations", "Core concepts", "Going to production"]
LESSONS = ["Overview", "Hands-on walkthrough", "Common pitfalls", "Wrap-up"]


class Command(BaseCommand):
    help = "Seed the database with realistic demo data."

    @transaction.atomic
    def handle(self, *args, **options):
        instructors = self._instructors()
        subjects = {
            name: Subject.objects.get_or_create(name=name)[0] for name in SUBJECTS
        }
        students = self._students()

        for i, (title, subject_name, pricing, price) in enumerate(COURSES):
            owner = instructors[i % len(instructors)]
            course = self._course(owner, subjects[subject_name], title, pricing, price)
            self._build_curriculum(course)
            course_service.publish_course(course=course)
            self._enroll_and_engage(course, students)

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {len(COURSES)} courses, {len(instructors)} instructors, "
            f"{len(students)} students. Password: {PASSWORD}"
        ))

    def _instructors(self):
        data = [
            ("ada.lovelace@campus.test", "Ada Lovelace"),
            ("grace.hopper@campus.test", "Grace Hopper"),
            ("alan.kay@campus.test", "Alan Kay"),
        ]
        users = []
        for email, name in data:
            user, _ = User.objects.get_or_create(
                email=email, defaults={"full_name": name, "role": Role.INSTRUCTOR}
            )
            user.role = Role.INSTRUCTOR
            user.set_password(PASSWORD)
            user.save()
            users.append(user)
        return users

    def _students(self):
        users = []
        for n in range(1, 13):
            email = f"student{n}@campus.test"
            user, _ = User.objects.get_or_create(
                email=email, defaults={"full_name": f"Student {n}"}
            )
            user.set_password(PASSWORD)
            user.save()
            users.append(user)
        return users

    def _course(self, owner, subject, title, pricing, price):
        from apps.catalog.models import Course

        course = Course.objects.filter(owner=owner, title=title).first()
        if course:
            return course
        return course_service.create_course(
            owner=owner,
            subject=subject,
            title=title,
            headline=f"A practical, production-focused take on {subject.name.lower()}.",
            overview=(
                "This course rebuilds the fundamentals into patterns you can ship. "
                "Expect hands-on walkthroughs, realistic examples and production notes."
            ),
            pricing_model=pricing,
            price=price,
        )

    def _build_curriculum(self, course):
        if course.modules.exists():
            return
        course.progression_mode = ProgressionMode.SEQUENTIAL
        course.save(update_fields=["progression_mode"])
        for m_title in MODULES:
            module = structure.add_module(course=course, title=m_title)
            for i, l_title in enumerate(LESSONS):
                lesson = structure.add_lesson(
                    module=module, title=l_title, is_preview=(i == 0)
                )
                structure.add_content_item(
                    lesson=lesson,
                    kind="text",
                    title=l_title,
                    body=f"## {l_title}\n\nKey ideas and a worked example for **{course.title}**.",
                )

    def _enroll_and_engage(self, course, students):
        from apps.enrollment.selectors import is_enrolled

        first_lessons = []
        for module in course.modules.all():
            first_lessons.extend(list(module.lessons.all()))

        for idx, student in enumerate(students[:6]):
            if course.pricing_model != PricingModel.FREE and idx % 2 == 0:
                continue  # leave some paid courses without enrollment
            if is_enrolled(student=student, course=course):
                continue
            enrollment = enrolling.enroll(
                student=student, course=course, payment_verified=True
            )
            # First learner completes the whole course; others partially progress.
            lessons_to_do = first_lessons if idx == 0 else first_lessons[:2]
            for lesson in lessons_to_do:
                tracking.mark_lesson_complete(enrollment=enrollment, lesson=lesson)
            upsert_review(
                course=course,
                student=student,
                rating=5 - (idx % 3),
                body="Clear, practical and well structured.",
            )

        if not course.threads.exists():
            discussions.create_thread(
                course=course,
                author=course.owner,
                title="Welcome — introduce yourself",
                body="Tell the cohort what you're hoping to get out of this course.",
            )
