
# Subtitle Extraction and Storage with Django, S3, and DynamoDB

This Django application extracts subtitles from uploaded videos, stores them in DynamoDB, and provides a search interface for viewing videos and their subtitles.

Key Features
Subtitle Extraction: Leverages CCExtractor to extract subtitles from videos in SRT format.
Subtitle Conversion: Converts SRT subtitles to VTT format for web compatibility.
S3 Storage: Stores videos and VTT files in Amazon S3 for efficient retrieval.
DynamoDB Storage: Stores extracted subtitle data in JSON format within a DynamoDB table for structured querying.
Search Functionality: Allows users to search for videos by name and view them along with their corresponding subtitles.
Prerequisites
Python 3.x
Django
boto3 (AWS SDK for Python)
webvtt
CCExtractor
An AWS account with S3 and DynamoDB services configured
Installation
Clone this repository.
Install required libraries: pip install -r requirements.txt
Replace placeholders in the code with your actual AWS credentials and region.
Usage
Run the Django development server: python manage.py runserver
Access the application in your web browser (usually at http://127.0.0.1:8000/).
Upload a video file to initiate subtitle extraction and storage.