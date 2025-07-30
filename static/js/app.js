/**
 * JavaScript for AI Cybersecurity Agent Web Interface
 */

class CyberSecurityApp {
    constructor() {
        this.currentFile = null;
        this.ws = null;
        this.processingActive = false;
        
        this.initializeElements();
        this.setupEventListeners();
        this.connectWebSocket();
        this.loadAuditLogs();
    }

    initializeElements() {
        // Get DOM elements
        this.fileInput = document.getElementById('fileInput');
        this.promptInput = document.getElementById('promptInput');
        this.processBtn = document.getElementById('processBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.kafkaTopicInput = document.getElementById('kafkaTopicInput');
        this.startKafkaBtn = document.getElementById('startKafkaBtn');
        this.stopKafkaBtn = document.getElementById('stopKafkaBtn');
        this.exportResultsBtn = document.getElementById('exportResultsBtn');
        this.exportAuditBtn = document.getElementById('exportAuditBtn');
        
        this.statusIndicator = document.getElementById('status-indicator');
        this.progressCard = document.getElementById('progressCard');
        this.progressBar = document.getElementById('progressBar');
        this.progressText = document.getElementById('progressText');
        this.progressCounter = document.getElementById('progressCounter');
        
        this.resultsContainer = document.getElementById('resultsContainer');
        this.auditContainer = document.getElementById('auditContainer');
        
        this.notificationToast = new bootstrap.Toast(document.getElementById('notificationToast'));
        this.toastBody = document.getElementById('toastBody');
    }

    setupEventListeners() {
        // File upload
        this.fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
        
        // Processing
        this.processBtn.addEventListener('click', () => this.processEvents());
        this.clearBtn.addEventListener('click', () => this.clearResults());
        
        // Kafka controls
        this.startKafkaBtn.addEventListener('click', () => this.startKafkaConsumer());
        this.stopKafkaBtn.addEventListener('click', () => this.stopKafkaConsumer());
        
        // Export buttons
        this.exportResultsBtn.addEventListener('click', () => this.exportResults());
        this.exportAuditBtn.addEventListener('click', () => this.exportAuditLogs());
        
        // Auto-refresh audit logs every 30 seconds
        setInterval(() => this.loadAuditLogs(), 30000);
    }

    async handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        this.updateStatus('processing', 'Uploading file...');
        
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Upload failed');
            }

            const result = await response.json();
            this.currentFile = result.upload_path;
            this.processBtn.disabled = false;
            
