# -*- coding: utf-8 -*-
import re
from datetime import timedelta, datetime
import calendar

# Variations of dates that the parser can capture
year_variations = ['year', 'years', 'yrs','ปี']
day_variations = ['days', 'day','วัน']
minute_variations = ['minute', 'minutes', 'mins','นาที']
hour_variations = ['hrs', 'hours', 'hour','ชั่วโมง','ชม.']
week_variations = ['weeks', 'week', 'wks','สัปดาห์']
month_variations = ['month', 'months','เดือน']

# Variables used for RegEx Matching
day_names = 'monday|tuesday|wednesday|thursday|friday|saturday|sunday'
month_names_long = (
    'january|february|march|april|may|june|july|august|september|october|november|december'
)
month_names = month_names_long + '|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec'
day_nearest_names = 'today|yesterday|tomorrow|tonight|tonite'
numbers = (
    '(^a(?=\s)|one|two|three|four|five|six|seven|eight|nine|ten|'
    'eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|'
    'eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|'
    'eighty|ninety|hundred|thousand)'
)
re_dmy = '(' + '|'.join(day_variations + minute_variations + year_variations + week_variations + month_variations) + ')'
re_duration = '(before|after|earlier|later|ago|from\snow)'
re_year = '(19|20)\d{2}|^(19|20)\d{2}'
re_timeframe = 'this|coming|next|following|previous|last|end\sof\sthe'
re_ordinal = 'st|nd|rd|th|first|second|third|fourth|fourth|' + re_timeframe
re_time = r'(?P<hour>\d{1,2})(\:(?P<minute>\d{1,2})|(?P<convention>am|pm))'
re_separator = 'of|at|on'

