def ask_movement_type(message):
    valid = False
    while valid == False:
        text = input(message)
        if text == "Ingreso" or text == "Retiro":
            movement_type = text
            valid = True
        else:
            print("The type must be Ingreso or Retiro")
    return movement_type