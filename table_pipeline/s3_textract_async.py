#!/usr/bin/env python3

import boto3
import json
import sys
import time
from botocore.exceptions import ClientError, NoCredentialsError
from pathlib import Path

class ProcessType:
    DETECTION = 1
    ANALYSIS = 2

class S3TextractProcessor:
    def __init__(self, role_arn, bucket, document, region_name='us-east-2'):
        """
        Initialize the Textract processor using Amazon's recommended pattern
        
        Args:
            role_arn (str): IAM role ARN for Textract to access S3 and SNS
            bucket (str): S3 bucket containing the document
            document (str): S3 key of the document
            region_name (str): AWS region
        """
        self.roleArn = role_arn
        self.bucket = bucket
        self.document = document
        self.region_name = region_name
        self.jobId = ''
        self.sqsQueueUrl = ''
        self.snsTopicArn = ''
        self.processType = ProcessType.ANALYSIS
        
        try:
            self.textract = boto3.client('textract', region_name=region_name)
            self.sqs = boto3.client('sqs', region_name=region_name)
            self.sns = boto3.client('sns', region_name=region_name)
            print(f"✓ Initialized Textract processor for s3://{bucket}/{document}")
        except Exception as e:
            print(f"Error initializing AWS clients: {e}")
            raise

    def create_topic_and_queue(self):
        """Create SNS topic and SQS queue for notifications"""
        millis = str(int(round(time.time() * 1000)))

        # Create SNS topic
        snsTopicName = "AmazonTextractTopic" + millis
        topicResponse = self.sns.create_topic(Name=snsTopicName)
        self.snsTopicArn = topicResponse['TopicArn']
        print(f"✓ Created SNS topic: {snsTopicName}")

        # Create SQS queue
        sqsQueueName = "AmazonTextractQueue" + millis
        self.sqs.create_queue(QueueName=sqsQueueName)
        self.sqsQueueUrl = self.sqs.get_queue_url(QueueName=sqsQueueName)['QueueUrl']
        print(f"✓ Created SQS queue: {sqsQueueName}")

        attribs = self.sqs.get_queue_attributes(QueueUrl=self.sqsQueueUrl,
                                               AttributeNames=['QueueArn'])['Attributes']
        sqsQueueArn = attribs['QueueArn']

        # Subscribe SQS queue to SNS topic
        self.sns.subscribe(
            TopicArn=self.snsTopicArn,
            Protocol='sqs',
            Endpoint=sqsQueueArn)

        # Authorize SNS to write to SQS queue
        policy = """{{
  "Version":"2012-10-17",
  "Statement":[
    {{
      "Sid":"MyPolicy",
      "Effect":"Allow",
      "Principal" : {{"AWS" : "*"}},
      "Action":"SQS:SendMessage",
      "Resource": "{}",
      "Condition":{{
        "ArnEquals":{{
          "aws:SourceArn": "{}"
        }}
      }}
    }}
  ]
}}""".format(sqsQueueArn, self.snsTopicArn)

        self.sqs.set_queue_attributes(
            QueueUrl=self.sqsQueueUrl,
            Attributes={'Policy': policy})

    def delete_topic_and_queue(self):
        """Clean up SNS topic and SQS queue"""
        try:
            self.sqs.delete_queue(QueueUrl=self.sqsQueueUrl)
            self.sns.delete_topic(TopicArn=self.snsTopicArn)
            print("✓ Cleaned up SNS topic and SQS queue")
        except Exception as e:
            print(f"Warning: Error cleaning up resources: {e}")

    def process_document(self, process_type=ProcessType.ANALYSIS, feature_types=None):
        """
        Start document processing and wait for completion
        
        Args:
            process_type: ProcessType.DETECTION or ProcessType.ANALYSIS
            feature_types: List of features for analysis (TABLES, FORMS, etc.)
        """
        if feature_types is None:
            feature_types = ["TABLES", "FORMS"]
            
        self.processType = process_type
        jobFound = False

        try:
            # Start the appropriate processing job
            if process_type == ProcessType.DETECTION:
                response = self.textract.start_document_text_detection(
                    DocumentLocation={'S3Object': {'Bucket': self.bucket, 'Name': self.document}},
                    NotificationChannel={'RoleArn': self.roleArn, 'SNSTopicArn': self.snsTopicArn})
                print('✓ Started text detection job')
            elif process_type == ProcessType.ANALYSIS:
                response = self.textract.start_document_analysis(
                    DocumentLocation={'S3Object': {'Bucket': self.bucket, 'Name': self.document}},
                    FeatureTypes=feature_types,
                    NotificationChannel={'RoleArn': self.roleArn, 'SNSTopicArn': self.snsTopicArn})
                print(f'✓ Started document analysis job with features: {", ".join(feature_types)}')
            else:
                raise ValueError("Invalid processing type. Choose DETECTION or ANALYSIS.")

            self.jobId = response['JobId']
            print(f'Job ID: {self.jobId}')

            # Wait for job completion via SQS notifications
            print('Waiting for job completion...')
            dotLine = 0
            
            while not jobFound:
                sqsResponse = self.sqs.receive_message(
                    QueueUrl=self.sqsQueueUrl,
                    MessageAttributeNames=['ALL'],
                    MaxNumberOfMessages=10)

                if 'Messages' not in sqsResponse:
                    if dotLine < 40:
                        print('.', end='')
                        dotLine += 1
                    else:
                        print()
                        dotLine = 0
                    sys.stdout.flush()
                    time.sleep(5)
                    continue

                for message in sqsResponse['Messages']:
                    notification = json.loads(message['Body'])
                    textMessage = json.loads(notification['Message'])
                    
                    print(f"\nJob Status: {textMessage['Status']}")
                    
                    if str(textMessage['JobId']) == self.jobId:
                        print(f'✓ Job completed: {textMessage["JobId"]}')
                        if textMessage['Status'] == 'SUCCEEDED':
                            jobFound = True
                            return self.get_results(textMessage['JobId'])
                        elif textMessage['Status'] == 'FAILED':
                            print(f"✗ Job failed: {textMessage.get('StatusMessage', 'Unknown error')}")
                            return None
                    else:
                        print(f"Different job completed: {textMessage['JobId']}")
                    
                    # Delete the message
                    self.sqs.delete_message(QueueUrl=self.sqsQueueUrl,
                                          ReceiptHandle=message['ReceiptHandle'])

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'InvalidS3ObjectException':
                print(f"Error: File s3://{self.bucket}/{self.document} not found or inaccessible")
            elif error_code == 'UnsupportedDocumentException':
                print(f"Error: Document format not supported")
            elif error_code == 'AccessDenied':
                print(f"Error: Access denied. Check IAM permissions")
            else:
                print(f"Error starting analysis: {e}")
            raise

        return None

    def get_results(self, jobId):
        """
        Retrieve complete results from completed job
        
        Args:
            jobId (str): Job ID of completed job
        
        Returns:
            dict: Complete analysis results
        """
        print("Retrieving results...")
        maxResults = 1000
        paginationToken = None
        finished = False
        all_blocks = []

        while not finished:
            response = None

            if self.processType == ProcessType.ANALYSIS:
                if paginationToken is None:
                    response = self.textract.get_document_analysis(
                        JobId=jobId, MaxResults=maxResults)
                else:
                    response = self.textract.get_document_analysis(
                        JobId=jobId, MaxResults=maxResults, NextToken=paginationToken)

            elif self.processType == ProcessType.DETECTION:
                if paginationToken is None:
                    response = self.textract.get_document_text_detection(
                        JobId=jobId, MaxResults=maxResults)
                else:
                    response = self.textract.get_document_text_detection(
                        JobId=jobId, MaxResults=maxResults, NextToken=paginationToken)

            blocks = response['Blocks']
            all_blocks.extend(blocks)

            if 'NextToken' in response:
                paginationToken = response['NextToken']
            else:
                finished = True

        print(f'✓ Retrieved {len(all_blocks)} blocks from {response["DocumentMetadata"]["Pages"]} pages')

        # Return structured results similar to your existing format
        return {
            'job_id': jobId,
            'job_status': 'SUCCEEDED',
            'document_metadata': response['DocumentMetadata'],
            'blocks': all_blocks,
            'total_blocks': len(all_blocks)
        }

    def save_results_to_file(self, results, output_file):
        """Save results to JSON file"""
        try:
            # Convert to format compatible with your existing extract_table_raw.py
            output_data = {
                'DocumentMetadata': results['document_metadata'],
                'Blocks': results['blocks']
            }
            
            with open(output_file, 'w') as f:
                json.dump(output_data, f, indent=2, default=str)
            print(f"✓ Results saved to: {output_file}")
        except Exception as e:
            print(f"Error saving results: {e}")
            raise

    def process_document_complete_workflow(self, output_file=None, process_type=ProcessType.ANALYSIS, feature_types=None):
        """
        Complete workflow: create queue, process document, get results, cleanup
        
        Args:
            output_file (str): File to save results
            process_type: DETECTION or ANALYSIS
            feature_types: Features to extract for analysis
        
        Returns:
            dict: Complete analysis results
        """
        try:
            # Setup
            self.create_topic_and_queue()
            
            # Process document
            results = self.process_document(process_type, feature_types)
            
            if results and output_file:
                self.save_results_to_file(results, output_file)
                
            return results
            
        finally:
            # Always cleanup
            self.delete_topic_and_queue()

