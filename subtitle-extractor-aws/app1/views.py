# Import necessary libraries
import subprocess
from django.shortcuts import render
import webvtt
from boto3.dynamodb.conditions import Key
from django.core.files.storage import default_storage
import boto3
import json
import logging


# Define the view for the initial file upload form
def upload(request):
    return render(request, 'index.html')


# Define the view for the video player
def player(request):
    return render(request, 'player.html')


# Global variables for AWS and pre-signed URLs
AWS_ACCESS_KEY_ID = 'YOUR_AWS_ACCESS_KEY_ID'
AWS_SECRET_ACCESS_KEY = 'YOUR_AWS_SECRET_ACCESS_KEY'
AWS_STORAGE_BUCKET_NAME = "vimalrs"
AWS_REGION = "eu-north-1"
pre_signed_url_video = ""
pre_signed_url_vtt = ""


# Define the view for extracting subtitles and uploading to S3 and DynamoDB
def extract_subtitles(request):
    if request.method == 'POST':
        # Retrieve the uploaded video file
        video = request.FILES['video']

        # Save the video file temporarily
        with open('temp_file.mp4', 'wb') as temp_file:
            for chunk in video.chunks():
                temp_file.write(chunk)

        # Extract subtitles using CCExtractor
        video_name = video.name
        sp_list = video_name.split('.')
        video_name_sub = sp_list[0]

        # Run CCExtractor to generate SRT subtitles
        subprocess.run(['CCExtractor_win_portable\ccextractorwinfull.exe',
                        'temp_file.mp4', '-o', 'subtitles/' + video_name_sub + '.srt'])

        # Convert SRT to VTT format
        input_path = 'subtitles/' + video_name_sub + '.srt'
        output_path = 'subtitles/' + video_name_sub + '.vtt'
        captions = webvtt.from_srt(input_path)
        captions.save(output_path)

        # Convert VTT to JSON and upload to DynamoDB
        subprocess.run(
            ['webvtt-to-json', 'subtitles/' + video_name_sub + '.vtt', '-o', 'subtitles/' + video_name_sub + '.json'])
        upload_json_to_dynamodb('subtitles/' + video_name_sub + '.json', video_name_sub)

        # Upload video to S3 and generate pre-signed URL
        s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                                 aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                                 region_name=AWS_REGION, )
        default_storage.save(video_name, video)

        pre_signed_url_video = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': AWS_STORAGE_BUCKET_NAME,
                'Key': video_name
            },
            ExpiresIn=3600)

        # Save VTT file to S3 and generate pre-signed URL
        file_name = video_name_sub + '.vtt'
        with open('subtitles/' + video_name_sub + '.vtt', 'rb') as vtt_file:
            default_storage.save(file_name, vtt_file)

        pre_signed_url_vtt = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': AWS_STORAGE_BUCKET_NAME,
                'Key': file_name
            },
            ExpiresIn=3600
        )

    print('✅This is the subtitle link : ', pre_signed_url_vtt)
    return render(request, 'view_video.html', {'video_file': pre_signed_url_video, 'sub': pre_signed_url_vtt})


# Global variable for VTT file path
vtt_file_path = pre_signed_url_vtt


# Define the view for searching and viewing video details in DynamoDB
def view_video(request):
    response = []
    result = []
    if request.method == 'POST':
        search_word = request.POST.get('search')
        print('🔍 search word:', search_word)

        TABLE_NAME = "data"

        # Connect to DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name="eu-north-1")
        table = dynamodb.Table(TABLE_NAME)

        # Query DynamoDB table for video details
        response = table.query(
            KeyConditionExpression=Key('video_name').eq(search_word))
        result = response['Items']
        print(response['Items'])

        print('✅ items are: ', response)

        print('list creation done ✅')

    return render(request, 'view_video.html', {'results': result})


# Function to upload JSON data to DynamoDB
def upload_json_to_dynamodb(json_file_path, video_name):
    # AWS credentials and region
    aws_access_key_id = "YOUR_AWS_ACCESS_KEY_ID"
    aws_secret_access_key = "YOUR_AWS_SECRET_ACCESS_KEY"
    region_name = "eu-north-1"

    # DynamoDB table details
    table_name = "data"

    # Create a session and DynamoDB resource
    session = boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name
    )
    dynamodb = session.resource('dynamodb')
    table = dynamodb.Table(table_name)

    # Read JSON file
    try:
        with open(json_file_path, 'r') as json_file:
            data = json.load(json_file)
    except Exception as e:
        logging.error(f'Error reading JSON file: {e}')
        return

    # Upload each entry in the JSON file to DynamoDB with video_name as the primary key
    for item in data:
        # Add video_name to each item
        item['video_name'] = video_name

        try:
            response = table.put_item(Item=item)
            logging.info(f'Successfully added item to DynamoDB: {item}')
        except Exception as e:
            logging.error(f'Error adding item to DynamoDB: {e}')
            logging.error(f'Failed item details: {item}')

    logging.info('Done uploading to DynamoDB')
