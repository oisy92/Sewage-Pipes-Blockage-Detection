import datetime

def secs_to_HMS(secs):
    if secs < 3600:
        return (datetime.timedelta(seconds = secs))