// Constants
const POLL_INTERVAL = 5000; // 5 seconds
const MAX_POLL_ATTEMPTS = 12; // 1 minute total

// Elements
const tipForm = document.getElementById('tipForm');
const submitBtn = document.getElementById('submitBtn');
const successAlert = document.getElementById('success-alert');
const errorAlert = document.getElementById('error-alert');
const successMessage = document.getElementById('success-message');
const errorMessage = document.getElementById('error-message');
const loadingIndicator = document.getElementById('loading-indicator');
const amountInput = document.getElementById('amount');
const phoneInput = document.getElementById('phoneNumber');
const creatorIdInput = document.getElementById('creatorId');
const tipperNameInput = document.getElementById('tipperName');
const messageInput = document.getElementById('message');

// Handle preset amount buttons
const presetButtons = document.querySelectorAll('.preset-btn');
let selectedPresetButton = null;

presetButtons.forEach(button => {
    button.addEventListener('click', () => {
        const amount = button.dataset.amount;
        
        // Update input value
        if (amountInput) {
            amountInput.value = amount;
        }
        
        // Update button states
        if (selectedPresetButton) {
            selectedPresetButton.classList.remove('selected');
        }
        button.classList.add('selected');
        selectedPresetButton = button;
    });
});

// Clear selected preset when amount is manually changed
if (amountInput) {
    amountInput.addEventListener('input', () => {
        if (selectedPresetButton) {
            selectedPresetButton.classList.remove('selected');
            selectedPresetButton = null;
        }
    });
}

// Socket setup
const socket = io({
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    reconnectionAttempts: 5
});

let socketConnected = false;
let currentTransactionId = null;

socket.on('connect', () => {
    console.log('Socket connected');
    socketConnected = true;
    // Join creator's room
    const creatorId = document.getElementById('creatorId')?.value;
    if (creatorId) {
        console.log('Joining creator room:', creatorId);
        socket.emit('join', { creator_id: creatorId });
    } else {
        console.error('No creator ID found');
    }
});

socket.on('disconnect', () => {
    console.log('Socket disconnected');
    socketConnected = false;
});

socket.on('connect_error', (error) => {
    console.error('Socket connection error:', error);
    socketConnected = false;
});

// --- UI Helper Functions ---

function setSubmitButtonState(isDisabled, text = 'Send Tip') {
    if (submitBtn) {
        submitBtn.disabled = isDisabled;
        // Use innerHTML to allow for spinner icon
        submitBtn.innerHTML = isDisabled ? '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...' : text;
    }
}

function showLoading(isLoading) {
    if (loadingIndicator) {
        loadingIndicator.style.display = isLoading ? 'block' : 'none';
    }
}

