from app.services.stock_data import get_stock_name

print("HK 00700:", get_stock_name("00700", "HK"))
print("HK 00853:", get_stock_name("00853", "HK"))
print("US AAPL:", get_stock_name("AAPL", "US"))
print("US TSLA:", get_stock_name("TSLA", "US"))
