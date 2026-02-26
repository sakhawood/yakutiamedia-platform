print("INIT SHEETS START", flush=True)
self.events_book = self.client.open("Order_Yakutia.media")
self.photographers_book = self.client.open("Order_Photographers")

self.sheet_events = self.get_orders_sheet()
self.sheet_assignments = self.get_assignments_sheet()
self.sheet_photographers = self.get_photographers_sheet()
self.sheet_notifications = self.get_notifications_sheet()