# A list tuple of regular expressions / parser fn to match
# Start with the widest match and narrow it down because the order of the match in this list matters
regex = [
    (
        re.compile(
            r'''
            (
                ((?P<dow>%s)[,\s]\s*)? #Matches Monday, 12 Jan 2012, 12 Jan 2012 etc
                (?P<day>\d{1,2}) # Matches a digit
                (%s)?
                [-\s] # One or more space
                (?P<month>%s) # Matches any month name
                [-\s] # Space
                (?P<year>%s) # Year
                ((\s|,\s|\s(%s))?\s*(%s))?
            )
            ''' % (day_names, re_ordinal, month_names, re_year, re_separator, re_time),
            (re.VERBOSE | re.IGNORECASE)
        ),
        lambda m, base_date: datetime(
            int(m.group('year') if m.group('year') else base_date.year),
            HASHMONTHS[m.group('month').strip().lower()],
            int(m.group('day') if m.group('day') else 1),
        ) + timedelta(**convert_time_to_hour_minute(
            m.group('hour'),
            m.group('minute'),
            m.group('convention')
        ))
    ),
    (
        re.compile(
            r'''
            (
                ((?P<dow>%s)[,\s][-\s]*)? #Matches Monday, Jan 12 2012, Jan 12 2012 etc
                (?P<month>%s) # Matches any month name
                [-\s] # Space
                ((?P<day>\d{1,2})) # Matches a digit
                (%s)?
                ([-\s](?P<year>%s))? # Year
                ((\s|,\s|\s(%s))?\s*(%s))?
            )
            ''' % (day_names, month_names, re_ordinal, re_year, re_separator, re_time),
            (re.VERBOSE | re.IGNORECASE)
        ),
        lambda m, base_date: datetime(
            int(m.group('year') if m.group('year') else base_date.year),
            HASHMONTHS[m.group('month').strip().lower()],
            int(m.group('day') if m.group('day') else 1)
        ) + timedelta(**convert_time_to_hour_minute(
            m.group('hour'),
            m.group('minute'),
            m.group('convention')
        ))
    ),
    (
        re.compile(
            r'''
            (
                (?P<month>%s) # Matches any month name
                [-\s] # One or more space
                (?P<day>\d{1,2}) # Matches a digit
                (%s)?
                [-\s]\s*?
                (?P<year>%s) # Year
                ((\s|,\s|\s(%s))?\s*(%s))?
            )
            ''' % (month_names, re_ordinal, re_year, re_separator, re_time),
            (re.VERBOSE | re.IGNORECASE)
        ),
        lambda m, base_date: datetime(
            int(m.group('year') if m.group('year') else base_date.year),
            HASHMONTHS[m.group('month').strip().lower()],
            int(m.group('day') if m.group('day') else 1),
        ) + timedelta(**convert_time_to_hour_minute(
            m.group('hour'),
            m.group('minute'),
            m.group('convention')
        ))
    ),
    (
        re.compile(
            r'''
            (
                ((?P<number>\d+|(%s[-\s]?)+)\s)? # Matches any number or string 25 or twenty five
                (?P<unit>%s)s?\s # Matches days, months, years, weeks, minutes
                (?P<duration>%s) # before, after, earlier, later, ago, from now
                (\s*(?P<base_time>(%s)))?
                ((\s|,\s|\s(%s))?\s*(%s))?
            )
            ''' % (numbers, re_dmy, re_duration, day_nearest_names, re_separator, re_time),
            (re.VERBOSE | re.IGNORECASE)
        ),
        lambda m, base_date: date_from_duration(
            base_date,
            m.group('number'),
            m.group('unit').lower(),
            m.group('duration').lower(),
            m.group('base_time')
        ) + timedelta(**convert_time_to_hour_minute(
            m.group('hour'),
            m.group('minute'),
            m.group('convention')
        ))
    ),
    (
        re.compile(
            r'''
            (
                (?P<ordinal>%s) # First quarter of 2014
                \s+
                quarter\sof
                \s+
                (?P<year>%s)
            )
            ''' % (re_ordinal, re_year),
            (re.VERBOSE | re.IGNORECASE)
        ),
        lambda m, base_date: date_from_quarter(
            base_date,
            HASHORDINALS[m.group('ordinal').lower()],
            int(m.group('year') if m.group('year') else base_date.year)
        )
    ),
    (
        re.compile(
            r'''
            (
                (?P<ordinal_value>\d+)
                (?P<ordinal>%s) # 1st January 2012
                ((\s|,\s|\s(%s))?\s*)?
                (?P<month>%s)
                ([,\s]\s*(?P<year>%s))?
            )
            ''' % (re_ordinal, re_separator, month_names, re_year),
            (re.VERBOSE | re.IGNORECASE)
        ),
        lambda m, base_date: datetime(
            int(m.group('year') if m.group('year') else base_date.year),
            int(HASHMONTHS[m.group('month').lower()] if m.group('month') else 1),
            int(m.group('ordinal_value') if m.group('ordinal_value') else 1),
        )
    ),
    (
        re.compile(
            r'''
            (
                (?P<month>%s)
                \s+
                (?P<ordinal_value>\d+)
                (?P<ordinal>%s) # January 1st 2012
                ([,\s]\s*(?P<year>%s))?
            )
            ''' % (month_names, re_ordinal, re_year),
            (re.VERBOSE | re.IGNORECASE)
        ),
        lambda m, base_date: datetime(
            int(m.group('year') if m.group('year') else base_date.year),
            int(HASHMONTHS[m.group('month').lower()] if m.group('month') else 1),
            int(m.group('ordinal_value') if m.group('ordinal_value') else 1),
        )
    ),
    (
        re.compile(
            r'''
            (?P<time>%s) # this, next, following, previous, last
            \s+
            ((?P<number>\d+|(%s[-\s]?)+)\s)?
            (?P<dmy>%s) # year, day, week, month, night, minute, min
            ((\s|,\s|\s(%s))?\s*(%s))?
            ''' % (re_timeframe, numbers, re_dmy, re_separator, re_time),
            (re.VERBOSE | re.IGNORECASE),
        ),
        lambda m, base_date: date_from_relative_week_year(
            base_date,
            m.group('time'),
            m.group('dmy'),
            m.group('number')
        ) + timedelta(**convert_time_to_hour_minute(
            m.group('hour'),
            m.group('minute'),
            m.group('convention')
        ))
    ),
    (
        re.compile(
            r'''
            (?P<time>%s) # this, next, following, previous, last
            \s+
            (?P<dow>%s) # mon - fri
            ((\s|,\s|\s(%s))?\s*(%s))?
            ''' % (re_timeframe, day_names, re_separator, re_time),
            (re.VERBOSE | re.IGNORECASE),
        ),
        lambda m, base_date: date_from_relative_day(
            base_date,
            m.group('time'),
            m.group('dow')
        ) + timedelta(**convert_time_to_hour_minute(
            m.group('hour'),
            m.group('minute'),
            m.group('convention')
        ))
    ),
    (
        re.compile(
            r'''
            (
                (?P<day>\d{1,2}) # Day, Month
                (%s)
                [-\s] # One or more space
                (?P<month>%s)
            )
            ''' % (re_ordinal, month_names),
            (re.VERBOSE | re.IGNORECASE)
        ),
        lambda m, base_date: datetime(
            base_date.year,
            HASHMONTHS[m.group('month').strip().lower()],
            int(m.group('day') if m.group('day') else 1)
        )
    ),
    (
        re.compile(
            r'''
            (
                (?P<month>%s) # Month, day
                [-\s] # One or more space
                ((?P<day>\d{1,2})\b) # Matches a digit January 12
                (%s)?
            )
            ''' % (month_names, re_ordinal),
            (re.VERBOSE | re.IGNORECASE)
        ),
        lambda m, base_date: datetime(
            base_date.year,
            HASHMONTHS[m.group('month').strip().lower()],
            int(m.group('day') if m.group('day') else 1)
        )
    ),
    (
        re.compile(
            r'''
            (
                (?P<month>%s) # Month, year
                [-\s] # One or more space
                ((?P<year>\d{1,4})\b) # Matches a digit January 12
            )
            ''' % (month_names),
            (re.VERBOSE | re.IGNORECASE)
        ),
        lambda m, base_date: datetime(
            int(m.group('year')),
            HASHMONTHS[m.group('month').strip().lower()],
            1
        )
    ),
    (
        re.compile(
            r'''
            (
                (?P<month>\d{1,2}) # MM/DD or MM/DD/YYYY
                /
                ((?P<day>\d{1,2}))
                (/(?P<year>%s))?
            )
            ''' % (re_year),
            (re.VERBOSE | re.IGNORECASE)
        ),
        lambda m, base_date: datetime(
            int(m.group('year') if m.group('year') else base_date.year),
            int(m.group('month').strip()),
            int(m.group('day'))
        )
    ),
    (
        re.compile(
            r'''
            (?P<adverb>%s) # today, yesterday, tomorrow, tonight
            ((\s|,\s|\s(%s))?\s*(%s))?
            ''' % (day_nearest_names, re_separator, re_time),
            (re.VERBOSE | re.IGNORECASE)
        ),
        lambda m, base_date: date_from_adverb(
            base_date,
            m.group('adverb')
        ) + timedelta(**convert_time_to_hour_minute(
            m.group('hour'),
            m.group('minute'),
            m.group('convention')
        ))
    ),
    (
        re.compile(
            r'''
            (?P<named_day>%s) # Mon - Sun
            ''' % (day_names),
            (re.VERBOSE | re.IGNORECASE)
        ),
        lambda m, base_date: this_week_day(
            base_date,
            HASHWEEKDAYS[m.group('named_day').lower()]
        )
    ),
    (
        re.compile(
            r'''
            (?P<year>%s) # Year
            ''' % (re_year),
            (re.VERBOSE | re.IGNORECASE)
        ),
        lambda m, base_date: datetime(int(m.group('year')), 1, 1)
    ),
    (
        re.compile(
            r'''
            (?P<month>%s) # Month
            ''' % (month_names_long),
            (re.VERBOSE | re.IGNORECASE)
        ),
        lambda m, base_date: datetime(
            base_date.year,
            HASHMONTHS[m.group('month').lower()],
            1
        )
    ),
    (
        re.compile(
            r'''
            (%s) # Matches time 12:00
            ''' % (re_time),
            (re.VERBOSE | re.IGNORECASE),
        ),
        lambda m, base_date: datetime(
            base_date.year,
            base_date.month,
            base_date.day
        ) + timedelta(**convert_time_to_hour_minute(
            m.group('hour'),
            m.group('minute'),
            m.group('convention')
        ))
    ),
    (
        re.compile(
            r'''
            (
                (?P<hour>\d+) # Matches 12 hours, 2 hrs
                \s+
                (%s)
            )
            ''' % ('|'.join(hour_variations)),
            (re.VERBOSE | re.IGNORECASE),
        ),
        lambda m, base_date: datetime(
            base_date.year,
            base_date.month,
            base_date.day,
            int(m.group('hour'))
        )
    )
]