            this.showNotification('success', `File uploaded: ${result.filename} (${result.event_count} events)`);
            this.updateStatus('ready', `Ready - ${result.event_count} events loaded`);
            
        } catch (error) {
            this.showNotification('error', `Upload failed: ${error.message}`);
            this.updateStatus('error', 'Upload failed');
            this.processBtn.disabled = true;
        }
    }

    async processEvents() {
        if (!this.currentFile || !this.promptInput.value.trim()) {
            this.showNotification('warning', 'Please upload a file and enter a prompt');
            return;
        }

        this.processingActive = true;
        this.processBtn.disabled = true;
        this.updateStatus('processing', 'Processing events...');
        this.showProgressCard(true);

        const formData = new FormData();
        formData.append('file_path', this.currentFile);
        formData.append('prompt', this.promptInput.value.trim());

        try {
            const response = await fetch('/api/process', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Processing failed');
            }

            const result = await response.json();
            this.showNotification('info', result.message);
            
        } catch (error) {
            this.showNotification('error', `Processing failed: ${error.message}`);
            this.updateStatus('error', 'Processing failed');
            this.processingActive = false;
            this.processBtn.disabled = false;
            this.showProgressCard(false);
        }
    }

    async startKafkaConsumer() {
        const topic = this.kafkaTopicInput.value.trim();
        if (!topic) {
            this.showNotification('warning', 'Please enter a Kafka topic');
            return;
        }

        this.startKafkaBtn.disabled = true;

        const formData = new FormData();
        formData.append('topic', topic);

        try {
            const response = await fetch('/api/kafka/start', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to start Kafka consumer');
            }

            const result = await response.json();
            this.showNotification('success', `Kafka consumer started for topic: ${result.topic}`);
            this.stopKafkaBtn.disabled = false;
            
        } catch (error) {
            this.showNotification('error', `Kafka start failed: ${error.message}`);
            this.startKafkaBtn.disabled = false;
        }
    }

    async stopKafkaConsumer() {
        this.stopKafkaBtn.disabled = true;

        try {
            const response = await fetch('/api/kafka/stop', {
                method: 'POST'
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to stop Kafka consumer');
            }

            this.showNotification('success', 'Kafka consumer stopped');
            this.startKafkaBtn.disabled = false;
            
        } catch (error) {
            this.showNotification('error', `Kafka stop failed: ${error.message}`);
        }
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
        };
        
        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleWebSocketMessage(message);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected, attempting to reconnect...');
            setTimeout(() => this.connectWebSocket(), 5000);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    handleWebSocketMessage(message) {
        switch (message.type) {
            case 'processing_update':
                this.updateProcessingProgress(message.data);
                break;
            case 'processing_complete':
                this.handleProcessingComplete(message.data);
                break;
            case 'kafka_event':
                this.handleKafkaEvent(message.data);
                break;
            case 'error':
                this.handleProcessingError(message.data);
                break;
        }
    }

    updateProcessingProgress(data) {
        const { progress, total, result } = data;
        const percentage = Math.round((progress / total) * 100);
        
        this.progressBar.style.width = `${percentage}%`;
        this.progressBar.textContent = `${percentage}%`;
        this.progressCounter.textContent = `${progress}/${total}`;
        this.progressText.textContent = `Processing event ${progress} of ${total}`;
        
        if (result) {
            this.addResult(result, `Event ${progress}`);
        }
    }

    handleProcessingComplete(data) {
        this.processingActive = false;
        this.processBtn.disabled = false;
        this.showProgressCard(false);
        this.updateStatus('complete', 'Processing complete');
        
        this.showNotification('success', `Processing completed successfully! ${data.results.length} events processed.`);
        this.loadAuditLogs(); // Refresh audit logs
    }

    handleKafkaEvent(data) {
        this.addResult(data, 'Kafka Event');
        this.showNotification('info', 'New Kafka event processed');
    }

    handleProcessingError(data) {
        this.processingActive = false;
        this.processBtn.disabled = false;
        this.showProgressCard(false);
        this.updateStatus('error', `Error: ${data.error}`);
        
        this.showNotification('error', `Processing error: ${data.error}`);
    }

    addResult(result, title) {
        const timestamp = new Date().toLocaleString();
        const severity = this.detectSeverity(result);
        
        const resultElement = document.createElement('div');
        resultElement.className = `result-item ${severity}`;
        resultElement.innerHTML = `
            <div class="result-header">
                ${title} - ${timestamp}
                <button class="btn btn-sm btn-outline-secondary float-end" onclick="this.parentElement.nextElementSibling.querySelector('.result-json').style.display = 
                this.parentElement.nextElementSibling.querySelector('.result-json').style.display === 'none' ? 'block' : 'none'">
                    <i class="fas fa-eye"></i> Toggle Details
                </button>
            </div>
            <div class="result-content">
                <div class="mb-2">
                    <strong>Event ID:</strong> ${result.event_id || 'N/A'}<br>
                    <strong>Status:</strong> <span class="badge bg-primary">${result.analysis?.status || 'processed'}</span><br>
                    <strong>Actions:</strong> ${result.analysis?.selected_servers?.join(', ') || 'N/A'}
                </div>
                <div class="result-json" style="display: none;">
                    ${this.formatJSON(result)}
                </div>
            </div>
        `;
        
        // Clear placeholder if it exists
        const placeholder = this.resultsContainer.querySelector('.text-muted');
        if (placeholder) {
            placeholder.remove();
        }
        
        this.resultsContainer.appendChild(resultElement);
        resultElement.scrollIntoView({ behavior: 'smooth' });
    }

    detectSeverity(result) {
        const analysisText = JSON.stringify(result).toLowerCase();
        if (analysisText.includes('critical')) return 'severity-critical';
        if (analysisText.includes('high')) return 'severity-high';
        if (analysisText.includes('medium')) return 'severity-medium';
        return 'severity-low';
    }

    formatJSON(obj) {
        return JSON.stringify(obj, null, 2)
            .replace(/("([^"]+)":)/g, '<span class="json-key">$1</span>')
            .replace(/: "([^"]+)"/g, ': <span class="json-string">"$1"</span>')
            .replace(/: (\d+)/g, ': <span class="json-number">$1</span>')
            .replace(/: (true|false)/g, ': <span class="json-boolean">$1</span>')
            .replace(/: null/g, ': <span class="json-null">null</span>');
    }

    async loadAuditLogs() {
        try {
            const response = await fetch('/api/audit');
            if (!response.ok) return;

            const data = await response.json();
            this.displayAuditLogs(data.logs);
            
        } catch (error) {
            console.error('Failed to load audit logs:', error);
        }
    }

    displayAuditLogs(logs) {
        if (!logs || logs.length === 0) return;

        // Clear placeholder if it exists
        const placeholder = this.auditContainer.querySelector('.text-muted');
        if (placeholder) {
            placeholder.remove();
        }

        this.auditContainer.innerHTML = '';
        
        const logElement = document.createElement('div');
        logElement.className = 'audit-log';
        logElement.innerHTML = logs.map(log => 
            `<div class="audit-entry">${this.escapeHtml(log)}</div>`
        ).join('');
        
        this.auditContainer.appendChild(logElement);
        this.auditContainer.scrollTop = this.auditContainer.scrollHeight;
    }

    clearResults() {
        this.resultsContainer.innerHTML = `
            <div class="text-muted text-center py-5">
                <i class="fas fa-file-alt fa-3x mb-3"></i>
                <p>No results yet. Upload a file and process events to see results here.</p>
            </div>
        `;
        this.showNotification('info', 'Results cleared');
    }

    showProgressCard(show) {
        this.progressCard.style.display = show ? 'block' : 'none';
        if (!show) {
            this.progressBar.style.width = '0%';
            this.progressBar.textContent = '';
            this.progressCounter.textContent = '0/0';
            this.progressText.textContent = 'Processing...';
        }
    }

    updateStatus(type, message) {
        const icon = this.statusIndicator.querySelector('i');
        const text = this.statusIndicator.childNodes[1];
        
        // Remove existing classes
        icon.className = 'fas fa-circle';
        
        switch (type) {
            case 'ready':
                icon.classList.add('text-success');
                break;
            case 'processing':
                icon.classList.add('text-warning');
                break;
            case 'error':
                icon.classList.add('text-danger');
                break;
            case 'complete':
                icon.classList.add('text-info');
                break;
        }
        
        text.textContent = ` ${message}`;
    }

    showNotification(type, message) {
        let bgClass = 'bg-primary';
        let icon = 'fas fa-info-circle';
        
        switch (type) {
            case 'success':
                bgClass = 'bg-success';
                icon = 'fas fa-check-circle';
                break;
            case 'error':
                bgClass = 'bg-danger';
                icon = 'fas fa-exclamation-circle';
                break;
            case 'warning':
                bgClass = 'bg-warning';
                icon = 'fas fa-exclamation-triangle';
                break;
        }
        
        this.toastBody.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="${icon} me-2"></i>
                <span>${message}</span>
            </div>
        `;
        
        const toastElement = document.getElementById('notificationToast');
        toastElement.className = `toast ${bgClass} text-white`;
        
        this.notificationToast.show();
    }

    async exportResults() {
        // Export current results as JSON
        const results = Array.from(this.resultsContainer.querySelectorAll('.result-item'));
        if (results.length === 0) {
            this.showNotification('warning', 'No results to export');
            return;
        }

        const exportData = {
            timestamp: new Date().toISOString(),
            results_count: results.length,
            results: results.map((item, index) => ({
                id: index + 1,
                title: item.querySelector('.result-header').textContent.split(' - ')[0],
                timestamp: item.querySelector('.result-header').textContent.split(' - ')[1],
                // Extract JSON data would require more complex parsing
                summary: item.querySelector('.result-content').textContent.trim()
            }))
        };

        this.downloadJSON(exportData, 'cybersecurity_results');
    }

    async exportAuditLogs() {
        try {
            const response = await fetch('/api/results/export');
            if (!response.ok) {
                throw new Error('Export failed');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `audit_log_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
            a.click();
            window.URL.revokeObjectURL(url);

            this.showNotification('success', 'Audit log exported successfully');
            
        } catch (error) {
            this.showNotification('error', `Export failed: ${error.message}`);
        }
    }

    downloadJSON(data, filename) {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${filename}_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
        a.click();
        window.URL.revokeObjectURL(url);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new CyberSecurityApp();
});