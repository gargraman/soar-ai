"""
S3 Bucket client for managing file uploads and processing
Handles file operations for the ai-soar bucket
"""

import json
import csv
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import tempfile
import os

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)

class BucketClient:
    """S3 Bucket client for file operations"""
    
    def __init__(self, bucket_config: Dict[str, Any]):
        self.bucket_name = bucket_config["bucket_name"]
        self.region = bucket_config["region"]
        self.unprocessed_prefix = bucket_config["unprocessed_prefix"]
        self.processed_prefix = bucket_config["processed_prefix"]
        self.check_interval = bucket_config["check_interval"]
        
        # Initialize S3 client
        try:
            self.s3_client = boto3.client('s3', region_name=self.region)
            logger.info(f"Initialized S3 client for bucket: {self.bucket_name}")
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure AWS credentials.")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {str(e)}")
            raise
    
    async def list_unprocessed_files(self) -> List[Dict[str, Any]]:
        """List all unprocessed files in the bucket"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=self.unprocessed_prefix
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    # Skip directory entries
                    if not obj['Key'].endswith('/'):
                        files.append({
                            'key': obj['Key'],
                            'filename': os.path.basename(obj['Key']),
                            'size': obj['Size'],
                            'last_modified': obj['LastModified'],
                            'etag': obj['ETag'].strip('"')
                        })
            
            logger.info(f"Found {len(files)} unprocessed files")
            return files
            
        except ClientError as e:
            logger.error(f"Error listing unprocessed files: {str(e)}")
            raise
    
    async def download_file(self, file_key: str) -> Tuple[str, str]:
        """Download a file from S3 to a temporary location"""
        try:
            # Create temporary file
            temp_dir = tempfile.mkdtemp()
            filename = os.path.basename(file_key)
            local_path = os.path.join(temp_dir, filename)
            
            # Download file from S3
            self.s3_client.download_file(
                Bucket=self.bucket_name,
                Key=file_key,
                Filename=local_path
            )
            
            logger.info(f"Downloaded {file_key} to {local_path}")
            return local_path, filename
            
        except ClientError as e:
            logger.error(f"Error downloading file {file_key}: {str(e)}")
            raise
    
    async def move_to_processed(self, file_key: str) -> str:
        """Move file from unprocessed to processed folder"""
        try:
            # Generate new key in processed folder
            filename = os.path.basename(file_key)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            processed_key = f"{self.processed_prefix}{timestamp}_{filename}"
            
            # Copy object to processed folder
            copy_source = {'Bucket': self.bucket_name, 'Key': file_key}
            self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=self.bucket_name,
                Key=processed_key
            )
            
            # Delete original file from unprocessed folder
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            
            logger.info(f"Moved {file_key} to {processed_key}")
            return processed_key
            
        except ClientError as e:
            logger.error(f"Error moving file {file_key}: {str(e)}")
            raise
    
    async def upload_results(self, file_key: str, results: Dict[str, Any]) -> str:
        """Upload processing results to S3"""
        try:
            # Generate results key
            base_filename = os.path.basename(file_key)
            name, ext = os.path.splitext(base_filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_key = f"{self.processed_prefix}results/{timestamp}_{name}_results.json"
            
            # Upload results as JSON
            results_json = json.dumps(results, indent=2, default=str)
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=results_key,
                Body=results_json,
                ContentType='application/json'
            )
            
            logger.info(f"Uploaded results to {results_key}")
            return results_key
            
        except ClientError as e:
            logger.error(f"Error uploading results for {file_key}: {str(e)}")
            raise
    
    def load_events_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Load events from downloaded file (JSON, CSV, or syslog)"""
        events = []
        
        try:
            if file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        events = data
                    else:
                        events = [data]
            elif file_path.endswith('.csv'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    events = list(reader)
            elif file_path.endswith('.log') or file_path.endswith('.syslog'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    events = [line.strip() for line in f if line.strip()]
            else:
                # Auto-detect format
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    try:
                        data = json.loads(content)
                        if isinstance(data, list):
                            events = data
                        else:
                            events = [data]
                    except json.JSONDecodeError:
                        # Try line-by-line syslog
                        events = [line.strip() for line in content.split('\n') if line.strip()]
            
            logger.info(f"Loaded {len(events)} events from {file_path}")
            return events
            
        except Exception as e:
            logger.error(f"Error loading events from {file_path}: {str(e)}")
            raise
    
    async def cleanup_temp_file(self, file_path: str):
        """Clean up temporary downloaded file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                # Also remove parent temp directory if empty
                parent_dir = os.path.dirname(file_path)
                if os.path.exists(parent_dir) and not os.listdir(parent_dir):
                    os.rmdir(parent_dir)
                logger.debug(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp file {file_path}: {str(e)}")
    
    async def process_bucket_files(self, event_processor, prompt: str = None) -> List[Dict[str, Any]]:
        """Process all unprocessed files in the bucket"""
        if not prompt:
            prompt = "Analyze security events and take appropriate action based on threat level"
        
        results = []
        
        # Get list of unprocessed files
        unprocessed_files = await self.list_unprocessed_files()
        
        if not unprocessed_files:
            logger.info("No unprocessed files found in bucket")
            return results
        
        logger.info(f"Processing {len(unprocessed_files)} files from bucket")
        
        for file_info in unprocessed_files:
            file_key = file_info['key']
            filename = file_info['filename']
            
            try:
                logger.info(f"Processing file: {filename}")
                
                # Download file to temporary location
                local_path, _ = await self.download_file(file_key)
                
                # Load events from file
                events = self.load_events_from_file(local_path)
                
                # Process each event
                file_results = []
                for i, event in enumerate(events):
                    logger.info(f"Processing event {i+1}/{len(events)} from {filename}")
                    
                    # Process single event
                    result = await event_processor.process_event(event, prompt)
                    file_results.append({
                        'event_index': i + 1,
                        'event_data': event,
                        'processing_result': result
                    })
                
                # Upload processing results
                processing_summary = {
                    'source_file': filename,
                    'source_key': file_key,
                    'processed_at': datetime.now().isoformat(),
                    'total_events': len(events),
                    'prompt_used': prompt,
                    'results': file_results
                }
                
                results_key = await self.upload_results(file_key, processing_summary)
                
                # Move original file to processed folder
                processed_key = await self.move_to_processed(file_key)
                
                results.append({
                    'original_file': filename,
                    'original_key': file_key,
                    'processed_key': processed_key,
                    'results_key': results_key,
                    'events_processed': len(events),
                    'processing_results': file_results
                })
                
                # Clean up temporary file
                await self.cleanup_temp_file(local_path)
                
                logger.info(f"Successfully processed {filename} ({len(events)} events)")
                
            except Exception as e:
                logger.error(f"Error processing file {filename}: {str(e)}")
                # Still try to clean up temp file
                try:
                    await self.cleanup_temp_file(local_path)
                except:
                    pass
                continue
        
        logger.info(f"Completed processing {len(results)} files from bucket")
        return results