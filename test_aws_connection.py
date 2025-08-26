#!/usr/bin/env python3
"""
AWS Textract Connection Test
Verifies AWS credentials and Textract API access
"""

import boto3
import json
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

def test_aws_credentials():
    """Test AWS credentials and basic connectivity."""
    print("Testing AWS Credentials and Textract Access...")
    print("=" * 50)
    
    try:
        # Test basic AWS credentials
        print("1. Checking AWS credentials...")
        session = boto3.Session()
        credentials = session.get_credentials()
        
        if credentials is None:
            print("❌ No AWS credentials found!")
            print("Please configure your credentials using one of these methods:")
            print("   - aws configure")
            print("   - Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
            print("   - Use IAM roles (if on EC2)")
            return False
        
        print(f"✅ AWS credentials found")
        print(f"   Access Key ID: {credentials.access_key[:8]}...")
        
        # Test STS (to verify credentials work)
        print("\n2. Testing credential validity...")
        sts_client = boto3.client('sts')
        identity = sts_client.get_caller_identity()
        print(f"✅ Credentials valid")
        print(f"   Account: {identity.get('Account', 'Unknown')}")
        print(f"   User/Role: {identity.get('Arn', 'Unknown')}")
        
        # Test Textract access
        print("\n3. Testing Textract API access...")
        textract_client = boto3.client('textract', region_name='us-east-1')
        
        # Try to call a simple Textract operation (this will fail but tells us about permissions)
        try:
            # This should fail with InvalidParameterException, not AccessDenied
            textract_client.detect_document_text(Document={'Bytes': b''})
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'InvalidParameterException':
                print("✅ Textract API accessible (got expected InvalidParameter error)")
                return True
            elif error_code == 'AccessDenied':
                print("❌ Access denied to Textract API")
                print("Your AWS user/role needs textract:DetectDocumentText and textract:AnalyzeDocument permissions")
                return False
            else:
                print(f"❌ Unexpected error: {error_code}")
                print(f"   Message: {e.response['Error']['Message']}")
                return False
        
        return True
        
    except NoCredentialsError:
        print("❌ No AWS credentials configured")
        return False
    except PartialCredentialsError:
        print("❌ Incomplete AWS credentials")
        return False
    except ClientError as e:
        print(f"❌ AWS API Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_with_sample_image():
    """Test Textract with a minimal sample image (if available)."""
    print("\n4. Testing with minimal image data...")
    
    try:
        textract_client = boto3.client('textract', region_name='us-east-1')
        
        # Create a minimal 1x1 pixel PNG image in memory
        import base64
        
        # Minimal PNG image (1x1 transparent pixel)
        minimal_png = base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
        )
        
        response = textract_client.detect_document_text(
            Document={'Bytes': minimal_png}
        )
        
        print("✅ Textract API call successful!")
        print(f"   Response received with {len(response.get('Blocks', []))} blocks")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'UnsupportedDocumentException':
            print("✅ Textract API accessible (minimal image not supported, but API works)")
            return True
        elif error_code == 'AccessDenied':
            print("❌ Access denied to Textract")
            return False
        else:
            print(f"⚠️  API accessible but got error: {error_code}")
            print(f"   Message: {e.response['Error']['Message']}")
            return True  # API is accessible, just image issue
    except Exception as e:
        print(f"❌ Error testing Textract: {e}")
        return False

def show_aws_config_help():
    """Show help for configuring AWS credentials."""
    print("\nAWS Configuration Help:")
    print("=" * 30)
    print("\nOption 1: AWS CLI Configuration")
    print("   pip install awscli")
    print("   aws configure")
    print("   # Enter your Access Key ID, Secret Access Key, region (us-east-1), output format (json)")
    
    print("\nOption 2: Environment Variables")
    print("   export AWS_ACCESS_KEY_ID=your_access_key_here")
    print("   export AWS_SECRET_ACCESS_KEY=your_secret_key_here")
    print("   export AWS_DEFAULT_REGION=us-east-1")
    
    print("\nOption 3: AWS Credentials File")
    print("   Create ~/.aws/credentials with:")
    print("   [default]")
    print("   aws_access_key_id = your_access_key_here")
    print("   aws_secret_access_key = your_secret_key_here")
    
    print("\nRequired Permissions:")
    print("   Your AWS user/role needs these permissions:")
    print("   - textract:DetectDocumentText")
    print("   - textract:AnalyzeDocument")

def main():
    print("AWS Textract Connection Test")
    print("=" * 40)
    
    # Test basic connectivity
    if test_aws_credentials():
        # If basic test passes, try with sample image
        test_with_sample_image()
        print("\n🎉 AWS Textract setup appears to be working!")
        print("\nYou can now use the historical_education_textract.py script.")
    else:
        print("\n❌ AWS setup needs attention.")
        show_aws_config_help()

if __name__ == "__main__":
    main()