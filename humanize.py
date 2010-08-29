from django.template import defaultfilters
from datetime import date, datetime
from google.appengine.ext import webapp
import re

register = webapp.template.create_template_register()

def ordinal(value):
    """
    Converts an integer to its ordinal as a string. 1 is '1st', 2 is '2nd',
    3 is '3rd', etc. Works for any integer.
    """
    try:
        value = int(value)
    except ValueError:
        return value
    t = ('th', 'st', 'nd', 'rd', 'th', 'th', 'th', 'th', 'th', 'th')
    if value % 100 in (11, 12, 13): # special case
        return u"%d%s" % (value, t[0])
    return u'%d%s' % (value, t[value % 10])
ordinal.is_safe = True
register.filter(ordinal)

def intcomma(value):
    """
    Converts an integer to a string containing commas every three digits.
    For example, 3000 becomes '3,000' and 45000 becomes '45,000'.
    """
    orig = str(value)
    new = re.sub("^(-?\d+)(\d{3})", '\g<1>,\g<2>', orig)
    if orig == new:
        return new
    else:
        return intcomma(new).encode('utf-8')
intcomma.is_safe = True
register.filter(intcomma)

def intword(value):
    """
    Converts a large integer to a friendly text representation. Works best for
    numbers over 1 million. For example, 1000000 becomes '1.0 million', 1200000
    becomes '1.2 million' and '1200000000' becomes '1.2 billion'.
    """
    value = int(value)
    if value < 1000000:
        return value
    if value < 1000000000:
        new_value = value / 1000000.0
        return '%(value).1f million' % {'value': new_value}
    if value < 1000000000000:
        new_value = value / 1000000000.0
        return '%(value).1f billion' % {'value': new_value}
    if value < 1000000000000000:
        new_value = value / 1000000000000.0
        return '%(value).1f trillion' % {'value': new_value}
    return value
intword.is_safe = False
register.filter(intword)

def apnumber(value):
    """
    For numbers 1-9, returns the number spelled out. Otherwise, returns the
    number. This follows Associated Press style.
    """
    try:
        value = int(value)
    except ValueError:
        return value
    if not 0 < value < 10:
        return value
    return ('one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine')[value-1]
apnumber.is_safe = True
register.filter(apnumber)

def naturalday(value, arg=None):
    """
    For date values that are tomorrow, today or yesterday compared to
    present day returns representing string. Otherwise, returns a string
    formatted according to settings.DATE_FORMAT.
    """
    try:
        value = date(value.year, value.month, value.day)
    except AttributeError:
        # Passed value wasn't a date object
        return value
    except ValueError:
        # Date arguments out of range
        return value
    delta = value - date.today()
    if delta.days == 0:
        return u'today'
    elif delta.days == 1:
        return u'tomorrow'
    elif delta.days == -1:
        return u'yesterday'
    return defaultfilters.date(value, arg)
register.filter(naturalday)

def naturaltime(value, arg="D d M Y"):
    """
    For time values that are tomorrow, today or yesterday compared to
    present day returns representing string. Otherwise, returns a string
    formatted according to settings.DATE_FORMAT.
    """

    try:
        value = datetime(value.year, value.month, value.day,
                         value.hour, value.minute, value.second)
    except AttributeError:
        # Passed value wasn't a datetime object
        return value
    except ValueError:
        # Date arguments out of range
        return value

    def plural(s,p,n):
        return (s if n == 0 else p)

    delta = datetime.now() - value
    if delta.days >= 30:
        return defaultfilters.date(value, arg)
    if delta.days >= 1:
        return (plural('%(days).i day ago', '%(days).i days ago',
                        delta.days) % {'days' : delta.days})
    if (delta.seconds / 3600.0) >= 1:
        return (plural('%(hours).i hour ago', '%(hours).i hours ago',
                        delta.seconds / 3600) %
                        {'hours' : delta.seconds / 3600.0})
    if (delta.seconds / 60.0) >= 1:
        return (plural('%(minutes).i minute ago', '%(minutes).i minutes ago',
                        delta.seconds / 60) %
                        {'minutes' : delta.seconds / 60.0})
    return _('just now')
register.filter(naturaltime)
