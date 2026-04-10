"""Trying Out various OCR methods"""
from receiptparser.config import read_config
from receiptparser.parser import process_receipt

config = read_config("uploads/germany.yml")
receipt = process_receipt(config, "uploads/receipt1.jpg")

print("Filename:   ", receipt.filename)
print("Company:    ", receipt.company)
print("Postal code:", receipt.postal)
print("Date:       ", receipt.date)
print("Amount:     ", receipt.sum)