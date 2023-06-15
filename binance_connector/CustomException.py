class CustomException(Exception):
    SEND_ALERT = True
    NOT_SEND_ALERT = False

    def __init__(self, send_alert, message):
        self.send_alert = send_alert
        self.message = message