def hashnum(number):
    """
    Hash of numbers
    Append more number to modify your match
    """
    if re.match(r'one|^a\b', number, re.IGNORECASE):
        return 1
    if re.match(r'two', number, re.IGNORECASE):
        return 2
    if re.match(r'three', number, re.IGNORECASE):
        return 3
    if re.match(r'four', number, re.IGNORECASE):
        return 4
    if re.match(r'five', number, re.IGNORECASE):
        return 5
    if re.match(r'six', number, re.IGNORECASE):
        return 6
    if re.match(r'seven', number, re.IGNORECASE):
        return 7
    if re.match(r'eight', number, re.IGNORECASE):
        return 8
    if re.match(r'nine', number, re.IGNORECASE):
        return 9
    if re.match(r'ten', number, re.IGNORECASE):
        return 10
    if re.match(r'eleven', number, re.IGNORECASE):
        return 11
    if re.match(r'twelve', number, re.IGNORECASE):
        return 12
    if re.match(r'thirteen', number, re.IGNORECASE):
        return 13
    if re.match(r'fourteen', number, re.IGNORECASE):
        return 14
    if re.match(r'fifteen', number, re.IGNORECASE):
        return 15
    if re.match(r'sixteen', number, re.IGNORECASE):
        return 16
    if re.match(r'seventeen', number, re.IGNORECASE):
        return 17
    if re.match(r'eighteen', number, re.IGNORECASE):
        return 18
    if re.match(r'nineteen', number, re.IGNORECASE):
        return 19
    if re.match(r'twenty', number, re.IGNORECASE):
        return 20
    if re.match(r'thirty', number, re.IGNORECASE):
        return 30
    if re.match(r'forty', number, re.IGNORECASE):
        return 40
    if re.match(r'fifty', number, re.IGNORECASE):
        return 50
    if re.match(r'sixty', number, re.IGNORECASE):
        return 60
    if re.match(r'seventy', number, re.IGNORECASE):
        return 70
    if re.match(r'eighty', number, re.IGNORECASE):
        return 80
    if re.match(r'ninety', number, re.IGNORECASE):
        return 90
    if re.match(r'hundred', number, re.IGNORECASE):
        return 100
    if re.match(r'thousand', number, re.IGNORECASE):
        return 1000


