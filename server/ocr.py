"""Trying Out various OCR methods"""
from receiptparser.config import read_config
from receiptparser.parser import process_receipt

CONFIG = read_config("uploads/germany.yml")  # config file necessary for receiptparser library

def _testReceiptParser(fileName):
    """Test the receipt parser library"""
    receipt = process_receipt(CONFIG, fileName)
    print("Filename:   ", receipt.filename)
    print("Company:    ", receipt.company)
    print("Postal code:", receipt.postal)
    print("Date:       ", receipt.date)
    print("Amount:     ", receipt.sum)

def testReceiptParser():
    """Test 4 different receipts"""
    _testReceiptParser("uploads/receipt1.jpg")
    _testReceiptParser("uploads/receipt2.jpg")
    _testReceiptParser("uploads/receipt3.jpg")
    _testReceiptParser("uploads/receipt4.jpg")
    

"""
This library was originally trainined on German receipts. Format is similar to US receipts,
but language differents seem to cause issues in identifying certain fields of the receipt.
Also, this library lacks the granularity necessary for our project, as it only recovers
the ZIP code, Company, Date of transaction, and Total cost.
In the following test, this library is unable to correctly identify the receipts as belonging
to Alberstsons, and it captures the zip code backwards/upside down as 21926 instead of 92612.
It is unable to capture date and amount in all tests
"""
testReceiptParser()