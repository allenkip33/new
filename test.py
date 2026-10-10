import unittest
import json
from app import app, inventory_db

class InventoryApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        # Reset inventory database state before each test
        inventory_db.clear()
        inventory_db.extend([
            {"id": "1001", "name": "Wireless Mouse", "quantity": 50, "price": 29.99, "source": "manual"},
            {"id": "1002", "name": "Mechanical Keyboard", "quantity": 20, "price": 89.99, "source": "manual"}
        ])

    def test_get_all_inventory(self):
        response = self.app.get('/inventory')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.data)), 2)

    def test_get_single_item(self):
        response = self.app.get('/inventory/1001')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Wireless Mouse", response.data)

    def test_add_item_success(self):
        payload = {"id": "1003", "name": "USB-C Cable", "quantity": 100, "price": 9.99}
        response = self.app.post('/inventory', json=payload)
        self.assertEqual(response.status_code, 201)
        self.assertIn(b"USB-C Cable", response.data)

    def test_patch_item(self):
        payload = {"price": 24.99, "quantity": 45}
        response = self.app.patch('/inventory/1001', json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["price"], 24.99)
        self.assertEqual(data["quantity"], 45)

    def test_delete_item(self):
        response = self.app.delete('/inventory/1002')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(inventory_db), 1)

if __name__ == '__main__':
    unittest.main()
