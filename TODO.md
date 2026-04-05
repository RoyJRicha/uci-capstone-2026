TODO

Frontend (Cody):

- store address search
- firebase auth

Backend:

- implement basic receipt scanning using some ocr text extraction tool. Seems like theres some python libraries/projects that might help with this.
  - opencv
  - git@github.com:ReceiptManager/receipt-parser-legacy.git
  - llm if needed
  - ????

  main data needed: - items bought and quantity - prices - what store - date/time - i think that's it for now

- processing flow of receipt part prettymuch the same as the shelf images
  receive image through FastAPI, store image into local/cloud data (currently working on uploading), upload parsed and structured data to SQL or other relational database. Upload csv's to cloud data storage if needed as well

- catch error when gemini api is down, and retry later or go to next steps in
  retrieval pipeline?

Currently working on (Daniel):
- Firebase database
- Uploading photos to google cloud bucket.
