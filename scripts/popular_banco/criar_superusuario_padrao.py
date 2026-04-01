from django.contrib.auth.models import User


def run(username='nome', email='', password='123'):
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'is_superuser': True,
            'is_staff': True,
        },
    )

    user.email = email
    user.is_superuser = True
    user.is_staff = True
    user.set_password(password)
    user.save()

    return {
        'created': created,
        'username': username,
        'email': user.email,
        'password': password,
    }
