def ask_amount(message):
    valid = False
    while valid == False:
        text = input(message)
        try:
            amount = float(text)
            valid = True
        except ValueError:
            print("The amount must be a number")
    return amount