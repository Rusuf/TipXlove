document.addEventListener('DOMContentLoaded', function() {
    // Initialize variables
    let socket;
    const userId = document.body.getAttribute('data-user-id') || 'unknown';
    
    // Connect to WebSocket
    initializeSocketConnection();
    
    // Set up navigation
    setupNavigation();
    
    // Load initial data
    loadDashboardData();
    
    // Auto refresh data every 30 seconds
    setInterval(loadDashboardData, 30000);
    
    /**
     * Initialize WebSocket connection
     */
    function initializeSocketConnection() {
        socket = io.connect('/');
        
        socket.on('connect', function() {
            console.log('Connected to WebSocket');
            socket.emit('join', { userId: userId });
        });
        
        socket.on('new_tip', function(data) {
            console.log('New tip received:', data);
            showNotification('New tip received!');
            loadDashboardData();
        });
    }
    
    /**
     * Set up navigation between sections
     */
    function setupNavigation() {
        // Dashboard link
        document.getElementById('dashboardNavLink').addEventListener('click', function(e) {
            e.preventDefault();
            showSection('dashboardSection');
            updateActiveLink(this);
        });
        
        // Transactions link
        document.getElementById('transactionsNavLink').addEventListener('click', function(e) {
            e.preventDefault();
            showSection('transactionsSection');
            updateActiveLink(this);
            loadTransactionsData();
        });

        // Overlay link
        document.getElementById('overlayNavLink').addEventListener('click', function(e) {
            e.preventDefault();
            showSection('overlaySection');
            updateActiveLink(this);
        });
        
        // Profile link
        document.getElementById('profileNavLink').addEventListener('click', function(e) {
            e.preventDefault();
            showSection('profileSection');
            updateActiveLink(this);
        });
    }
    
    /**
     * Show selected section and hide others
     */
    function showSection(sectionId) {
        // Hide all sections
        document.getElementById('dashboardSection').style.display = 'none';
        document.getElementById('transactionsSection').style.display = 'none';
        document.getElementById('overlaySection').style.display = 'none';
        document.getElementById('profileSection').style.display = 'none';
        
        // Show selected section
        document.getElementById(sectionId).style.display = 'block';
    }
    
    /**
     * Update active navigation link
     */
    function updateActiveLink(link) {
        document.querySelectorAll('.sidebar .nav-link').forEach(function(el) {
            el.classList.remove('active');
        });
        link.classList.add('active');
    }
    
    /**
     * Load dashboard data from server
     */
    function loadDashboardData() {
        // Load stats
        fetch('/api/dashboard/stats')
            .then(response => response.json())
            .then(data => {
                document.getElementById('totalAmount').textContent = data.stats.total_tips.toLocaleString();
                document.getElementById('tipCount').textContent = data.stats.total_transactions.toLocaleString();
                document.getElementById('averageAmount').textContent = 
                    (data.stats.total_tips / (data.stats.total_transactions || 1)).toLocaleString();
                document.getElementById('lastRefreshTime').textContent = 'Last updated: ' + new Date().toLocaleTimeString();
            })
            .catch(error => {
                console.error('Error loading dashboard stats:', error);
            });

        // Load tip link
        fetch('/api/overlay/info')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    const fullUrl = window.location.origin + data.tipLink;
                    document.getElementById('tipLink').value = fullUrl;
                    
                    // Set QR code image
                    document.getElementById('qrCode').src = data.qrCodeUrl;
                }
            })
            .catch(error => {
                console.error('Error loading tip link:', error);
            });

        // Load recent transactions
        fetch('/api/transactions?days=7&limit=5')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    updateRecentTransactions(data.transactions);
                }
            })
            .catch(error => {
                console.error('Error loading recent transactions:', error);
            });
            
        // Load balance data
        loadBalanceData();
        
        // Load withdrawal history
        loadWithdrawalHistory();
    }
    
    /**
     * Load creator's balance information
     */
    function loadBalanceData() {
        fetch('/api/balance')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Update balance information in the dashboard
                    document.getElementById('availableBalance').textContent = data.balance.toLocaleString();
                    document.getElementById('pendingWithdrawals').textContent = data.pending_withdrawals.toLocaleString();
                    
                    // Update withdrawal modal
                    document.getElementById('modalAvailableBalance').textContent = 'KES ' + data.balance.toLocaleString();
                    
                    // Enable/disable withdraw button based on available balance
                    const withdrawBtn = document.getElementById('withdrawBtn');
                    withdrawBtn.disabled = data.balance <= 0;
                    
                    // Load creator's phone number for withdrawal
                    fetch('/api/profile')
                        .then(response => response.json())
                        .then(profileData => {
                            if (profileData.status === 'success') {
                                document.getElementById('withdrawPhoneNumber').textContent = profileData.creator.phone_number || 'No phone number set';
                            }
                        })
                        .catch(error => {
                            console.error('Error loading profile data:', error);
                        });
                }
            })
            .catch(error => {
                console.error('Error loading balance data:', error);
            });
    }
    
    /**
     * Load withdrawal history
     */
    function loadWithdrawalHistory() {
        fetch('/api/withdrawals')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    updateWithdrawalHistory(data.withdrawals);
                }
            })
            .catch(error => {
                console.error('Error loading withdrawal history:', error);
                showError('Failed to load withdrawal history');
            });
    }
    
    /**
     * Update withdrawal history table
     */
    function updateWithdrawalHistory(withdrawals) {
        const tableBody = document.getElementById('withdrawalHistory');
        tableBody.innerHTML = '';
        
        if (withdrawals.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="4" class="text-center">No withdrawals yet</td>';
            tableBody.appendChild(row);
            return;
        }
        
        withdrawals.forEach(withdrawal => {
            const row = document.createElement('tr');
            const date = new Date(withdrawal.created_at);
            const formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
            
            // Determine badge class based on status
            let statusBadgeClass = 'bg-secondary';
            if (withdrawal.status === 'completed') {
                statusBadgeClass = 'bg-success';
            } else if (withdrawal.status === 'pending') {
                statusBadgeClass = 'bg-warning text-dark';
            } else if (withdrawal.status === 'failed') {
                statusBadgeClass = 'bg-danger';
            }
            
            row.innerHTML = `
                <td>${formattedDate}</td>
                <td>KES ${withdrawal.amount.toLocaleString()}</td>
                <td><span class="badge ${statusBadgeClass}">${withdrawal.status}</span></td>
                <td>${withdrawal.mpesa_receipt || '-'}</td>
            `;
            
            tableBody.appendChild(row);
        });
    }
    
    /**
     * Load all transactions
     */
    function loadTransactionsData() {
        const days = document.getElementById('timeFilter').value;
        const status = document.getElementById('statusFilter').value;
        
        fetch(`/api/transactions?days=${days}&status=${status}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    updateAllTransactions(data.transactions);
                }
            })
            .catch(error => {
                console.error('Error loading transactions:', error);
            });
            
        // Load transaction chart data
        loadTransactionChart();
    }
    
    /**
     * Update all transactions table
     */
    function updateAllTransactions(transactions) {
        const tableBody = document.getElementById('allTransactions');
        tableBody.innerHTML = '';
        
        if (transactions.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="6" class="text-center">No transactions found</td>';
            tableBody.appendChild(row);
            return;
        }
        
        transactions.forEach(transaction => {
            const row = document.createElement('tr');
            const date = new Date(transaction.created_at);
            const formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
            
            // Determine badge class based on status
            let statusBadgeClass = 'bg-secondary';
            if (transaction.status === 'completed') {
                statusBadgeClass = 'bg-success';
            } else if (transaction.status === 'pending') {
                statusBadgeClass = 'bg-warning text-dark';
            } else if (transaction.status === 'failed') {
                statusBadgeClass = 'bg-danger';
            }
            
            row.innerHTML = `
                <td>${transaction.tipper_name || 'Anonymous'}</td>
                <td>KES ${transaction.amount.toLocaleString()}</td>
                <td>${transaction.message || '-'}</td>
                <td>${transaction.mpesa_receipt || '-'}</td>
                <td>${formattedDate}</td>
                <td><span class="badge ${statusBadgeClass}">${transaction.status}</span></td>
            `;
            
            tableBody.appendChild(row);
        });
    }
    
    /**
     * Update recent transactions
     */
    function updateRecentTransactions(transactions) {
        const tableBody = document.getElementById('recentTransactions');
        tableBody.innerHTML = '';
        
        if (transactions.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="5" class="text-center">No transactions yet</td>';
            tableBody.appendChild(row);
            return;
        }
        
        transactions.forEach(transaction => {
            const row = document.createElement('tr');
            const date = new Date(transaction.created_at);
            const formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
            
            // Determine badge class based on status
            let statusBadgeClass = 'bg-secondary';
            if (transaction.status === 'completed') {
                statusBadgeClass = 'bg-success';
            } else if (transaction.status === 'pending') {
                statusBadgeClass = 'bg-warning text-dark';
            } else if (transaction.status === 'failed') {
                statusBadgeClass = 'bg-danger';
            }
            
            row.innerHTML = `
                <td>${transaction.tipper_name || 'Anonymous'}</td>
                <td>KES ${transaction.amount.toLocaleString()}</td>
                <td>${transaction.message || '-'}</td>
                <td>${formattedDate}</td>
                <td><span class="badge ${statusBadgeClass}">${transaction.status}</span></td>
            `;
            
            tableBody.appendChild(row);
        });
    }
    
    /**
     * Load transaction chart
     */
    function loadTransactionChart() {
        const days = document.getElementById('chartTimeFilter').value;
        
        fetch(`/api/transactions/chart?days=${days}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    updateTransactionChart(data.data.dates, data.data.totals);
                }
            })
            .catch(error => {
                console.error('Error loading transaction chart:', error);
            });
    }
    
    /**
     * Update transaction chart
     */
    function updateTransactionChart(dates, totals) {
        const ctx = document.getElementById('transactionChart').getContext('2d');
        
        // If chart already exists, destroy it
        if (window.transactionChart) {
            window.transactionChart.destroy();
        }
        
        // Create new chart
        window.transactionChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                    label: 'Tips (KES)',
                    data: totals,
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 2,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    /**
     * Show notification
     */
    function showNotification(message) {
        const toast = new bootstrap.Toast(document.getElementById('newTipAlert'));
        document.querySelector('#newTipAlert .toast-body').innerHTML = `<i class="bi bi-bell-fill"></i> ${message}`;
        toast.show();
    }
    
    /**
     * Handle withdrawal submission
     */
    document.getElementById('submitWithdrawal').addEventListener('click', function() {
        const form = document.getElementById('withdrawalForm');
        const amount = document.getElementById('withdrawalAmount').value;
        const phoneNumber = document.getElementById('phoneNumber').value;
        const submitBtn = this;
        const spinner = submitBtn.querySelector('.spinner-border');

        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        if (!amount || isNaN(amount) || amount <= 0) {
            showError('Please enter a valid amount');
            return;
        }

        // Disable form and show spinner
        submitBtn.disabled = true;
        spinner.classList.remove('d-none');

        // Send withdrawal request
        fetch('/withdrawals/initiate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
            },
            body: JSON.stringify({
                amount: parseFloat(amount),
                phone_number: phoneNumber
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('withdrawalModal'));
                modal.hide();

                // Show success message
                if (data.test_mode) {
                    showSuccess('Test withdrawal completed successfully');
                } else {
                    showSuccess('Withdrawal initiated successfully. You will receive an M-Pesa payment shortly.');
                }

                // Reset form
                form.reset();

                // Update withdrawals table and stats
                loadWithdrawalHistory();
                loadBalanceData();
            } else {
                showError(data.message || 'Failed to process withdrawal');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('Network error. Please try again later.');
        })
        .finally(() => {
            // Re-enable form and hide spinner
            submitBtn.disabled = false;
            spinner.classList.add('d-none');
        });
    });
    
    /**
     * Show success toast
     */
    function showSuccess(message) {
        const toast = new bootstrap.Toast(document.getElementById('successAlert'));
        document.querySelector('#successAlert .toast-body').innerHTML = `<i class="bi bi-check-circle-fill"></i> ${message}`;
        toast.show();
    }
    
    /**
     * Show error toast
     */
    function showError(message) {
        const toast = new bootstrap.Toast(document.getElementById('errorAlert'));
        document.querySelector('#errorAlert .toast-body').innerHTML = `<i class="bi bi-exclamation-circle-fill"></i> ${message}`;
        toast.show();
    }
    
    /**
     * Copy text to clipboard
     */
    document.getElementById('copyTipLink').addEventListener('click', function() {
        const tipLink = document.getElementById('tipLink');
        tipLink.select();
        document.execCommand('copy');
        
        const toast = new bootstrap.Toast(document.getElementById('copyAlert'));
        toast.show();
    });
    
    // View All Transactions button
    document.getElementById('viewAllTransactionsBtn').addEventListener('click', function(e) {
        e.preventDefault();
        showSection('transactionsSection');
        updateActiveLink(document.getElementById('transactionsNavLink'));
        loadTransactionsData();
    });
    
    // Apply transaction filter
    document.getElementById('applyFilter').addEventListener('click', function() {
        loadTransactionsData();
    });
    
    // Update chart button
    document.getElementById('updateChart').addEventListener('click', function() {
        loadTransactionChart();
    });
    
    // Reset tip link
    document.getElementById('resetTipLink').addEventListener('click', function() {
        if (confirm('Are you sure you want to reset your tip link? The old link will no longer work.')) {
            fetch('/api/tip-link/reset', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showSuccess('Tip link reset successfully');
                    loadDashboardData(); // Reload to get new link
                } else {
                    showError(data.message || 'Failed to reset tip link');
                }
            })
            .catch(error => {
                console.error('Error resetting tip link:', error);
                showError('Failed to reset tip link');
            });
        }
    });
    
    // Test tip button
    document.getElementById('testTipBtn').addEventListener('click', function() {
        fetch('/api/overlay/test-tip', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showSuccess('Test tip sent successfully');
            } else {
                showError(data.message || 'Failed to send test tip');
            }
        })
        .catch(error => {
            console.error('Error sending test tip:', error);
            showError('Failed to send test tip');
        });
    });
    
    // Initialize overlay preview
    const overlayUrl = `${window.location.protocol}//${window.location.host}/overlay/${userId}`;
    document.getElementById('overlayUrl').value = overlayUrl;
    document.getElementById('overlayPreview').src = overlayUrl;
    
    // Copy overlay URL
    document.getElementById('copyOverlayUrl').addEventListener('click', function() {
        const overlayUrl = document.getElementById('overlayUrl');
        overlayUrl.select();
        document.execCommand('copy');
        
        const toast = new bootstrap.Toast(document.getElementById('copyAlert'));
        toast.show();
    });
    
    // Download QR code
    document.getElementById('downloadQR').addEventListener('click', function() {
        const img = document.getElementById('qrCode');
        const link = document.createElement('a');
        link.href = img.src;
        link.download = 'streamtip-qrcode.png';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });
    
    // Profile form submission
    document.getElementById('profileForm').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const email = document.getElementById('email').value;
        const phoneNumber = document.getElementById('phoneNumber').value;
        
        fetch('/api/user/profile', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                email: email,
                phone_number: phoneNumber
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showSuccess('Profile updated successfully');
                // Reload data to reflect changes
                loadDashboardData();
            } else {
                showError(data.message || 'Failed to update profile');
            }
        })
        .catch(error => {
            console.error('Error updating profile:', error);
            showError('Failed to update profile');
        });
    });
    
    // Test mode toggle
    document.getElementById('testModeToggle').addEventListener('change', function() {
        fetch('/api/settings/test-mode', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                enabled: this.checked
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showSuccess(`Test mode ${this.checked ? 'enabled' : 'disabled'}`);
            } else {
                showError(data.message || 'Failed to update test mode');
                // Reset toggle to previous state
                this.checked = !this.checked;
            }
        })
        .catch(error => {
            console.error('Error updating test mode:', error);
            showError('Failed to update test mode');
            // Reset toggle to previous state
            this.checked = !this.checked;
        });
    });
    
    // Load profile data for form
    fetch('/api/user/profile')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                document.getElementById('username').value = data.profile.username || '';
                document.getElementById('email').value = data.profile.email || '';
                document.getElementById('phoneNumber').value = data.profile.phone_number || '';
            }
        })
        .catch(error => {
            console.error('Error loading profile data:', error);
        });

    // Listen for withdrawal completion
    document.addEventListener('withdrawalCompleted', function() {
        loadWithdrawalHistory();
        loadBalanceData();
    });
}); 