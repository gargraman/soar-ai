"""
Background service to monitor S3 bucket for new files and process them automatically
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Callable

from .bucket_client import BucketClient
from .event_processor import EventProcessor

logger = logging.getLogger(__name__)

class BucketMonitor:
    """Background service to monitor S3 bucket for new files"""
    
    def __init__(self, bucket_client: BucketClient, event_processor: EventProcessor, 
                 check_interval: int = 30, auto_prompt: str = None):
        self.bucket_client = bucket_client
        self.event_processor = event_processor
        self.check_interval = check_interval
        self.auto_prompt = auto_prompt or "Analyze security events and take appropriate action based on threat level"
        
        self.is_running = False
        self.monitor_task = None
        self.last_check = None
        self.processed_files = set()
        
        # Callback for processing updates
        self.update_callback: Optional[Callable] = None
    
    def set_update_callback(self, callback: Callable):
        """Set callback function for processing updates"""
        self.update_callback = callback
    
    async def start_monitoring(self):
        """Start monitoring the bucket for new files"""
        if self.is_running:
            logger.warning("Bucket monitor is already running")
            return
        
        self.is_running = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info(f"Started bucket monitoring with {self.check_interval}s interval")
        
        if self.update_callback:
            await self.update_callback({
                "type": "monitor_started",
                "data": {
                    "message": "Bucket monitoring started",
                    "check_interval": self.check_interval
                }
            })
    
    async def stop_monitoring(self):
        """Stop monitoring the bucket"""
        if not self.is_running:
            logger.warning("Bucket monitor is not running")
            return
        
        self.is_running = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped bucket monitoring")
        
        if self.update_callback:
            await self.update_callback({
                "type": "monitor_stopped",
                "data": {"message": "Bucket monitoring stopped"}
            })
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                await self._check_and_process_files()
                self.last_check = datetime.now()
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                logger.info("Bucket monitor cancelled")
                break
            except Exception as e:
                logger.error(f"Error in bucket monitor loop: {str(e)}")
                if self.update_callback:
                    await self.update_callback({
                        "type": "monitor_error",
                        "data": {"error": f"Monitor error: {str(e)}"}
                    })
                
                # Wait before retrying
                await asyncio.sleep(min(self.check_interval, 60))
    
    async def _check_and_process_files(self):
        """Check for new files and process them"""
        try:
            # Get list of unprocessed files
            unprocessed_files = await self.bucket_client.list_unprocessed_files()
            
            if not unprocessed_files:
                logger.debug("No unprocessed files found")
                return
            
            # Filter out files we've already processed in this session
            new_files = [f for f in unprocessed_files if f['etag'] not in self.processed_files]
            
            if not new_files:
                logger.debug("No new files to process")
                return
            
            logger.info(f"Found {len(new_files)} new files to process")
            
            if self.update_callback:
                await self.update_callback({
                    "type": "new_files_detected",
                    "data": {
                        "message": f"Found {len(new_files)} new files",
                        "files": [f['filename'] for f in new_files]
                    }
                })
            
            # Process new files
            for file_info in new_files:
                if not self.is_running:
                    break
                
                try:
                    await self._process_single_file(file_info)
                    # Mark as processed
                    self.processed_files.add(file_info['etag'])
                    
                except Exception as e:
                    logger.error(f"Error processing file {file_info['filename']}: {str(e)}")
                    if self.update_callback:
                        await self.update_callback({
                            "type": "file_processing_error",
                            "data": {
                                "filename": file_info['filename'],
                                "error": str(e)
                            }
                        })
            
        except Exception as e:
            logger.error(f"Error checking for files: {str(e)}")
            raise
    
    async def _process_single_file(self, file_info: Dict[str, Any]):
        """Process a single file from the bucket"""
        filename = file_info['filename']
        file_key = file_info['key']
        
        logger.info(f"Processing file: {filename}")
        
        if self.update_callback:
            await self.update_callback({
                "type": "file_processing_started",
                "data": {
                    "filename": filename,
                    "message": f"Started processing {filename}"
                }
            })
        
        try:
            # Download file to temporary location
            local_path, _ = await self.bucket_client.download_file(file_key)
            
            # Load events from file
            events = self.bucket_client.load_events_from_file(local_path)
            
            if self.update_callback:
                await self.update_callback({
                    "type": "file_events_loaded",
                    "data": {
                        "filename": filename,
                        "event_count": len(events),
                        "message": f"Loaded {len(events)} events from {filename}"
                    }
                })
            
            # Process each event
            file_results = []
            for i, event in enumerate(events):
                if not self.is_running:
                    break
                
                logger.debug(f"Processing event {i+1}/{len(events)} from {filename}")
                
                # Process single event
                result = await self.event_processor.process_event(event, self.auto_prompt)
                file_results.append({
                    'event_index': i + 1,
                    'event_data': event,
                    'processing_result': result
                })
                
                # Send progress update
                if self.update_callback and (i + 1) % 10 == 0:  # Update every 10 events
                    await self.update_callback({
                        "type": "file_processing_progress",
                        "data": {
                            "filename": filename,
                            "progress": i + 1,
                            "total": len(events),
                            "message": f"Processed {i+1}/{len(events)} events from {filename}"
                        }
                    })
            
            # Upload processing results
            processing_summary = {
                'source_file': filename,
                'source_key': file_key,
                'processed_at': datetime.now().isoformat(),
                'total_events': len(events),
                'prompt_used': self.auto_prompt,
                'results': file_results,
                'processed_by': 'bucket_monitor'
            }
            
            results_key = await self.bucket_client.upload_results(file_key, processing_summary)
            
            # Move original file to processed folder
            processed_key = await self.bucket_client.move_to_processed(file_key)
            
            # Clean up temporary file
            await self.bucket_client.cleanup_temp_file(local_path)
            
            logger.info(f"Successfully processed {filename} ({len(events)} events)")
            
            if self.update_callback:
                await self.update_callback({
                    "type": "file_processing_complete",
                    "data": {
                        "filename": filename,
                        "events_processed": len(events),
                        "processed_key": processed_key,
                        "results_key": results_key,
                        "message": f"Successfully processed {filename} with {len(events)} events"
                    }
                })
            
        except Exception as e:
            logger.error(f"Error processing file {filename}: {str(e)}")
            # Try to clean up temp file even on error
            try:
                await self.bucket_client.cleanup_temp_file(local_path)
            except:
                pass
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get current monitor status"""
        return {
            "is_running": self.is_running,
            "check_interval": self.check_interval,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "processed_files_count": len(self.processed_files),
            "auto_prompt": self.auto_prompt
        }