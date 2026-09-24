import time
import logging

class MockDatabase:
    def __init__(self):
        self.inventory = {"X": 5}
        self.orders = []

    def get_stock(self, item_id):
        return self.inventory.get(item_id, 0)

    def add_order(self, item_id, quantity):
        self.inventory[item_id] = self.inventory.get(item_id, 0) + quantity
        self.orders.append({"item_id": item_id, "quantity": quantity})
        return True

class FaultInjector:
    def __init__(self):
        self.fault_type = None

    def set_fault(self, fault_type):
        self.fault_type = fault_type

class Environment:
    def __init__(self, fault_injector):
        self.db = MockDatabase()
        self.fault_injector = fault_injector

    def check_inventory(self, item_id: str) -> dict:
        """API idempotente para checar estoque."""
        stock = self.db.get_stock(item_id)
        return {"item_id": item_id, "stock": stock, "status": "success"}

    def order_item(self, item_id: str, quantity: int) -> dict:
        """API mutável para realizar pedido."""
        
        # Injeta falha de Timeout Tardio
        if self.fault_injector.fault_type == "late_timeout":
            # Simula a execução com sucesso no BD
            self.db.add_order(item_id, quantity)
            # Mas retorna erro de timeout para o agente
            raise TimeoutError("Connection timed out while waiting for supplier response.")
            
        # Execução Normal
        success = self.db.add_order(item_id, quantity)
        if success:
            return {"item_id": item_id, "ordered_quantity": quantity, "status": "success"}
        return {"status": "error", "message": "Failed to process order"}
