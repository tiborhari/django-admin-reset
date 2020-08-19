from binascii import b2a_hex
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from os import urandom
from re import search, sub
from sys import version_info
from unittest.mock import patch

import django
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode
from pytest import fixture, mark

from django_admin_reset.admin import _get_password_reset_token_expiry

pytestmark = [mark.django_db]


@fixture(autouse=True)
def check_no_user():
    """
    No user (except admin) should exists at the end of each test case.
    """
    try:
        yield
    finally:
        assert not User.objects.exclude(username='admin').exists()


@contextmanager
def manage_user(user):
    user.save()
    try:
        yield user
    finally:
        User.objects.get(pk=user.pk).delete()


@fixture
def staff_without_perm():
    user = User(username='staff', is_staff=True)
    user.set_password('staff')
    with manage_user(user):
        yield user


@fixture(params=[True, False])
def staff_with_perm(request, admin_user, client):
    is_admin = request.param
    if is_admin:
        client.login(username='admin', password='password')
        yield admin_user
        if version_info[0] == 2:
            raise StopIteration
        else:
            return

    user = User(username='staff', is_staff=True)
    user.set_password('staff')

    with manage_user(user):
        content_type = ContentType.objects.get_for_model(User)
        user.user_permissions.add(Permission.objects.get(
            codename='change_user',
            content_type=content_type,
        ))
        user.user_permissions.add(Permission.objects.get(
            codename='add_user',
            content_type=content_type,
        ))
        user.save()
        client.login(username='staff', password='staff')
        yield user


@fixture
def demo_users():
    user_0 = User(username='user_0')
    user_0.set_password('pw0')
    with manage_user(user_0):
        with manage_user(User(username='user_1')) as user_1:
            yield user_0, user_1


def get_reset_url(user, client):
    res = client.get(reverse('admin:password_reset_url',
                             kwargs={'id': user.pk}))
    assert res.status_code == 200
    body = res.content.decode('utf-8')
    assert 'password_reset_confirm' in body
    pattern = r'>(?P<url>http.*/password_reset_confirm/.*/.*/)</a>'

    assert search(pattern, body)
    return search(pattern, body).group('url')


def get_csrf_token(client, url):
    response = client.get(url)
    if response.status_code == 302:
        response = client.get(response.url)
    assert response.status_code == 200
    body = response.content.decode('utf-8')
    token_pattern = r'csrfmiddlewaretoken.*(?P<token>)'
    assert search(token_pattern, body)
    return search(token_pattern, body).group('token')


def assert_invalid_url(client, url, token, uids):
    res = client.get(url)
    assert res.status_code == 200
    body = res.content.decode('utf-8')
    assert 'Password reset unsuccessful' in body

    res = client.post(url, data={'csrfmiddlewaretoken': token,
                                 'new_password1': 'newpw',
                                 'new_password2': 'newpw'})
    assert res.status_code == 200
    body = res.content.decode('utf-8')
    assert 'Password reset unsuccessful' in body

    for uid in uids:
        user = User.objects.get(pk=uid)
        assert not user.check_password('newpw')


def test_without_users(admin_user, client):
    client.login(username='admin', password='password')
    res = client.get(reverse('admin:password_reset_url', kwargs={'id': 0}))
    assert res.status_code == 404


@mark.parametrize('user_idx', [0, 1])
@mark.parametrize('logout', [True, False])
def test_password_reset_process(user_idx, logout, demo_users,
                                staff_with_perm, client):
    user = demo_users[user_idx]
    url = get_reset_url(user, client)

    if logout:
        client.logout()

    token = get_csrf_token(client, url)

    user = User.objects.get(pk=user.pk)
    assert not user.check_password('newpw')

    res = client.get(url)
    assert res.status_code == 302
    assert 'set-password' in res.url
    url = res.url
    res = client.post(url, data={'csrfmiddlewaretoken': token,
                                 'new_password1': 'newpw',
                                 'new_password2': 'newpw'})
    assert res.status_code == 302
    assert 'password_reset_complete' in res.url

    user = User.objects.get(pk=user.pk)
    assert user.check_password('newpw')

    res = client.get(res.url)
    assert res.status_code == 200
    assert reverse('admin:login') in res.content.decode('utf-8')


@mark.parametrize('user_idx', [0, 1])
@mark.parametrize('logout', [True, False])
def test_other_user(user_idx, logout, demo_users,
                    staff_with_perm, client):
    change_user = demo_users[user_idx]
    token_user = demo_users[1-user_idx]
    change_user_url = get_reset_url(change_user, client)
    token_user_url = get_reset_url(token_user, client)

    if logout:
        client.logout()

    uidb64_pattern = r'password_reset_confirm/(?P<uidb64>[^/]+)/'
    change_uidb64 = search(uidb64_pattern, change_user_url).group('uidb64')

    forged_url = sub(uidb64_pattern,
                     'password_reset_confirm/%s/' % change_uidb64,
                     token_user_url)

    token = get_csrf_token(client, token_user_url)
    assert_invalid_url(client, forged_url, token,
                       [change_user.pk, token_user.pk])


