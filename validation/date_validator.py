from datetime import datetime

def ask_date(message):
    valid = False                      # we start without a valid date
    while valid == False:              # repeat until the date is valid
        text = input(message)
        try:
            date_value = datetime.strptime(text, "%Y-%m-%d")
            valid = True               # the date worked, so we stop repeating
        except ValueError:
            print("Invalid date. Use the format YYYY-MM-DD")
    return date_value