def convert_string_to_number(value):
    """
    Convert strings to numbers
    """
    if value is None:
        return 1
    if isinstance(value, int):
        return value
    if value.isdigit():
        return int(value)
    num_list = map(lambda s: hashnum(s), re.findall(numbers + '+', value, re.IGNORECASE))
    return sum(num_list)


def convert_time_to_hour_minute(hour, minute, convention):
    """
    Convert time to hour, minute
    """
    if hour is None:
        hour = 0
    if minute is None:
        minute = 0
    if convention is None:
        convention = 'am'

    hour = int(hour)
    minute = int(minute)

    if convention == 'pm':
        hour += 12

    return {'hours': hour, 'minutes': minute}


def date_from_quarter(base_date, ordinal, year):
    """
    Extract date from quarter of a year
    """
    interval = 3
    month_start = interval * (ordinal - 1)
    if month_start < 0:
        month_start = 9
    month_end = month_start + interval
    if month_start == 0:
        month_start = 1
    return [
        datetime(year, month_start, 1),
        datetime(year, month_end, calendar.monthrange(year, month_end)[1])
    ]


def date_from_relative_day(base_date, time, dow):
    """
    Converts relative day to time
    Ex: this tuesday, last tuesday
    """
    # Reset date to start of the day
    base_date = datetime(base_date.year, base_date.month, base_date.day)
    time = time.lower()
    dow = dow.lower()
    if time == 'this' or time == 'coming':
        # Else day of week
        num = HASHWEEKDAYS[dow]
        return this_week_day(base_date, num)
    elif time == 'last' or time == 'previous':
        # Else day of week
        num = HASHWEEKDAYS[dow]
        return previous_week_day(base_date, num)
    elif time == 'next' or time == 'following':
        # Else day of week
        num = HASHWEEKDAYS[dow]
        return next_week_day(base_date, num)


