import ckanext.gov_theme.mailer as custom_mailer
import ckan.lib.email_notifications as email_notifications

def get_and_send_notifications_for_all_users():
    context = {'model': email_notifications.model, 'session': email_notifications.model.Session, 'ignore_auth': True,
            'keep_email': True}
    users = email_notifications.logic.get_action('user_list')(context, {})
    for user in users:
        get_and_send_notifications_for_user(user)

def send_notification(user, email_dict):
    '''Email `email_dict` to `user`.'''
    import ckan.lib.mailer

    if not user.get('email'):
        # FIXME: Raise an exception.
        return

    try:
        custom_mailer.mail_recipient(user['display_name'], user['email'],
                email_dict['subject'], email_dict['body'])
    except ckan.lib.mailer.MailerException:
        raise


def get_and_send_notifications_for_user(user):

    # Parse the email_notifications_since config setting, email notifications
    # from longer ago than this time will not be sent.
    email_notifications_since = email_notifications.pylons.config.get(
            'ckan.email_notifications_since', '2 days')
    email_notifications_since = email_notifications.string_to_timedelta(
            email_notifications_since)
    email_notifications_since = (email_notifications.datetime.datetime.now()
            - email_notifications_since)

    # FIXME: We are accessing model from lib here but I'm not sure what
    # else to do unless we add a get_email_last_sent() logic function which
    # would only be needed by this lib.
    email_last_sent = email_notifications.model.Dashboard.get(user['id']).email_last_sent
    activity_stream_last_viewed = (
        email_notifications.model.Dashboard.get(user['id']).activity_stream_last_viewed)

    since = max(email_notifications_since, email_last_sent,
            activity_stream_last_viewed)

    notifications = email_notifications.get_notifications(user, since)

    # TODO: Handle failures from send_email_notification.
    for notification in notifications:
        send_notification(user, notification)

    # FIXME: We are accessing model from lib here but I'm not sure what
    # else to do unless we add a update_email_last_sent()
    # logic function which would only be needed by this lib.
    dash = email_notifications.model.Dashboard.get(user['id'])
    dash.email_last_sent = email_notifications.datetime.datetime.now()
    email_notifications.model.repo.commit()