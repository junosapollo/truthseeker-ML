# Truth Seeker: Real-Time Misinformation Detector

Truth Seeker is an end-to-end misinformation detection system. It leverages machine learning to help users analyze highlighted text directly from their browser and assess its truthfulness in real-time. 

## 🏗️ System Architecture

The project is divided into three main components:

1. **ML Model Training (`colab_training/`)**: Contains scripts designed to be run in Google Colab to train a misinformation detection model using the Truth Seeker dataset.
2. **Backend API (`api/`)**: A fast, local Python FastAPI server that serves the trained machine learning model and processes text evaluation requests.
3. **Browser Extension (`extension/`)**: A custom Chrome Extension that integrates with the browser, allowing users to highlight any text on a webpage, send it to the local API, and instantly see a truthfulness score or analysis.

## 📂 Repository Structure

```text
truthseeker/
├── api/                        # FastAPI server deployment code
│   ├── models/                 # Directory for storing trained ML models
│   ├── api.py                  # Main FastAPI application
│   └── requirements.txt        # Python dependencies for the backend
├── colab_training/             # Model training code
│   └── train_model.py          # Script for building and training the model
├── extension/                  # Chrome Extension source code
│   ├── background.js           # Service worker for handling API requests
│   ├── content.js              # Content script for extracting user-highlighted text
│   ├── content.css             # Styling for the in-page popups/results
│   ├── manifest.json           # Extension configuration
│   └── icons/                  # Extension icons
└── TruthSeeker-2024-dataset/   # Dataset used for training
```

## 🚀 Getting Started

### 1. Training the Model
1. Upload the contents of `colab_training/` to Google Colab.
2. Ensure you have access to the Truth Seeker dataset.
3. Run `train_model.py` to train and export your model.
4. Place the exported model files into the `api/models/` directory.

### 2. Running the Local API
The backend requires Python 3. Navigating to the `api` directory:

```bash
cd api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api:app --host 0.0.0.0 --port 8000
```
*(adjust the command `uvicorn api:app` based on the exact setup inside `api.py`)*

### 3. Installing the Chrome Extension
1. Open Google Chrome and navigate to `chrome://extensions/`.
2. Enable **Developer mode** in the top right corner.
3. Click **Load unpacked** and select the `truthseeker/extension/` directory.
4. The extension is now installed. Highlight any text on a webpage, right-click, or use the extension popup to analyze the text's validity.

## 🛠️ Built With

* [FastAPI](https://fastapi.tiangolo.com/) - Web framework for developing the API
* Python & Machine Learning infrastructure (Google Colab)
* Vanilla JavaScript/CSS and the Chrome Extensions API

## 📝 License
This project is open-source and available under the terms of the MIT License.