def date_from_relative_week_year(base_date, time, dow, ordinal=1):
    """
    Converts relative day to time
    Eg. this tuesday, last tuesday
    """
    # If there is an ordinal (next 3 weeks) => return a start and end range
    # Reset date to start of the day
    relative_date = datetime(base_date.year, base_date.month, base_date.day)
    if dow in year_variations:
        if time == 'this' or time == 'coming':
            return datetime(relative_date.year, 1, 1)
        elif time == 'last' or time == 'previous':
            return datetime(relative_date.year - 1, relative_date.month, 1)
        elif time == 'next' or time == 'following':
            return relative_date + timedelta(relative_date.year + 1)
        elif time == 'end of the':
            return datetime(relative_date.year, 12, 31)
    elif dow in month_variations:
        if time == 'this':
            return datetime(relative_date.year, relative_date.month, relative_date.day)
        elif time == 'last' or time == 'previous':
            return datetime(relative_date.year, relative_date.month - 1, relative_date.day)
        elif time == 'next' or time == 'following':
            return datetime(relative_date.year, relative_date.month + 1, relative_date.day)
        elif time == 'end of the':
            return datetime(
                relative_date.year,
                relative_date.month,
                calendar.monthrange(relative_date.year, relative_date.month)[1]
            )
    elif dow in week_variations:
        if time == 'this':
            return relative_date - timedelta(days=relative_date.weekday())
        elif time == 'last' or time == 'previous':
            return relative_date - timedelta(weeks=1)
        elif time == 'next' or time == 'following':
            return relative_date + timedelta(weeks=1)
        elif time == 'end of the':
            day_of_week = base_date.weekday()
            return day_of_week + timedelta(days=6 - relative_date.weekday())
    elif dow in day_variations:
        if time == 'this':
            return relative_date
        elif time == 'last' or time == 'previous':
            return relative_date - timedelta(days=1)
        elif time == 'next' or time == 'following':
            return relative_date + timedelta(days=1)
        elif time == 'end of the':
            return datetime(relative_date.year, relative_date.month, relative_date.day, 23, 59, 59)


def date_from_adverb(base_date, name):
    """
    Convert Day adverbs to dates
    Tomorrow => Date
    Today => Date
    """
    # Reset date to start of the day
    adverb_date = datetime(base_date.year, base_date.month, base_date.day)
    if name == 'today' or name == 'tonite' or name == 'tonight':
        return adverb_date.today()
    elif name == 'yesterday':
        return adverb_date - timedelta(days=1)
    elif name == 'tomorrow' or name == 'tom':
        return adverb_date + timedelta(days=1)


