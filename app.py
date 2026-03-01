"""
Simple CLI application for user login demonstration.
"""
from services.auth_service import (
    AuthService,
    InvalidCredentialsError,
    AccountDisabledError,
    ValidationError,
)


def main():
    auth = AuthService()

    print("=" * 50)
    print("  User Login System")
    print("=" * 50)

    # Register a demo user
    try:
        auth.register("demo_user", "password123", "demo@example.com")
        print("\n[INFO] Demo user created: username='demo_user', password='password123'\n")
    except ValidationError as e:
        print(f"[ERROR] Registration failed: {e}")

    while True:
        print("\nOptions:")
        print("  1. Login")
        print("  2. Register")
        print("  3. Exit")
        choice = input("\nSelect an option: ").strip()

        if choice == "1":
            username = input("Username: ").strip()
            password = input("Password: ").strip()
            try:
                result = auth.login(username, password)
                print(f"\n✅ {result['message']}")
                print(f"   Welcome, {result['user']['username']}!")
                print(f"   Session Token: {result['session_token'][:16]}...")
            except (InvalidCredentialsError, AccountDisabledError, ValidationError) as e:
                print(f"\n❌ Login failed: {e}")

        elif choice == "2":
            username = input("Choose a username: ").strip()
            password = input("Choose a password: ").strip()
            email = input("Enter your email: ").strip()
            try:
                user = auth.register(username, password, email)
                print(f"\n✅ Registration successful! Welcome, {user.username}.")
            except ValidationError as e:
                print(f"\n❌ Registration failed: {e}")

        elif choice == "3":
            print("\nGoodbye!")
            break
        else:
            print("\nInvalid option. Please try again.")


if __name__ == "__main__":
    main()