function displayMessage(type, message) {
    hideAlerts(); // Hide previous alerts first
    
    if (!message) {
        console.error('No message provided to displayMessage');
        return;
    }

    if (type === 'success' && successAlert) {
        // Format message as pre-formatted text if it contains newlines
        // or if it looks like an M-Pesa receipt
        if (message.includes('\n') || message.includes('M-PESA')) {
            successMessage.innerHTML = `<pre class="mb-0 text-success" style="font-family: monospace; white-space: pre-wrap; word-wrap: break-word;">${message}</pre>`;
        } else {
            successMessage.textContent = message;
        }
        successAlert.style.display = 'block';
        // Scroll the alert into view
        successAlert.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } else if (type === 'error' && errorAlert) {
        errorMessage.textContent = message;
        errorAlert.style.display = 'block';
        // Scroll the alert into view
        errorAlert.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

function hideAlerts() {
    if (successAlert) successAlert.style.display = 'none';
    if (errorAlert) errorAlert.style.display = 'none';
}

function resetForm() {
    if (tipForm) {
        tipForm.reset();
    }
    setSubmitButtonState(false);
    currentTransactionId = null;
    hideAlerts();
    showLoading(false);
}

// --- Form Handling ---

function getFormData() {
    return {
        creator_id: creatorIdInput?.value,
        amount: amountInput?.value,
        phone_number: phoneInput?.value,
        tipper_name: tipperNameInput?.value || 'Anonymous',
        message: messageInput?.value || ''
    };
}

function validateInput(formData) {
    // Validate phone number format
    if (!formData.phone_number || !formData.phone_number.match(/^254[0-9]{9}$/)) {
        displayMessage('error', 'Please enter a valid phone number in the format: 254XXXXXXXXX');
        return false;
    }

    // Validate amount
    const amountValue = parseFloat(formData.amount);
    if (isNaN(amountValue) || amountValue < 1) {
        displayMessage('error', 'Please enter a valid amount (minimum 1 KES)');
        return false;
    }
    return true;
}

async function handleFormSubmit(event) {
    event.preventDefault();
    hideAlerts();
    console.log('Form submitted');

    const formData = getFormData();
    console.log('Form data:', formData);

    if (!validateInput(formData)) {
        console.log('Form validation failed');
        return; // Stop if validation fails
    }

    setSubmitButtonState(true);
    showLoading(true);

    try {
        console.log('Initiating payment...');
        const response = await fetch('/payments/initiate_tip', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();
        console.log('Payment initiation response:', data);

        if (response.ok && data.status === 'success') {
            currentTransactionId = data.transaction_id;
            console.log('Transaction ID set:', currentTransactionId);

            if (data.test_mode) {
                console.log('Test mode response received');
                // Test mode - show immediate success with receipt
                const receipt = `
M-PESA
Transaction ID: ${data.mpesa_receipt}
Amount: KES ${data.amount}
Phone: ${data.phone_number || 'XXXXXXXXX'}
Time: ${data.timestamp}
Paid to: StreamTip Creator
Status: Completed

Thank you for using M-PESA
                `.trim();
                displayMessage('success', receipt);
                showLoading(false);
                resetForm(); // Resets button state as well
            } else {
                console.log('Starting payment polling...');
                // Real payment - show pending message and start polling
                displayMessage('success', 'Please check your phone for the M-Pesa prompt.');
                // Keep loading indicator until polling finishes or fails
                pollTransactionStatus(data.transaction_id);
            }
        } else {
            // Handle API errors (e.g., 4xx, 5xx responses or {status: 'error'})
            const errorMsg = data.message || 'Payment initiation failed. Please try again.';
            console.error('Payment initiation failed:', errorMsg);
            displayMessage('error', errorMsg);
            showLoading(false);
            setSubmitButtonState(false);
        }

    } catch (error) {
        console.error('Network or unexpected error initiating tip:', error);
        displayMessage('error', 'Network error. Please check your connection and try again.');
        showLoading(false);
        setSubmitButtonState(false);
    }
}

// --- Payment Status Handling ---

async function pollTransactionStatus(transactionId, attempt = 0) {
    console.log(`Polling attempt ${attempt + 1}/${MAX_POLL_ATTEMPTS} for transaction ${transactionId}`);
    
    if (attempt >= MAX_POLL_ATTEMPTS) {
        console.log('Max polling attempts reached');
        displayMessage('error', 'Payment taking longer than expected. Please check M-Pesa or try again later.');
        showLoading(false);
        setSubmitButtonState(false);
        currentTransactionId = null; // Stop polling
        return;
    }

    try {
        console.log('Checking transaction status...');
        const response = await fetch(`/payments/check_status/${transactionId}`);
        const data = await response.json();
        console.log('Status check response:', data);

        if (response.ok && data.status === 'success') {
            // If we have a completed status with receipt, show it immediately
            if (data.transaction_status === 'completed' && data.mpesa_receipt) {
                const receipt = `
M-PESA
Transaction ID: ${data.mpesa_receipt}
Amount: KES ${data.amount}
Phone: ${data.phone_number || 'XXXXXXXXX'}
Time: ${data.timestamp || new Date().toLocaleString()}
Paid to: StreamTip Creator
Status: Completed

Thank you for using M-PESA
                `.trim();
                displayMessage('success', receipt);
                showLoading(false);
                resetForm();
                currentTransactionId = null;
                return;
            }

            // For other statuses, pass to handler
            const transactionData = {
                id: transactionId,
                status: data.transaction_status,
                mpesa_receipt: data.mpesa_receipt,
                amount: data.amount,
                phone_number: data.phone_number,
                timestamp: data.timestamp
            };
            console.log('Processing transaction data:', transactionData);
            handlePaymentStatus(data.transaction_status, transactionData);

            // If still pending, schedule next poll
            if (data.transaction_status === 'pending') {
                console.log(`Transaction still pending, scheduling next poll in ${POLL_INTERVAL}ms`);
                setTimeout(() => {
                    // Ensure we are still polling the same transaction
                    if (transactionId === currentTransactionId) {
                        pollTransactionStatus(transactionId, attempt + 1);
                    } else {
                        console.log('Transaction ID changed, stopping poll');
                    }
                }, POLL_INTERVAL);
            } else {
                console.log('Final status received, clearing transaction ID');
                currentTransactionId = null; // Clear on final status
            }
        } else {
            // Error checking status (API error)
            const errorMsg = data.message || 'Could not check payment status.';
            console.error('Status check failed:', errorMsg);
            displayMessage('error', errorMsg);
            showLoading(false);
            setSubmitButtonState(false);
            currentTransactionId = null; // Stop polling
        }

    } catch (error) {
        console.error('Network error checking payment status:', error);
        displayMessage('error', 'Network error checking status. Please wait or try again later.');
        showLoading(false);
        setSubmitButtonState(false);
        currentTransactionId = null; // Stop polling
    }
}

// Handles final status updates from polling or WebSockets
function handlePaymentStatus(status, data = {}) {
    console.log('Handling final payment status:', status, data);
    switch (status) {
        case 'completed':
            if (data.mpesa_receipt) {
                const receipt = `
M-PESA
Transaction ID: ${data.mpesa_receipt}
Amount: KES ${data.amount}
Phone: ${data.phone_number || 'XXXXXXXXX'}
Time: ${data.timestamp || new Date().toLocaleString()}
Paid to: StreamTip Creator
Status: Completed

Thank you for using M-PESA
                `.trim();
                displayMessage('success', receipt);
                showLoading(false);
                resetForm();
            } else {
                displayMessage('success', 'Payment completed successfully!');
                showLoading(false);
                resetForm();
            }
            break;
        case 'failed':
            displayMessage('error', data.message || 'Payment failed. Please try again.');
            showLoading(false);
            setSubmitButtonState(false);
            currentTransactionId = null;
            break;
        case 'timeout':
            displayMessage('error', 'Payment request timed out. Please try again.');
            showLoading(false);
            setSubmitButtonState(false);
            currentTransactionId = null;
            break;
        case 'pending':
            // Keep the pending message and loading state
            console.log('Payment still pending...', data);
            break;
        default:
            displayMessage('error', 'Unknown payment status received. Please contact support.');
            showLoading(false);
            setSubmitButtonState(false);
            currentTransactionId = null;
            break;
    }
}

// --- Socket.IO Event Handlers ---

// Listen for status updates pushed from the server
socket.on('tip_status', function(data) {
    console.log('Socket: Tip status update received:', data);
    
    // Always handle the status update if we have a matching transaction
    if (data.id === currentTransactionId) {
        // For completed status, ensure we have all receipt data
        if (data.status === 'completed' && data.mpesa_receipt) {
            const receipt = `
M-PESA
Transaction ID: ${data.mpesa_receipt}
Amount: KES ${data.amount}
Phone: ${data.phone_number || 'XXXXXXXXX'}
Time: ${data.timestamp || new Date().toLocaleString()}
Paid to: StreamTip Creator
Status: Completed

Thank you for using M-PESA
            `.trim();
            displayMessage('success', receipt);
            showLoading(false);
            resetForm();
            currentTransactionId = null;
        } else {
            // For other statuses, use standard handler
            handlePaymentStatus(data.status, data);
            if (data.status !== 'pending') {
                currentTransactionId = null;
            }
        }
    }
});

// Handle new_tip event for immediate confirmation
socket.on('new_tip', (data) => {
    console.log('Socket: New tip received:', data);
    // If we have a current transaction and receive a new_tip event,
    // treat it as a successful completion
    if (currentTransactionId) {
        const receipt = `
M-PESA
Transaction ID: ${data.mpesa_receipt}
Amount: KES ${data.amount}
Phone: ${data.phone_number || 'XXXXXXXXX'}
Time: ${data.timestamp}
Paid to: StreamTip Creator
Status: Completed

Thank you for using M-PESA
        `.trim();
        displayMessage('success', receipt);
        showLoading(false);
        resetForm();
        currentTransactionId = null;
    }
});

// --- Initialization ---

// Add the main event listener
if (tipForm) {
    tipForm.addEventListener('submit', handleFormSubmit);
} else {
    console.error("Tip form not found on page.");
} 