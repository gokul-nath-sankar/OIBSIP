import random
import string


def get_password_length():
    while True:
        user_input = input("Enter desired password length (minimum 8): ").strip()
        try:
            length = int(user_input)
            if length < 8:
                print("Error: Password length must be at least 8 characters.")
                continue
            return length
        except ValueError:
            print("Error: Please enter a valid integer.")


def get_character_pools():
    while True:
        print("\nSelect character types to include (at least 2 required):")
        inc_upper = input("Include Uppercase letters (A-Z)? (y/n): ").strip().lower() == 'y'
        inc_lower = input("Include Lowercase letters (a-z)? (y/n): ").strip().lower() == 'y'
        inc_digits = input("Include Numbers (0-9)? (y/n): ").strip().lower() == 'y'
        inc_symbols = input("Include Symbols (!@#$...)? (y/n): ").strip().lower() == 'y'

        pools = []
        if inc_upper:
            pools.append(string.ascii_uppercase)
        if inc_lower:
            pools.append(string.ascii_lowercase)
        if inc_digits:
            pools.append(string.digits)
        if inc_symbols:
            pools.append(string.punctuation)

        if len(pools) < 2:
            print("Error: You must select at least 2 character types. Please try again.")
        else:
            return pools


def generate_cli_password(length, pools):
    # Ensure at least one character from each chosen category
    password_chars = [random.choice(pool) for pool in pools]
    all_chars = "".join(pools)
    password_chars.extend(random.choice(all_chars) for _ in range(length - len(password_chars)))
    random.shuffle(password_chars)
    return "".join(password_chars)


def main():
    print("=== Command-Line Password Generator ===")
    while True:
        length = get_password_length()
        pools = get_character_pools()
        password = generate_cli_password(length, pools)
        print(f"\nGenerated Password: {password}\n")

        again = input("Generate another password? (y/n): ").strip().lower()
        if again != 'y':
            print("Exiting Password Generator. Stay secure!")
            break


if __name__ == "__main__":
    main()