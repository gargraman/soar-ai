
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import csv
import asyncio
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional

from .event_processor import EventProcessor
from .mcp_client import MCPClient
from .kafka_consumer import KafkaEventConsumer
from ..config.settings import AppConfig

class CyberSecurityApp:
    """Main desktop application for cybersecurity event processing"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI Cybersecurity Agent - MCP Client")
        self.root.geometry("1200x800")
        
        self.config = AppConfig()
        self.mcp_client = MCPClient(self.config.mcp_servers)
        self.event_processor = EventProcessor(self.mcp_client)
        self.kafka_consumer = KafkaEventConsumer()
        
        self.audit_logs = []
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Create main notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Event Input Tab
        self.setup_event_input_tab(notebook)
        
        # Results Tab
        self.setup_results_tab(notebook)
        
        # Audit Trail Tab
        self.setup_audit_tab(notebook)
        
        # Configuration Tab
        self.setup_config_tab(notebook)
        
    def setup_event_input_tab(self, parent):
        """Setup event input and processing tab"""
        frame = ttk.Frame(parent)
        parent.add(frame, text="Event Processing")
        
        # File input section
        file_frame = ttk.LabelFrame(frame, text="File Input", padding=10)
        file_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(file_frame, text="Upload JSON/CSV File", 
                  command=self.upload_file).pack(side='left', padx=5)
        
        self.file_label = ttk.Label(file_frame, text="No file selected")
        self.file_label.pack(side='left', padx=10)
        
        # Kafka input section
        kafka_frame = ttk.LabelFrame(frame, text="Kafka Stream", padding=10)
        kafka_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(kafka_frame, text="Topic:").pack(side='left')
        self.kafka_topic = ttk.Entry(kafka_frame, width=30)
        self.kafka_topic.pack(side='left', padx=5)
        self.kafka_topic.insert(0, "security-events")
        
        ttk.Button(kafka_frame, text="Start Kafka Consumer", 
                  command=self.start_kafka_consumer).pack(side='left', padx=5)
        ttk.Button(kafka_frame, text="Stop Kafka Consumer", 
                  command=self.stop_kafka_consumer).pack(side='left', padx=5)
        
        # User prompt section
        prompt_frame = ttk.LabelFrame(frame, text="AI Prompt", padding=10)
        prompt_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        ttk.Label(prompt_frame, text="Enter your cybersecurity analysis prompt:").pack(anchor='w')
        
        self.prompt_text = scrolledtext.ScrolledText(prompt_frame, height=4, width=80)
        self.prompt_text.pack(fill='x', pady=5)
        self.prompt_text.insert('1.0', "Check if this IP is malicious and create a ServiceNow ticket if threat level is high")
        
        # Action buttons
        button_frame = ttk.Frame(prompt_frame)
        button_frame.pack(fill='x', pady=5)
        
        ttk.Button(button_frame, text="Process Events", 
                  command=self.process_events).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Clear Results", 
                  command=self.clear_results).pack(side='left', padx=5)
        
    def setup_results_tab(self, parent):
        """Setup results display tab"""
        frame = ttk.Frame(parent)
        parent.add(frame, text="Results")
        
        # Results display
        self.results_text = scrolledtext.ScrolledText(frame, height=30, width=100)
        self.results_text.pack(fill='both', expand=True, padx=10, pady=10)
        
    def setup_audit_tab(self, parent):
        """Setup audit trail tab"""
        frame = ttk.Frame(parent)
        parent.add(frame, text="Audit Trail")
        
        # Audit log display
        self.audit_text = scrolledtext.ScrolledText(frame, height=25, width=100)
        self.audit_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Export button
        ttk.Button(frame, text="Export Audit Log", 
                  command=self.export_audit_log).pack(pady=5)
        
    def setup_config_tab(self, parent):
        """Setup configuration tab"""
        frame = ttk.Frame(parent)
        parent.add(frame, text="Configuration")
        
        config_text = scrolledtext.ScrolledText(frame, height=25, width=100)
        config_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Display current configuration
        config_json = json.dumps(self.config.to_dict(), indent=2)
        config_text.insert('1.0', config_json)
        
    def upload_file(self):
        """Handle file upload"""
        file_path = filedialog.askopenfilename(
            title="Select Security Events File",
            filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            self.file_label.config(text=f"Selected: {file_path}")
            self.current_file = file_path
            
    def start_kafka_consumer(self):
        """Start Kafka consumer in background thread"""
        topic = self.kafka_topic.get()
        if not topic:
            messagebox.showerror("Error", "Please enter a Kafka topic")
            return
            
        def kafka_thread():
            self.kafka_consumer.start_consuming(topic, self.handle_kafka_event)
            
        threading.Thread(target=kafka_thread, daemon=True).start()
        messagebox.showinfo("Info", f"Started Kafka consumer for topic: {topic}")
        
    def stop_kafka_consumer(self):
        """Stop Kafka consumer"""
        self.kafka_consumer.stop_consuming()
        messagebox.showinfo("Info", "Stopped Kafka consumer")
        
    def handle_kafka_event(self, event_data):
        """Handle incoming Kafka event"""
        self.log_audit(f"Received Kafka event: {event_data}")
        # Process the event asynchronously
        asyncio.run_coroutine_threadsafe(
            self.process_single_event(event_data), 
            asyncio.new_event_loop()
        )
        
    def process_events(self):
        """Process uploaded events with user prompt"""
        prompt = self.prompt_text.get('1.0', tk.END).strip()
        if not prompt:
            messagebox.showerror("Error", "Please enter a prompt")
            return
            
        if not hasattr(self, 'current_file'):
            messagebox.showerror("Error", "Please upload a file first")
            return
            
        # Process in background thread to avoid blocking UI
        threading.Thread(target=self._process_events_async, args=(prompt,), daemon=True).start()
        
    def _process_events_async(self, prompt):
        """Process events asynchronously"""
        try:
            # Load events from file
            events = self.load_events_from_file(self.current_file)
            
            # Process each event
            for i, event in enumerate(events):
                self.log_audit(f"Processing event {i+1}/{len(events)}")
                result = asyncio.run(self.process_single_event(event, prompt))
                self.display_result(f"Event {i+1} Result", result)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process events: {str(e)}")
            
    async def process_single_event(self, event_data, prompt=None, event_format="auto"):
        """Process a single security event"""
        if prompt is None:
            prompt = self.prompt_text.get('1.0', tk.END).strip()
            
        return await self.event_processor.process_event(event_data, prompt, event_format)
        
    def load_events_from_file(self, file_path):
        """Load events from JSON, CSV, or syslog file"""
        events = []
        
        if file_path.endswith('.json'):
            with open(file_path, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    events = data
                else:
                    events = [data]
        elif file_path.endswith('.csv'):
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                events = list(reader)
        elif file_path.endswith('.log') or file_path.endswith('.syslog'):
            # Load syslog file line by line
            with open(file_path, 'r') as f:
                events = [line.strip() for line in f if line.strip()]
        else:
            # Try to auto-detect format
            with open(file_path, 'r') as f:
                content = f.read().strip()
                try:
                    # Try JSON first
                    data = json.loads(content)
                    if isinstance(data, list):
                        events = data
                    else:
                        events = [data]
                except:
                    # Try line-by-line syslog
                    events = [line.strip() for line in content.split('\n') if line.strip()]
                
        return events
        
    def display_result(self, title, result):
        """Display processing result in results tab"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result_text = f"\n{'='*50}\n{title} - {timestamp}\n{'='*50}\n"
        result_text += json.dumps(result, indent=2)
        result_text += "\n"
        
        self.results_text.insert(tk.END, result_text)
        self.results_text.see(tk.END)
        
    def log_audit(self, message):
        """Add entry to audit log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        audit_entry = f"[{timestamp}] {message}"
        self.audit_logs.append(audit_entry)
        
        self.audit_text.insert(tk.END, audit_entry + "\n")
        self.audit_text.see(tk.END)
        
    def clear_results(self):
        """Clear results display"""
        self.results_text.delete('1.0', tk.END)
        
    def export_audit_log(self):
        """Export audit log to file"""
        file_path = filedialog.asksaveasfilename(
            title="Save Audit Log",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            with open(file_path, 'w') as f:
                f.write("\n".join(self.audit_logs))
            messagebox.showinfo("Success", f"Audit log exported to {file_path}")
            
    def run(self):
        """Start the application"""
        self.root.mainloop()
