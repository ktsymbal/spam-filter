from imaplib import IMAP4_SSL

from settings import HOSTS


class Filter:
    def __init__(self, username, password):
        if self._get_host(username) in HOSTS:
            self.mail = IMAP4_SSL('imap.gmail.com')
            try:
                self.mail.login(username, password)
            except:
                print('An error occured while signing in.')
                exit(1)

    def filter_all(self):
        pass

    @staticmethod
    def _get_host(username):
        try:
            domain = username.split('@')[1].split('.')[0]
        except IndexError:
            domain = ""
            print('Invalid username')
        finally:
            return domain
