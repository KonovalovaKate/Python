class BankAccount:
    def __init__(self, owner: str, initial_balance: float = 0):
        if initial_balance < 0:
            raise ValueError("Початковий баланс не може бути від'ємним")
        self.owner = owner
        self.__balance = initial_balance

    def deposit(self, amount: float):
        if amount <= 0:
            raise ValueError("Сума депозиту має бути більше нуля")
        self.__balance += amount
        print(f"Поповнено: {amount:.2f} грн. Баланс: {self.__balance:.2f} грн")

    def withdraw(self, amount: float):
        if amount <= 0:
            raise ValueError("Сума зняття має бути більше нуля")
        if amount > self.__balance:
            raise ValueError(f"Недостатньо коштів. Баланс: {self.__balance:.2f} грн")
        self.__balance -= amount
        print(f"Знято: {amount:.2f} грн. Баланс: {self.__balance:.2f} грн")

    def get_balance(self) -> float:
        return self.__balance

    def __str__(self):
        return f"Аккаунт [{self.owner}] | Баланс: {self.__balance:.2f} грн"


if __name__ == "__main__":
    name = input("Введіть ім'я власника: ")
    account = BankAccount(name)
    print(account)

    while True:
        print("\n1 - Поповнити  2 - Зняти  0 - Вихід")
        choice = input("Оберіть дію: ").strip()

        if choice == "0":
            break
        elif choice in ("1", "2"):
            try:
                amount = float(input("Введіть суму: "))
                if choice == "1":
                    account.deposit(amount)
                else:
                    account.withdraw(amount)
            except ValueError as e:
                print(f"Помилка: {e}")
        else:
            print("Невірна дія, спробуйте ще раз")

    print(f"\nФінальний баланс: {account.get_balance():.2f} грн")
