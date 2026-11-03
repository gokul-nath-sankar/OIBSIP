def get_positive_float(prompt):
    """Prompts the user until a valid positive number is entered."""
    while True:
        user_input = input(prompt).strip()
        try:
            value = float(user_input)
            if value <= 0:
                print("Error: Please enter a positive number greater than zero.")
                continue
            return value
        except ValueError:
            print("Error: Invalid input. Please enter a numeric value.")


def classify_bmi(bmi):
    if bmi < 18.5:
        return "Underweight"
    elif 18.5 <= bmi < 25.0:
        return "Normal"
    elif 25.0 <= bmi < 30.0:
        return "Overweight"
    else:
        return "Obese"


def main():
    print("=== Command-Line BMI Calculator ===")
    weight = get_positive_float("Enter your weight in kg (e.g., 70): ")
    height = get_positive_float("Enter your height in meters (e.g., 1.75): ")

    bmi = weight / (height ** 2)
    category = classify_bmi(bmi)

    print("\n--- Results ---")
    print(f"BMI Value : {bmi:.2f}")
    print(f"Category  : {category}")


if __name__ == "__main__":
    main()