@mark.parametrize('user_idx', [0, 1])
@mark.parametrize('logout', [True, False])
@mark.parametrize('replace', [
    lambda m: '/%s-%s/' % (force_str(b2a_hex(urandom(2))),
                           force_str(b2a_hex(urandom(5)))),
    lambda m: '/%s-%s/' % (m.group('ts'), m.group('hash')[1:]),
    lambda m: '/%s-%s/' % (m.group('ts'), m.group('hash')[:-1]),
    lambda m: '/%s-%s/' % (m.group('ts'), '0' + m.group('hash')),
    lambda m: '/%s-%s/' % (m.group('ts'), m.group('hash') + '0'),
    lambda m: '/%s-%s/' % (m.group('ts'), (
            '1' if m.group('hash')[0] == '0' else '0') + m.group('hash')[1:]),
    lambda m: '/%s-%s/' % (m.group('ts'), m.group('hash')[:-1] + (
            '1' if m.group('hash')[-1] == '0' else '0')),
    lambda m: '/%s-%s/' % (m.group('ts'), m.group('hash') + '0')])
def test_invalid_token(user_idx, logout, replace,
                       demo_users, staff_with_perm, client):
    user = demo_users[user_idx]
    url = get_reset_url(user, client)

    if logout:
        client.logout()

    token = get_csrf_token(client, url)
    invalid_url = sub(r'/(?P<ts>[^/-]+)-(?P<hash>[^/-]+)/$', replace, url)
    assert invalid_url != url

    assert_invalid_url(client, invalid_url, token, [user.pk])


@mark.parametrize('logout', [True, False])
def test_invalid_uidb64(logout, demo_users, staff_with_perm, client):
    invalid_uid = max([u.pk for u in User.objects.all()] + [-1]) + 1
    user = demo_users[0]
    url = get_reset_url(user, client)

    if logout:
        client.logout()

    token = get_csrf_token(client, url)
    invalid_uidb64 = force_str(
        urlsafe_base64_encode(force_bytes(invalid_uid)))
    invalid_url = sub(r'/[^/]+(/[^/]+/)$', r'/%s\1' % invalid_uidb64, url)
    assert invalid_url != url

    assert_invalid_url(client, invalid_url, token, [user.pk])


@mark.parametrize('user_idx', [0, 1])
@mark.parametrize('logout', [True, False])
def test_expired_token(user_idx, logout,
                       demo_users, staff_with_perm, client):
    user = demo_users[user_idx]
    url = get_reset_url(user, client)

    if logout:
        client.logout()

    token = get_csrf_token(client, url)

    if django.VERSION < (3, 1):
        future_date = date.today() + timedelta(
            days=_get_password_reset_token_expiry() + 1)
        with patch('django.contrib.auth.tokens.PasswordResetTokenGenerator.'
                   '_today', return_value=future_date):
            assert_invalid_url(client, url, token, [user.pk])
    else:
        future_date = datetime.now() + timedelta(
            days=_get_password_reset_token_expiry() + 1)
        with patch('django.contrib.auth.tokens.PasswordResetTokenGenerator.'
                   '_now', return_value=future_date):
            assert_invalid_url(client, url, token, [user.pk])


@mark.parametrize('user_idx', [0, 1])
def test_without_login(user_idx, demo_users, client):
    user = demo_users[user_idx]
    res = client.get(reverse('admin:password_reset_url',
                             kwargs={'id': user.pk}))
    assert res.status_code == 302
    assert 'login' in res.url


@mark.parametrize('user_idx', [0, 1])
def test_without_permissions(user_idx, demo_users, staff_without_perm,
                             client):
    user = demo_users[user_idx]
    client.login(username='staff', password='staff')
    res = client.get(reverse('admin:password_reset_url',
                             kwargs={'id': user.pk}))
    assert res.status_code == 403


def test_admin_ui_add_user(staff_with_perm, client):
    res = client.get(reverse('admin:auth_user_add'))
    assert res.status_code == 200

    token = get_csrf_token(client, reverse('admin:auth_user_add'))
    res = client.post(reverse('admin:auth_user_add'),
                      data={'csrfmiddlewaretoken': token,
                            'username': 'new_user'})
    assert res.status_code == 302
    new_user = User.objects.filter(username='new_user').first()
    assert new_user
    assert not new_user.has_usable_password()
    new_user.delete()


@mark.parametrize('user_idx', [0, 1])
def test_admin_ui_change_user(user_idx, demo_users, staff_with_perm, client):
    user = demo_users[user_idx]
    res = client.get(reverse('admin:auth_user_change',
                             args=[user.pk]))
    assert res.status_code == 200
    body = res.content.decode('utf-8')
    assert '/password/' not in body
    assert 'you can reset the password using the link on top of this form' \
        in body