def date_from_duration(base_date, number_as_string, unit, duration, base_time=None):
    """
    Find dates from duration
    Eg: 20 days from now
    Currently does not support strings like "20 days from last monday".
    """
    # Check if query is `2 days before yesterday` or `day before yesterday`
    if base_time is not None:
        base_date = date_from_adverb(base_date, base_time)
    num = convert_string_to_number(number_as_string)
    if unit in day_variations:
        args = {'days': num}
    elif unit in minute_variations:
        args = {'minutes': num}
    elif unit in week_variations:
        args = {'weeks': num}
    elif unit in month_variations:
        args = {'days': 365 * num / 12}
    elif unit in year_variations:
        args = {'years': num}
    if duration == 'ago' or duration == 'before' or duration == 'earlier':
        if 'years' in args:
            return datetime(base_date.year - args['years'], base_date.month, base_date.day)
        return base_date - timedelta(**args)
    elif duration == 'after' or duration == 'later' or duration == 'from now':
        if 'years' in args:
            return datetime(base_date.year + args['years'], base_date.month, base_date.day)
        return base_date + timedelta(**args)


def this_week_day(base_date, weekday):
    """
    Finds coming weekday
    """
    day_of_week = base_date.weekday()
    # If today is Tuesday and the query is `this monday`
    # We should output the next_week monday
    if day_of_week > weekday:
        return next_week_day(base_date, weekday)
    start_of_this_week = base_date - timedelta(days=day_of_week + 1)
    day = start_of_this_week + timedelta(days=1)
    while day.weekday() != weekday:
        day = day + timedelta(days=1)
    return day


def previous_week_day(base_date, weekday):
    """
    Finds previous weekday
    """
    day = base_date - timedelta(days=1)
    while day.weekday() != weekday:
        day = day - timedelta(days=1)
    return day


def next_week_day(base_date, weekday):
    """
    Finds next weekday
    """
    day_of_week = base_date.weekday()
    end_of_this_week = base_date + timedelta(days=6 - day_of_week)
    day = end_of_this_week + timedelta(days=1)
    while day.weekday() != weekday:
        day = day + timedelta(days=1)
    return day


# Mapping of Month name and Value
HASHMONTHS = {
    'january': 1,
    'jan': 1,
    'february': 2,
    'feb': 2,
    'march': 3,
    'mar': 3,
    'april': 4,
    'apr': 4,
    'may': 5,
    'june': 6,
    'jun': 6,
    'july': 7,
    'jul': 7,
    'august': 8,
    'aug': 8,
    'september': 9,
    'sep': 9,
    'october': 10,
    'oct': 10,
    'november': 11,
    'nov': 11,
    'december': 12,
    'dec': 12
}

# Days to number mapping
HASHWEEKDAYS = {
    'monday': 0,
    'mon': 0,
    'tuesday': 1,
    'tue': 1,
    'wednesday': 2,
    'wed': 2,
    'thursday': 3,
    'thu': 3,
    'friday': 4,
    'fri': 4,
    'saturday': 5,
    'sat': 5,
    'sunday': 6,
    'sun': 6
}

# Ordinal to number
HASHORDINALS = {
    'first': 1,
    'second': 2,
    'third': 3,
    'fourth': 4,
    'forth': 4,
    'last': -1
}


def datetime_parsing(text, base_date=datetime.now()):
    """
    Extract datetime objects from a string of text.
    """
    matches = []
    found_array = []

    # Find the position in the string
    for expression, function in regex:
        for match in expression.finditer(text):
            matches.append((match.group(), function(match, base_date), match.span()))

    # Wrap the matched text with TAG element to prevent nested selections
    for match, value, spans in matches:
        subn = re.subn(
            '(?!<TAG[^>]*?>)' + match + '(?![^<]*?</TAG>)', '<TAG>' + match + '</TAG>', text
        )
        text = subn[0]
        is_substituted = subn[1]
        if is_substituted != 0:
            found_array.append((match, value, spans))

    # To preserve order of the match, sort based on the start position
    return sorted(found_array, key=lambda match: match and match[2][0])
