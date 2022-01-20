import ckan.lib.mailer as _mailer
from ckan.common import _
from ckan.common import config
import ckan.common
import ckan.lib.helpers as h


def send_invite(user):
    _mailer.create_reset_key(user)
    body = _mailer.get_invite_body(user)
    subject = _('Invite for {site_title}').format(site_title=config.get('site_title', ''))
    mail_user(user, subject, body)


def send_reset_link(user):
    _mailer.create_reset_key(user)
    body = get_reset_link_body(user)
    subject = _('Reset your password')
    mail_user(user, subject, body)


def mail_user(recipient, subject, body, headers={}):
    if (recipient.email is None) or not len(recipient.email):
        raise _mailer.MailerException(_("No recipient email address available!"))
    mail_recipient(recipient.display_name, recipient.email, subject,
                   body, headers=headers)


def get_reset_link_body(user):
    reset_link_message = _(
        "You have requested your password on {site_title} to be reset.\n"
        "\n"
        "Please click the following link to confirm this request:\n"
        "\n"
        "   {reset_link}\n"
    )

    d = {
        'reset_link': get_reset_link(user),
        'site_title': config.get('site_title', ''),
        'user_fullname': user.fullname
    }
    return reset_link_message.format(**d)


def get_reset_link(user):
    from urlparse import urljoin

    if "name" in _mailer.config.get("ckan.site_url"):
        site_url = g.site_url.replace("http://", "https://e.")
    else:
        site_url = g.site_url
    return urljoin(site_url,
                   h.url_for(controller='user',
                             action='perform_reset',
                             id=user.id,
                             key=user.reset_key))


def mail_recipient(recipient_name, recipient_email, subject, body, headers={}):
    site_title = _mailer.config.get('ckan.site_title')
    site_url = _mailer.config.get('ckan.site_url')
    return _mail_recipient(recipient_name, recipient_email,
                           site_title, site_url, subject, body, headers=headers)


def _mail_recipient(recipient_name, recipient_email,
                    sender_name, sender_url, subject,
                    body, headers={}):
    mail_from = _mailer.config.get('smtp.mail_from')
    # body = add_msg_niceties(recipient_name, body, sender_name, sender_url)
    msg = _mailer.MIMEText(body.encode('utf-8'), 'plain', 'utf-8')
    for k, v in headers.items(): msg[k] = v
    subject = _mailer.Header(subject.encode('utf-8'), 'utf-8')
    msg['Subject'] = subject
    msg['From'] = _("%s <%s>") % (sender_name, mail_from)
    msg['To'] = u"%s <%s>" % (recipient_name, recipient_email)
    msg['Date'] = _mailer.utils.formatdate(_mailer.time())
    msg['X-Mailer'] = "Version %s" % _mailer.ckan.__version__

    # Send the email using Python's smtplib.
    if 'smtp.test_server' in _mailer.config:
        # If 'smtp.test_server' is configured we assume we're running tests,
        # and don't use the smtp.server, starttls, user, password etc. options.
        smtp_server = _mailer.config['smtp.test_server']
        smtp_starttls = False
        smtp_user = None
        smtp_password = None
    else:
        smtp_server = _mailer.config.get('smtp.server', 'localhost')
        smtp_starttls = ckan.common.asbool(
            _mailer.config.get('smtp.starttls'))
        smtp_user = _mailer.config.get('smtp.user')
        smtp_password = _mailer.config.get('smtp.password')

    try:
        smtp_connection = _mailer.smtplib.SMTP(smtp_server)
        # smtp_connection.set_debuglevel(True)
    except (_mailer.socket.error, _mailer.smtplib.SMTPConnectError) as e:
        _mailer.log.exception(e)
        raise _mailer.MailerException('SMTP server could not be connected to: "%s" %s'
                                      % (smtp_server, e))

    try:
        # Identify ourselves and prompt the server for supported features.
        smtp_connection.ehlo()

        # If 'smtp.starttls' is on in CKAN config, try to put the SMTP
        # connection into TLS mode.
        if smtp_starttls:
            if smtp_connection.has_extn('STARTTLS'):
                smtp_connection.starttls()
                # Re-identify ourselves over TLS connection.
                smtp_connection.ehlo()
            else:
                raise _mailer.MailerException("SMTP server does not support STARTTLS")

        # If 'smtp.user' is in CKAN config, try to login to SMTP server.
        if smtp_user:
            assert smtp_password, ("If smtp.user is configured then "
                                   "smtp.password must be configured as well.")
            smtp_connection.login(smtp_user, smtp_password)

        smtp_connection.sendmail(mail_from, recipient_email.split(","), msg.as_string())
        _mailer.log.info("Sent email to {0}".format(recipient_email.split(",")))

    except _mailer.smtplib.SMTPException as e:
        msg = '%r' % e
        _mailer.log.exception(msg)
        raise _mailer.MailerException(msg)
    finally:
        smtp_connection.quit()
