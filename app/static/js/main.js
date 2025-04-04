document.addEventListener('DOMContentLoaded', () => {
    // Card hover effect with error handling
    const heroCards = document.querySelector('.hero-cards');
    if (heroCards) {
        const cards = document.querySelectorAll('.card');
        
        heroCards.addEventListener('mousemove', (e) => {
            try {
                const rect = heroCards.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                cards.forEach((card, index) => {
                    const rotateY = (x / rect.width - 0.5) * 20;
                    const rotateX = (y / rect.height - 0.5) * -20;
                    const translateZ = index * -50;
                    
                    requestAnimationFrame(() => {
                        card.style.transform = `
                            translateZ(${translateZ}px)
                            rotateY(${rotateY}deg)
                            rotateX(${rotateX}deg)
                            translateX(${index * -50}px)
                        `;
                    });
                });
            } catch (error) {
                console.error('Error in card hover effect:', error);
            }
        });
        
        heroCards.addEventListener('mouseleave', () => {
            try {
                cards.forEach((card, index) => {
                    requestAnimationFrame(() => {
                        card.style.transform = `
                            translateZ(${index * -50}px)
                            rotateY(-15deg)
                            translateX(${index * -50}px)
                        `;
                    });
                });
            } catch (error) {
                console.error('Error in card reset:', error);
            }
        });
    }

    // Clipboard functionality with loading states and error handling
    const copyButtons = document.querySelectorAll('.copy-btn');
    copyButtons.forEach(button => {
        button.addEventListener('click', async function() {
            const input = this.previousElementSibling;
            if (!input) return;

            try {
                this.classList.add('loading');
                await navigator.clipboard.writeText(input.value);
                
                const toast = new bootstrap.Toast(document.getElementById('copyToast'));
                toast.show();
                
                // Visual feedback
                this.classList.remove('btn-outline-primary');
                this.classList.add('btn-success');
                setTimeout(() => {
                    this.classList.remove('btn-success');
                    this.classList.add('btn-outline-primary');
                }, 1500);
            } catch (error) {
                console.error('Failed to copy:', error);
                const errorToast = document.getElementById('errorToast');
                if (errorToast) {
                    errorToast.querySelector('.toast-body').textContent = 'Failed to copy to clipboard';
                    new bootstrap.Toast(errorToast).show();
                }
            } finally {
                this.classList.remove('loading');
            }
        });
    });

    // Smooth scroll with error handling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            try {
                e.preventDefault();
                const targetId = this.getAttribute('href');
                if (targetId === '#') return;

                const target = document.querySelector(targetId);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            } catch (error) {
                console.error('Error in smooth scroll:', error);
            }
        });
    });

    // Initialize tooltips and popovers if Bootstrap is loaded
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });

        var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }
    
    // Connect to Socket.IO server if on dashboard
    if (document.querySelector('.dashboard') && typeof io !== 'undefined') {
        connectWebSocket();
    }
});

/**
 * Connect to WebSocket server and set up events
 */
function connectWebSocket() {
    // Initialize Socket.IO connection
    const socket = io();
    
    // Get creator ID from meta tag
    const creatorId = document.querySelector('meta[name="creator-id"]')?.content;
    
    if (!creatorId) {
        console.error('Creator ID not found');
        return;
    }
    
    // Set up connection events
    socket.on('connect', function() {
        console.log('Connected to server');
        
        // Join creator's room
        socket.emit('join', {
            creator_id: creatorId
        });
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from server');
    });
    
    // Handle new tip events
    socket.on('new_tip', function(data) {
        console.log('New tip received:', data);
        
        // Show toast notification
        showToast('New tip received!', 'success');
        
        // Add to transaction table if exists
        addTransactionToTable(data);
        
        // Play sound if enabled
        playTipSound();
    });
    
    // Handle tip status updates
    socket.on('tip_status', function(data) {
        console.log('Tip status update:', data);
        
        // Update transaction status in table
        updateTransactionStatus(data.transaction_id, data.status);
    });
}

/**
 * Add a new transaction to the table
 */
function addTransactionToTable(data) {
    const transactionTable = document.querySelector('#transactions-table tbody');
    if (!transactionTable) return;
    
    // Create new row
    const row = document.createElement('tr');
    
    // Format date
    const date = new Date();
    const formattedDate = date.toISOString().split('T')[0] + ' ' + 
                        date.toTimeString().split(' ')[0].substring(0, 5);
    
    // Set row HTML
    row.innerHTML = `
        <td>${formattedDate}</td>
        <td>${data.name}</td>
        <td class="tip-amount">KES ${data.amount}</td>
        <td>${data.message || ''}</td>
        <td>
            <span class="badge bg-success" role="status" aria-label="Tip status: completed">
                completed
            </span>
        </td>
    `;
    
    // Add to top of table
    const firstRow = transactionTable.querySelector('tr');
    if (firstRow) {
        transactionTable.insertBefore(row, firstRow);
    } else {
        transactionTable.appendChild(row);
    }
    
    // Remove "No tips yet" row if it exists
    const noTipsRow = transactionTable.querySelector('tr td[colspan="5"]');
    if (noTipsRow) {
        noTipsRow.parentElement.remove();
    }
    
    // Highlight row
    row.classList.add('highlight-row');
    setTimeout(() => {
        row.classList.remove('highlight-row');
    }, 3000);
}

/**
 * Update transaction status in the table
 */
function updateTransactionStatus(transactionId, status) {
    // This would require transaction IDs in the table, which would need to be added to the HTML template
    // For now, we'll just reload the page to reflect the latest status
    location.reload();
}

/**
 * Show a toast notification
 */
function showToast(message, type = 'success') {
    // If Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        const toastId = type === 'success' ? 'copyToast' : 'errorToast';
        const toastElement = document.getElementById(toastId);
        
        if (toastElement) {
            const toastBody = toastElement.querySelector('.toast-body');
            if (toastBody) {
                toastBody.textContent = message;
            }
            
            const bsToast = new bootstrap.Toast(toastElement);
            bsToast.show();
            return;
        }
    }
    
    // Fallback to alert
    alert(message);
}

/**
 * Play tip notification sound
 */
function playTipSound() {
    const audio = document.getElementById('tip-sound');
    if (audio) {
        audio.play().catch(err => {
            console.error('Could not play sound:', err);
        });
    }
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    // Use modern Clipboard API if available
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text)
            .then(() => {
                showToast('Copied to clipboard!');
            })
            .catch(err => {
                console.error('Could not copy text:', err);
                showToast('Failed to copy', 'error');
            });
        return;
    }
    
    // Fallback to older approach
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = 0;
    document.body.appendChild(textarea);
    textarea.select();
    
    try {
        const success = document.execCommand('copy');
        if (success) {
            showToast('Copied to clipboard!');
        } else {
            showToast('Failed to copy', 'error');
        }
    } catch (err) {
        console.error('Could not copy text:', err);
        showToast('Failed to copy', 'error');
    } finally {
        document.body.removeChild(textarea);
    }
}

/**
 * Copy tip link to clipboard
 */
function copyTipLink() {
    const tipLink = document.getElementById('tipLink');
    if (tipLink) {
        copyToClipboard(tipLink.value);
    }
}

/**
 * Copy overlay URL to clipboard
 */
function copyOverlayUrl() {
    const overlayUrl = document.getElementById('overlayUrl');
    if (overlayUrl) {
        copyToClipboard(overlayUrl.value);
    }
} 