def ask_id(message):
    valid = False
    while valid == False:
        text = input(message)
        try:
            id_value = int(text)
            valid = True
        except ValueError:
            print("The ID must be an integer")
    return id_value