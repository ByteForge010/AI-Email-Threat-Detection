# AI-Powered Email Threat Detection & Forensic Intelligence

An AI-powered cybersecurity platform that analyzes `.eml` files to detect potential email threats and generate forensic intelligence.

## Features

- AI-based email threat detection
- Threat confidence and risk assessment
- SPF, DKIM & DMARC analysis
- Public IP extraction from email headers
- IP geolocation
- Proxy/anonymizer detection
- ISP, ASN, country, region and city information
- Automated forensic report generation
- Web interface for uploading and analyzing emails

## Tech Stack

- Python
- Flask
- Scikit-learn
- TF-IDF
- Logistic Regression
- IP2Location
- IP2Proxy
- HTML, CSS & JavaScript

## Setup

- pip install -r requirements.txt

## Set Up IP Databases

- Download the database ZIP included in the repository: DATASETS.rar

- Extract it and place the database files in:
  
    - GEOLOCATION > IP2Location > IP2LOCATION-LITE-DB11.BIN
  
    - GEOLOCATION > IP2PROXY > IP2PROXY-LITE-PX12.BIN

## Run the Application

- python app.py

## Model

- The project includes a pre-trained NLP model, so the original training dataset is not required to run the application.
The model uses:
    - TF-IDF Vectorization
    - Logistic Regression
    - Email text classification
    - Threat confidence scoring
