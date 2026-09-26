"""
Seed demo data for the Library app (schema `library` on shared Postgres).

Idempotent-ish: users via update_or_create; categories/publishers/books by name/title;
members by email; prior BorrowRecord rows with created_by=seed_demo are replaced.

Preferred command (run from a host that can reach managed Postgres):

  cd /path/to/Library
  export $(grep -v '^#' .env  # gitignored DATABASE_URL | grep -v '^$' | xargs)
  .venv/bin/python scripts/seed_library_demo.py

All logic lives inside run() so `manage.py shell < thisfile` also works
(Django shell stdin exec does not bind module-level names into nested scopes).
"""
from __future__ import print_function

def run():
    import os
    import sys
    from datetime import timedelta

    # Bootstrap Django when executed as a standalone script
    if "DJANGO_SETTINGS_MODULE" not in os.environ:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    # __file__ missing when exec'd via manage.py shell < stdin
    try:
        _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    except NameError:
        _root = os.getcwd()
    if _root not in sys.path:
        sys.path.insert(0, _root)
    import django
    from django.conf import settings as dj_settings

    if not dj_settings.configured:
        django.setup()
    else:
        # manage.py already configured settings; apps should be ready
        pass

    from django.contrib.auth.models import User
    from django.db import transaction
    from django.utils import timezone

    from book.models import (
        Book,
        BorrowRecord,
        Category,
        Member,
        Publisher,
        UserActivity,
    )
    from comment.models import Comment

    seed_tag = "seed_demo"
    now = timezone.now()

    book_specs = [
        ("George Orwell", "1984", "Dystopian classic about surveillance."),
        ("Jane Austen", "Pride Prejudice", "Romance and social satire."),
        ("Mary Shelley", "Frankenstein", "Gothic science fiction pioneer."),
        ("Homer", "The Odyssey", "Epic journey of Odysseus."),
        ("Plato", "The Republic", "Foundational political philosophy."),
        ("Sun Tzu", "Art of War", "Strategy and leadership."),
        ("Darwin", "Origin Species", "Theory of natural selection."),
        ("Ada Lovelace", "Notes on Babbage", "Early computing insights."),
        ("Tolkien", "The Hobbit", "Adventure in Middle-earth."),
        ("Asimov", "Foundation", "Psychohistory and galactic empires."),
        ("Feynman", "Surely Joking", "Physics anecdotes and insight."),
        ("Sagan", "Cosmos", "Popular science of the universe."),
        ("Hawking", "Brief History", "Time, space, and black holes."),
        ("Knuth", "Art of Code 1", "Algorithms and programming."),
        ("Martin", "Clean Code", "Craftsmanship for software."),
        ("Beck", "TDD by Example", "Test-driven development primer."),
        ("Rowling", "Harry Potter 1", "The boy who lived begins."),
        ("Lewis", "Narnia Wardrobe", "Portal fantasy for children."),
        ("Seuss", "Green Eggs Ham", "Rhyming children's classic."),
        ("Curie", "Radioactivity", "Notes on radioactive research."),
    ]

    member_specs = [
        ("Alice Martin", 28, "f", "Paris", "alice.martin@example.com", "+33111111101"),
        ("Bob Dupont", 34, "m", "Lyon", "bob.dupont@example.com", "+33111111102"),
        ("Clara Nguyen", 22, "f", "Marseille", "clara.nguyen@example.com", "+33111111103"),
        ("David Rossi", 41, "m", "Nice", "david.rossi@example.com", "+33111111104"),
        ("Emma Weber", 29, "f", "Toulouse", "emma.weber@example.com", "+33111111105"),
        ("Farid Benali", 37, "m", "Lille", "farid.benali@example.com", "+33111111106"),
        ("Gina Costa", 25, "f", "Bordeaux", "gina.costa@example.com", "+33111111107"),
        ("Hugo Lefevre", 31, "m", "Nantes", "hugo.lefevre@example.com", "+33111111108"),
        ("Ines Moreau", 27, "f", "Strasbourg", "ines.moreau@example.com", "+33111111109"),
        ("Jules Petit", 45, "m", "Rennes", "jules.petit@example.com", "+33111111110"),
        ("Karim Saidi", 33, "m", "Grenoble", "karim.saidi@example.com", "+33111111111"),
        ("Lea Bernard", 24, "f", "Montpellier", "lea.bernard@example.com", "+33111111112"),
    ]

    with transaction.atomic():
        print("Seeding Library demo data (%s)..." % seed_tag)

        admin, created_admin = User.objects.update_or_create(
            username="admin",
            defaults={
                "email": "admin@library.local",
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )
        admin.set_password("admin")
        admin.save()
        print("admin: created=%s superuser=%s" % (created_admin, admin.is_superuser))

        staff, created_staff = User.objects.update_or_create(
            username="staff",
            defaults={
                "email": "staff@library.local",
                "is_staff": True,
                "is_superuser": False,
                "is_active": True,
            },
        )
        staff.set_password("staff")
        staff.save()
        print(
            "staff: created=%s is_staff=%s superuser=%s"
            % (created_staff, staff.is_staff, staff.is_superuser)
        )

        cat_names = [
            "Fiction",
            "Science",
            "History",
            "Biography",
            "Technology",
            "Children",
        ]
        categories = []
        for name in cat_names:
            obj, _ = Category.objects.update_or_create(
                name=name, defaults={"created_at": now}
            )
            categories.append(obj)
        print("categories: %s" % len(categories))

        pub_data = [
            ("Penguin Books", "London", "contact@penguin.example"),
            ("O'Reilly Media", "Sebastopol", "info@oreilly.example"),
            ("HarperCollins", "New York", "hello@harper.example"),
            ("MIT Press", "Cambridge", "press@mit.example"),
        ]
        publishers = []
        for name, city, contact in pub_data:
            obj, _ = Publisher.objects.update_or_create(
                name=name,
                defaults={
                    "city": city,
                    "contact": contact,
                    "updated_by": seed_tag,
                    "created_at": now,
                },
            )
            publishers.append(obj)
        print("publishers: %s" % len(publishers))

        books = []
        title_limit = Book._meta.get_field("title").max_length
        for i, (author, title, description) in enumerate(book_specs):
            assert len(title) <= title_limit, title
            obj, _ = Book.objects.update_or_create(
                title=title,
                defaults={
                    "author": author[:20],
                    "description": description,
                    "category": categories[i % len(categories)],
                    "publisher": publishers[i % len(publishers)],
                    "quantity": 5 + (i % 8),
                    "status": 1,
                    "floor_number": (i % 3) + 1,
                    "bookshelf_number": "%04d" % (i + 1),
                    "updated_by": seed_tag,
                    "total_borrow_times": i % 5,
                },
            )
            books.append(obj)
        print("books: %s" % len(books))

        members = []
        for name, age, gender, city, email, phone in member_specs:
            obj, _ = Member.objects.update_or_create(
                email=email,
                defaults={
                    "name": name,
                    "age": age,
                    "gender": gender,
                    "city": city,
                    "phone_number": phone,
                    "created_by": seed_tag,
                    "updated_by": seed_tag,
                    "created_at": now - timedelta(days=30),
                },
            )
            members.append(obj)
        print("members: %s" % len(members))

        deleted, _ = BorrowRecord.objects.filter(created_by=seed_tag).delete()
        if deleted:
            print("cleared prior seed borrows: %s" % deleted)

        # book/borrower are varchar names (PR #8), not FKs
        plans = [
            (0, 0, 3, 7, 0),
            (1, 1, 10, 7, 0),
            (2, 2, 20, 14, 1),
            (3, 3, 5, 7, 0),
            (4, 4, 15, 7, 1),
            (5, 5, 2, 14, 0),
            (6, 6, 25, 7, 1),
            (7, 7, 8, 7, 0),
            (8, 8, 1, 7, 0),
            (9, 9, 12, 10, 1),
            (10, 10, 4, 7, 0),
            (11, 11, 18, 7, 1),
            (12, 0, 6, 7, 0),
            (13, 2, 9, 14, 0),
            (14, 4, 30, 7, 1),
        ]
        for bi, mi, ago, period, status in plans:
            book = books[bi]
            member = members[mi]
            start = now - timedelta(days=ago)
            end = start + timedelta(days=period)
            rec = BorrowRecord(
                borrower=member.name[:20],
                borrower_card=member.card_number,
                borrower_email=member.email,
                borrower_phone_number=member.phone_number,
                book=book.title,
                quantity=1,
                start_day=start,
                end_day=end,
                periode=period,
                open_or_close=status,
                created_at=start,
                created_by=seed_tag,
                closed_by=admin.username if status == 1 else "",
                final_status="Closed" if status == 1 else "Unknown",
            )
            rec.save()
            Book.objects.filter(pk=book.pk).update(
                total_borrow_times=book.total_borrow_times + 1
            )
        print("borrow records: %s" % len(plans))

        Comment.objects.filter(
            user__username__in=["admin", "staff"], content__startswith="[seed]"
        ).delete()
        comment_samples = [
            (0, admin, "[seed] Classic — still chilling."),
            (1, staff, "[seed] Witty and sharp."),
            (8, admin, "[seed] Great for a rainy weekend."),
            (9, staff, "[seed] Foundation trilogy is essential."),
            (15, admin, "[seed] Excellent TDD intro."),
            (16, staff, "[seed] Kids love this one."),
        ]
        for bi, user, text in comment_samples:
            Comment.objects.create(
                book=books[bi], user=user, content=text, body=text
            )
        print("comments: %s" % len(comment_samples))

        UserActivity.objects.filter(
            created_by__in=["admin", "staff"], detail__startswith="[seed]"
        ).delete()
        UserActivity.objects.create(
            created_by=admin.username,
            operation_type="success",
            target_model="Book",
            detail="[seed] seeded demo catalog",
        )
        UserActivity.objects.create(
            created_by=staff.username,
            operation_type="info",
            target_model="BorrowRecord",
            detail="[seed] reviewed open loans",
        )
        print("user activities: 2 seed rows")

        print("--- counts (this DB) ---")
        print("User: %s" % User.objects.count())
        print("Category: %s" % Category.objects.count())
        print("Publisher: %s" % Publisher.objects.count())
        print("Book: %s" % Book.objects.count())
        print("Member: %s" % Member.objects.count())
        print("BorrowRecord: %s" % BorrowRecord.objects.count())
        print("Comment: %s" % Comment.objects.count())
        print("UserActivity: %s" % UserActivity.objects.count())
        print(
            "admin superuser: %s"
            % User.objects.filter(username="admin", is_superuser=True).exists()
        )
        print(
            "staff staff-only: %s"
            % User.objects.filter(
                username="staff", is_staff=True, is_superuser=False
            ).exists()
        )
        print("DONE")


run()
