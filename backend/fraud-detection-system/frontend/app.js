class FraudDetectionUI {
    constructor() {
        this.ws = null;
        this.transactions = [];
        this.currentFilter = 'all';
        this.stats = {
            total_transactions: 0,
            safe_transactions: 0,
            suspicious_transactions: 0,
            fraud_transactions: 0,
            total_amount_processed: 0
        };
        this.isConnected = false;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.connectWebSocket();
        this.setupFilterButtons();
    }
    
    setupEventListeners() {
        // Form submission
        document.getElementById('transactionForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.analyzeTransaction();
        });
        
        // Window events
        window.addEventListener('beforeunload', () => {
            if (this.ws) {
                this.ws.close();
            }
        });
        
        // Auto-reconnect on visibility change
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && !this.isConnected) {
                this.connectWebSocket();
            }
        });
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.hostname}:8000/ws`;
        
        console.log('🔌 Connecting to WebSocket:', wsUrl);
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('✅ WebSocket connected');
            this.isConnected = true;
            this.updateConnectionStatus(true);
            this.clearNoTransactionsMessage();
        };
        
        this.ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                this.handleWebSocketMessage(message);
            } catch (error) {
                console.error('❌ Error parsing WebSocket message:', error);
            }
        };
        
        this.ws.onclose = (event) => {
            console.log('🔌 WebSocket closed:', event.code, event.reason);
            this.isConnected = false;
            this.updateConnectionStatus(false);
            
            // Auto-reconnect after 3 seconds
            setTimeout(() => {
                if (!this.isConnected) {
                    this.connectWebSocket();
                }
            }, 3000);
        };
        
        this.ws.onerror = (error) => {
            console.error('❌ WebSocket error:', error);
            this.updateConnectionStatus(false);
        };
    }
    
    handleWebSocketMessage(message) {
        switch (message.type) {
            case 'stats_update':
                this.updateStats(message.data);
                break;
            case 'realtime_transaction':
                this.addTransaction(message.data, true);
                break;
            case 'new_transaction':
                this.addTransaction(message.data, false);
                break;
            default:
                console.log('🔔 Unknown message type:', message.type);
        }
    }
    
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connectionStatus');
        const indicator = statusElement.querySelector('.status-indicator');
        const text = statusElement.querySelector('span:last-child');
        
        if (connected) {
            indicator.className = 'status-indicator online';
            text.textContent = 'Connected to ML Backend';
            statusElement.style.background = 'rgba(39, 174, 96, 0.1)';
        } else {
            indicator.className = 'status-indicator offline';
            text.textContent = 'Reconnecting to ML Backend...';
            statusElement.style.background = 'rgba(231, 76, 60, 0.1)';
        }
    }
    
    async analyzeTransaction() {
        const form = document.getElementById('transactionForm');
        const button = form.querySelector('.btn');
        const buttonText = button.querySelector('.btn-text');
        const spinner = button.querySelector('.btn-spinner');
        
        // Show loading state
        button.disabled = true;
        buttonText.style.display = 'none';
        spinner.style.display = 'block';
        
        try {
            const formData = {
                amount: parseFloat(document.getElementById('amount').value),
                merchant_type: document.getElementById('merchant').value,
                location: document.getElementById('location').value,
                time_of_day: document.getElementById('timeOfDay').value,
                card_type: document.getElementById('cardType').value
            };
            
            const response = await fetch('http://localhost:8000/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            // The WebSocket will handle adding the transaction to the UI
            // Just show the alert here
            this.showAlert(result);
            
            // Reset form
            form.reset();
            
        } catch (error) {
            console.error('❌ Error analyzing transaction:', error);
            this.showAlert({
                status: 'error',
                fraud_probability: 0,
                message: 'Failed to analyze transaction. Please try again.'
            });
        } finally {
            // Reset button state
            button.disabled = false;
            buttonText.style.display = 'block';
            spinner.style.display = 'none';
        }
    }
    
    addTransaction(transaction, isRealTime = false) {
        // Add to transactions array
        this.transactions.unshift(transaction);
        
        // Keep only latest 100 transactions
        if (this.transactions.length > 100) {
            this.transactions = this.transactions.slice(0, 100);
        }
        
        // Create and add transaction element
        const element = this.createTransactionElement(transaction, isRealTime);
        const container = document.getElementById('transactionList');
        
        // Remove no-transactions message if present
        this.clearNoTransactionsMessage();
        
        // Add the new transaction at the top
        container.insertBefore(element, container.firstChild);
        
        // Remove excess transactions from DOM
        while (container.children.length > 50) {
            container.removeChild(container.lastChild);
        }
        
        // Apply current filter
        this.applyFilter();
        
        // Show alert for manual transactions
        if (!isRealTime) {
            this.showAlert(transaction);
        }
    }
    
    createTransactionElement(transaction, isRealTime = false) {
        const div = document.createElement('div');
        div.className = `transaction-item ${transaction.status}`;
        if (isRealTime) div.classList.add('new');
        
        const riskClass = transaction.fraud_probability >= 0.8 ? 'risk-high' : 
                         transaction.fraud_probability >= 0.5 ? 'risk-medium' : 'risk-low';
        
        const timestamp = new Date(transaction.timestamp).toLocaleString();
        const amount = typeof transaction.amount === 'number' ? transaction.amount.toFixed(2) : transaction.amount;
        
        div.innerHTML = `
            <div class="transaction-header">
                <span class="transaction-id">${transaction.transaction_id}</span>
                <span class="risk-score ${riskClass}">
                    ${(transaction.fraud_probability * 100).toFixed(1)}% Risk
                </span>
            </div>
            <div class="transaction-details">
                <div class="transaction-detail">
                    <span class="detail-label">Amount</span>
                    <span class="detail-value">$${amount}</span>
                </div>
                <div class="transaction-detail">
                    <span class="detail-label">Merchant</span>
                    <span class="detail-value">${transaction.merchant_type || 'N/A'}</span>
                </div>
                <div class="transaction-detail">
                    <span class="detail-label">Location</span>
                    <span class="detail-value">${transaction.location || 'N/A'}</span>
                </div>
                <div class="transaction-detail">
                    <span class="detail-label">Time</span>
                    <span class="detail-value">${transaction.time_of_day || 'N/A'}</span>
                </div>
                <div class="transaction-detail">
                    <span class="detail-label">Card Type</span>
                    <span class="detail-value">${transaction.card_type || 'N/A'}</span>
                </div>
                <div class="transaction-detail">
                    <span class="detail-label">Status</span>
                    <span class="detail-value status-${transaction.status}">${transaction.status.toUpperCase()}</span>
                </div>
            </div>
            <div class="ml-info">
                <div><strong>ML Confidence:</strong> ${((transaction.ml_confidence || 0) * 100).toFixed(1)}%</div>
                <div><strong>Risk Score:</strong> ${((transaction.risk_score || 0) * 100).toFixed(1)}%</div>
                <div><strong>Timestamp:</strong> ${timestamp}</div>
            </div>
        `;
        
        return div;
    }
    
    setupFilterButtons() {
        const filterButtons = document.querySelectorAll('.filter-btn');
        filterButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                // Remove active class from all buttons
                filterButtons.forEach(btn => btn.classList.remove('active'));
                
                // Add active class to clicked button
                e.target.classList.add('active');
                
                // Update current filter
                this.currentFilter = e.target.dataset.filter;
                
                // Apply filter
                this.applyFilter();
            });
        });
    }
    
    applyFilter() {
        const transactionItems = document.querySelectorAll('.transaction-item');
        
        transactionItems.forEach(item => {
            if (this.currentFilter === 'all') {
                item.style.display = 'block';
            } else {
                const hasClass = item.classList.contains(this.currentFilter);
                item.style.display = hasClass ? 'block' : 'none';
            }
        });
    }
    
    updateStats(stats) {
        this.stats = stats;
        
        document.getElementById('safeCount').textContent = stats.safe_transactions.toLocaleString();
        document.getElementById('suspiciousCount').textContent = stats.suspicious_transactions.toLocaleString();
        document.getElementById('fraudCount').textContent = stats.fraud_transactions.toLocaleString();
        
        const totalAmount = stats.total_amount_processed;
        let displayAmount;
        if (totalAmount >= 1000000) {
            displayAmount = `$${(totalAmount / 1000000).toFixed(1)}M`;
        } else if (totalAmount >= 1000) {
            displayAmount = `$${(totalAmount / 1000).toFixed(1)}K`;
        } else {
            displayAmount = `$${totalAmount.toFixed(0)}`;
        }
        
        document.getElementById('totalAmount').textContent = displayAmount;
        
        // Update model metrics if provided
        if (stats.model_accuracy) {
            document.getElementById('modelAccuracy').textContent = `${(stats.model_accuracy * 100).toFixed(1)}%`;
        }
        if (stats.model_precision) {
            document.getElementById('modelPrecision').textContent = `${(stats.model_precision * 100).toFixed(1)}%`;
        }
        if (stats.model_recall) {
            document.getElementById('modelRecall').textContent = `${(stats.model_recall * 100).toFixed(1)}%`;
        }
    }
    
    showAlert(transaction) {
        const alert = document.getElementById('alert');
        let alertClass, message;
        
        if (transaction.status === 'error') {
            alertClass = 'danger';
            message = `❌ ERROR: ${transaction.message}`;
        } else {
            switch (transaction.status) {
                case 'fraud':
                    alertClass = 'danger';
                    message = `🚨 FRAUD DETECTED: High-risk transaction! ML Confidence: ${(transaction.fraud_probability * 100).toFixed(1)}%`;
                    break;
                case 'suspicious':
                    alertClass = 'warning';
                    message = `⚠️ SUSPICIOUS: Transaction flagged for review. ML Confidence: ${(transaction.fraud_probability * 100).toFixed(1)}%`;
                    break;
                default:
                    alertClass = 'success';
                    message = `✅ SAFE: Transaction approved by ML model. Risk Score: ${(transaction.fraud_probability * 100).toFixed(1)}%`;
            }
        }
        
        alert.className = `alert ${alertClass}`;
        alert.textContent = message;
        alert.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            alert.style.display = 'none';
        }, 5000);
    }
    
    clearNoTransactionsMessage() {
        const container = document.getElementById('transactionList');
        const noTransactions = container.querySelector('.no-transactions');
        if (noTransactions) {
            noTransactions.remove();
        }
    }
}

// Quick test functions
function quickTest(type) {
    const testData = {
        safe: {
            amount: 45.67,
            merchant: 'grocery',
            location: 'New York, NY',
            timeOfDay: 'afternoon',
            cardType: 'debit'
        },
        suspicious: {
            amount: 2500.00,
            merchant: 'online',
            location: 'Unknown Location',
            timeOfDay: 'night',
            cardType: 'credit'
        },
        fraud: {
            amount: 9999.99,
            merchant: 'unknown',
            location: 'Foreign Country',
            timeOfDay: 'night',
            cardType: 'prepaid'
        }
    };
    
    const data = testData[type];
    if (data) {
        document.getElementById('amount').value = data.amount;
        document.getElementById('merchant').value = data.merchant;
        document.getElementById('location').value = data.location;
        document.getElementById('timeOfDay').value = data.timeOfDay;
        document.getElementById('cardType').value = data.cardType;
        
        // Trigger form submission
        document.getElementById('transactionForm').dispatchEvent(new Event('submit'));
    }
}

function clearTransactions() {
    const container = document.getElementById('transactionList');
    container.innerHTML = '<div class="no-transactions"><p>No transactions to display</p></div>';
    
    if (window.fraudUI) {
        window.fraudUI.transactions = [];
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initializing Fraud Detection UI...');
    window.fraudUI = new FraudDetectionUI();
});

// Handle connection errors gracefully
window.addEventListener('online', () => {
    console.log('🌐 Internet connection restored');
    if (window.fraudUI && !window.fraudUI.isConnected) {
        window.fraudUI.connectWebSocket();
    }
});

window.addEventListener('offline', () => {
    console.log('🌐 Internet connection lost');
});