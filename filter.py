import os
import pickle
from email import message_from_string
from getpass import getpass, getuser
from imaplib import IMAP4_SSL
import json

from classifier import Classifier
from settings import BASEDIR


class Filter:
    processed_mail_file = BASEDIR + '/processed_mail.json'

    def __init__(self, username, password):
        self.username = username
        self.classifier = Classifier.get_trained_classifier()
        try:
            self.mail = IMAP4_SSL(self._get_host(self.username))
            self.mail.login(self.username, password)
        except:
            print('An error occured while signing in.')
            exit(1)

    @staticmethod
    def _get_host(username):
        try:
            domain = username.split('@')[1]
        except IndexError:
            print('Invalid username')
            exit(1)
        else:
            return 'imap.{}'.format(domain)

    def filter_all(self):
        processed_mail = []
        for uid in self._get_messages_uids():
            self._handle_message(uid, processed_mail)
        self._update_processed_mail(self.username, processed_mail)

    def filter_new(self):
        processed_mail = self._get_users_processed_mail(self.username)
        uids = set(self._get_messages_uids()) - set(processed_mail)
        for uid in uids:
            self._handle_message(uid, processed_mail)
        self._update_processed_mail(self.username, processed_mail)

    def _handle_message(self, uid, processed_mail):
        processed_mail.append(uid)
        result, data = self.mail.uid('fetch', uid, '(RFC822)')
        if result == 'OK':
            message = message_from_string(data[0][1])
            if self.classifier.classify(self._get_message_text(message)) == 'spam':
                self._is_spam_folder()
                self.mail.uid('copy', uid, 'SPAM')
                self.mail.uid('store', uid, '+FLAGS', '\\Deleted')
                self.mail.expunge()

    def _is_spam_folder(self):
        result, data = self.mail.select('SPAM')
        if result == 'NO':
            self.mail.create('SPAM')
        self.mail.select('INBOX')

    @staticmethod
    def _get_message_text(message):
        maintype = message.get_content_maintype()
        if maintype == 'multipart':
            for part in message.get_payload():
                if part.get_content_maintype() == 'text':
                    return part.get_payload()
        if maintype == 'text':
            return message.get_payload()
        return ''

    def _get_messages_uids(self):
        self.mail.select("INBOX")
        result, data = self.mail.uid('search', None, "ALL")
        if result == 'OK':
            return data[0].split()
        return None

    def _get_processed_mail(self):
        all_processed_mail = {}
        if os.path.isfile(self.processed_mail_file):
            with open(self.processed_mail_file, 'r') as f:
                content = f.read()
                if content:
                    all_processed_mail = json.loads(content)
        return all_processed_mail

    def _get_users_processed_mail(self, username):
        """
        json schema:
        { username : [uids of processed emails] }
        :return: list of processed uids of the current user
        """
        users_processed_mail = self._get_processed_mail().get(username, [])
        return users_processed_mail

    def _update_processed_mail(self, username, processed_mail):
        all_processed_mail = self._get_processed_mail()
        all_processed_mail[self.username] = processed_mail
        with open(self.processed_mail_file, 'w') as f:
            json.dump(all_processed_mail, f)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.mail.close()
        self.mail.logout()

if __name__ == '__main__':
    username = raw_input('Email: ')
    password = getpass()
    only_new = raw_input('Do you want to filter only new mail? y/n ')
    with Filter(username, password) as filter:
        if only_new == 'y':
            filter.filter_new()
        else:
            filter.filter_all()