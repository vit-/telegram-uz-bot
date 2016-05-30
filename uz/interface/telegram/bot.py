import aiotg


class UZTGBot(aiotg.Bot):

    _scanner = None

    @property
    def scanner(self):
        assert self._scanner, 'Scanner is not set'
        return self._scanner

    def set_scanner(self, scanner):
        self._scanner = scanner

    def ticket_booked_cb(self, orig_msg, session_id):
        chat = aiotg.Chat.from_message(self, orig_msg)
        msg = ('Ticket is booked! To proceed checkout use this session id '
               'in your browser: {}'.format(session_id))
        return chat.send_text(msg)
