def celsius_to_fahrenheit():
    try:
        celsius = float(input("Enter temperature in Celsius: "))
        fahrenheit = (celsius * 9 / 5) + 32
        print(f"{celsius}°C is equal to {fahrenheit:.2f}°F")
    except ValueError:
        print("Please enter a valid number!")


celsius_to_fahrenheit()
