import sys
import requests

BASE_URL = "http://127.0.0.1:5001/inventory"
SESSION_URL = "http://127.0.0.1:5001/session"

session = requests.Session()


def start_session():
    try:
        response = session.get(SESSION_URL, timeout=5)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


def show_menu():
    print("\n--- INVENTORY MANAGEMENT ---")
    print("1. View Inventory")
    print("2. Add Item")
    print("3. Find Product Online")
    print("4. Update Item")
    print("5. Delete Item")
    print("6. Exit")


def view_inventory():
    try:
        response = session.get(BASE_URL)

        if response.status_code == 401:
            if start_session():
                response = session.get(BASE_URL)

        if response.status_code == 200:
            items = response.json()

            if not items:
                print("\nInventory is empty.")
                return

            print("\n--- CURRENT INVENTORY ---")
            print(
                f"{'ID':<14} | "
                f"{'Name':<25} | "
                f"{'Quantity':<10} | "
                f"{'Price':<12} | "
                f"Source"
            )

            print("-" * 85)

            for item in items:
                print(
                    f"{item['id']:<14} | "
                    f"{item['name']:<25} | "
                    f"{item['quantity']:<10} | "
                    f"KSh {item['price']:<8.2f} | "
                    f"{item['source']}"
                )
        else:
            print("Failed to get inventory.")

    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to the Flask server.")
        print("Make sure app.py is running on port 5001.")


def add_item():
    print("\n--- ADD NEW ITEM ---")

    name = input("Enter Product Name: ").strip()

    if not name:
        print("Product name cannot be empty.")
        return

    try:
        quantity = int(input("Enter Quantity: ") or 0)
        price = float(input("Enter Price (KSh): ") or 0)
    except ValueError:
        print("Error: Quantity must be an integer.")
        print("Price must be a number.")
        return

    data = {
        "name": name,
        "quantity": quantity,
        "price": price,
        "source": "manual"
    }

    try:
        response = session.post(BASE_URL, json=data)

        if response.status_code == 201:
            item = response.json()
            print(
                f"\nSuccess! {item['name']} "
                f"was added with ID {item['id']}."
            )
        else:
            print(f"Error: {response.json().get('error')}")

    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to the Flask server.")


def find_external_item():
    print("\n--- FIND PRODUCT ONLINE ---")

    barcode = input("Enter Barcode: ").strip()

    if not barcode:
        print("Barcode cannot be empty.")
        return

    try:
        response = session.get(
            f"{BASE_URL}/external/{barcode}"
        )

        if response.status_code == 200:
            result = response.json()
            product = result["data"]

            print("\n--- PRODUCT FOUND ---")
            print(f"Name: {product['name']}")
            print(f"Barcode: {product['id']}")
            print(f"Source: {product['source']}")

            save = input(
                "\nSave this product to inventory? (yes/no): "
            ).strip().lower()

            if save == "yes":
                try:
                    quantity = int(
                        input("Enter Quantity: ") or 0
                    )
                    price = float(
                        input("Enter Price (KSh): ") or 0
                    )
                except ValueError:
                    print("Invalid quantity or price.")
                    return

                data = {
                    "id": product["id"],
                    "name": product["name"],
                    "quantity": quantity,
                    "price": price,
                    "source": product["source"]
                }

                add_response = session.post(
                    BASE_URL,
                    json=data
                )

                if add_response.status_code == 201:
                    print(
                        "Product successfully added to inventory."
                    )
                else:
                    print(
                        f"Error: "
                        f"{add_response.json().get('error')}"
                    )

        else:
            message = response.json().get(
                "message",
                "Product was not found."
            )
            print(f"\n{message}")

    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to the Flask server.")


def update_item():
    print("\n--- UPDATE ITEM ---")

    item_id = input("Enter Item ID: ").strip()

    if not item_id:
        print("Item ID cannot be empty.")
        return

    print("\nLeave a field empty if you don't want to change it.")

    name = input("New Name: ").strip()
    quantity = input("New Quantity: ").strip()
    price = input("New Price (KSh): ").strip()

    data = {}

    if name:
        data["name"] = name

    if quantity:
        try:
            data["quantity"] = int(quantity)
        except ValueError:
            print("Quantity must be an integer.")
            return

    if price:
        try:
            data["price"] = float(price)
        except ValueError:
            print("Price must be a number.")
            return

    if not data:
        print("No changes were made.")
        return

    try:
        response = session.patch(
            f"{BASE_URL}/{item_id}",
            json=data
        )

        if response.status_code == 200:
            print("Item updated successfully.")
        else:
            print(
                f"Error: "
                f"{response.json().get('error')}"
            )

    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to the Flask server.")


def delete_item():
    print("\n--- DELETE ITEM ---")

    item_id = input("Enter Item ID: ").strip()

    if not item_id:
        print("Item ID cannot be empty.")
        return

    confirm = input(
        f"Are you sure you want to delete item "
        f"{item_id}? (y/n): "
    ).strip().lower()

    if confirm != "y":
        print("Delete cancelled.")
        return

    try:
        response = session.delete(
            f"{BASE_URL}/{item_id}"
        )

        if response.status_code == 200:
            print(
                response.json().get(
                    "message",
                    "Item deleted."
                )
            )
        else:
            print(
                f"Error: "
                f"{response.json().get('error')}"
            )

    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to the Flask server.")


def main():
    if not start_session():
        print(
            "Warning: Could not connect to the Flask server."
        )
        print(
            "Make sure app.py is running on port 5001."
        )

    while True:
        show_menu()

        choice = input(
            "\nChoose an option (1-6): "
        ).strip()

        if choice == "1":
            view_inventory()

        elif choice == "2":
            add_item()

        elif choice == "3":
            find_external_item()

        elif choice == "4":
            update_item()

        elif choice == "5":
            delete_item()

        elif choice == "6":
            print("\nThank you for using the inventory system.")
            print("Goodbye!")
            sys.exit(0)

        else:
            print(
                "\nInvalid choice. "
                "Please choose a number from 1 to 6."
            )


if __name__ == "__main__":
    main()
