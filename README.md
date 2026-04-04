# UCI Capstone 2026: Wayvia Hyperlocal Retail Intelligence

This is the official repository for the UCI Capstone 2026 project in partnership with Wayvia.

## Project Overview

This project aims to develop a mobile application that enables users to capture hyperlocal retail inventory data through receipt scanning and in-store shelf photography. The app will automatically itemize products from photos and receipts, extracting detailed product information including SKUs, prices, availability, and quantities to provide real-time inventory insights to major retail brands.

More info coming soon.

## Mobile Frontend

The mobile frontend has been bootstrapped with React Native and Expo using `npx create-expo-app@latest`. See [the documentation](https://docs.expo.dev/) for more information.

### Prerequisites

- Latest version of Node.js
- Expo Go <img src="https://is1-ssl.mzstatic.com/image/thumb/PurpleSource211/v4/be/84/84/be8484d1-88fd-1e06-fe73-c1da33fd8140/Placeholder.mill/400x400bb-75.webp" height="20"> app on your mobile device (available on Android/iOS)

### Running the Mobile Frontend

```bash
# clone the repository (if not already)
git clone https://github.com/PriceSpider-NeuIntel/uci-capstone-2026.git
cd mobile

# install Node.js dependencies
npm install

# start the Expo runtime
npm run start

# open Expo Go on your mobile device and scan the QR code in the console
```

## FastAPI Backend

### Prerequisites

- Latest version of Python 3

### Running the FastAPI Backend

```bash
# clone the repository (if not already)
git clone https://github.com/PriceSpider-NeuIntel/uci-capstone-2026.git
cd server

# install Python dependencies (virtual environment recommended)
pip install -r requirements.txt

# to process images with Gemini, first create a Gemini API key
# then create an .env file in the server directory with the following format:
GEMINI_API_KEY=your_api_key

# start the FastAPI server
fastapi dev --port 8000

# head to http://localhost:8000/docs to test the API

# to expose the API to your phone, use VS Code port forwarding to
# expose port 8000 to the public internet, then paste the link in
# mobile/constants/api.ts
```
