def convert_secs(secs: int):
    seconds = secs % (24 * 3600)
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    print(hours)
    print(minutes)
    print(seconds)

    if minutes == 0:
        return f"{hours} hours"
    elif hours == 0:
        return f"{minutes} minutes"
    else:
        return f"{hours} hours {minutes} minutes"