def main():
    if len(sys.argv) < 4:
        print("Usage: python s3_textract_async.py <role_arn> <s3_bucket> <s3_key> [output_file] [process_type] [features]")
        print()
        print("Examples:")
        print("  python s3_textract_async.py arn:aws:iam::123:role/TextractRole my-bucket document.pdf")
        print("  python s3_textract_async.py arn:aws:iam::123:role/TextractRole my-bucket document.pdf results.json")
        print("  python s3_textract_async.py arn:aws:iam::123:role/TextractRole my-bucket document.pdf results.json ANALYSIS TABLES,FORMS")
        print()
        print("Process types: DETECTION, ANALYSIS")
        print("Features (for ANALYSIS): TABLES, FORMS, LAYOUT, SIGNATURES, QUERIES")
        print()
        print("Note: The IAM role must have permissions for:")
        print("  - s3:GetObject on your bucket")
        print("  - sns:Publish")
        print("  - textract:StartDocument* and textract:GetDocument*")
        sys.exit(1)

    role_arn = sys.argv[1]
    s3_bucket = sys.argv[2]
    s3_key = sys.argv[3]
    output_file = sys.argv[4] if len(sys.argv) > 4 else None
    
    # Parse process type
    process_type = ProcessType.ANALYSIS  # Default
    if len(sys.argv) > 5:
        if sys.argv[5].upper() == 'DETECTION':
            process_type = ProcessType.DETECTION
        elif sys.argv[5].upper() == 'ANALYSIS':
            process_type = ProcessType.ANALYSIS

    # Parse feature types
    feature_types = ['TABLES', 'FORMS']  # Default
    if len(sys.argv) > 6:
        feature_types = [f.strip().upper() for f in sys.argv[6].split(',')]

    # Set default output file if none provided
    if not output_file:
        document_name = Path(s3_key).stem
        output_file = f"{document_name}_textract_results.json"

    try:
        processor = S3TextractProcessor(role_arn, s3_bucket, s3_key)
        results = processor.process_document_complete_workflow(
            output_file=output_file,
            process_type=process_type,
            feature_types=feature_types
        )

        if results and results.get('job_status') == 'SUCCEEDED':
            print(f"\n✓ Processing completed successfully!")
            print(f"  Results saved to: {output_file}")
            print(f"  You can now use extract_table_raw.py to process the results")
        else:
            print(f"\n✗ Processing failed or incomplete")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()