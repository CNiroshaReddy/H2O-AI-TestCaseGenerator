let uploadedItems = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Clear results container on page load
    const resultsContainer = document.getElementById('results-container');
    if (resultsContainer) {
        resultsContainer.innerHTML = '<p style="text-align:center;padding:20px;color:#6B7280;">No results available. Please upload documents/URLs and generate test cases first.</p>';
    }
});

// Tab switching
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tabName = btn.dataset.tab;
        
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
        
        btn.classList.add('active');
        document.getElementById(`${tabName}-tab`).classList.add('active');
        
        // Don't auto-load results - user must click View button
    });
});

// Validate URL format
function isValidUrl(url) {
    try {
        const trimmed = url.trim();
        // Check if URL contains multiple protocol occurrences (https://, http://)
        const protocolCount = (trimmed.match(/https?:\/\//g) || []).length;
        if (protocolCount !== 1) return false;
        
        const parsed = new URL(trimmed);
        // Must be http or https
        if (!['http:', 'https:'].includes(parsed.protocol)) return false;
        
        const hostname = parsed.hostname;
        // Hostname must have a valid TLD: at least one dot, letters-only TLD of 2+ chars
        if (!/^([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$/.test(hostname)) return false;
        
        // Extract TLD and validate against common TLDs
        const parts = hostname.split('.');
        const tld = parts[parts.length - 1].toLowerCase();
        
        // List of common valid TLDs
        const validTlds = ['com', 'org', 'net', 'edu', 'gov', 'mil', 'int', 'io', 'co', 'uk', 'us', 'ca', 'de', 'fr', 'it', 'es', 'nl', 'be', 'ch', 'at', 'se', 'no', 'dk', 'fi', 'pl', 'cz', 'ru', 'cn', 'jp', 'kr', 'in', 'au', 'nz', 'br', 'mx', 'za', 'sg', 'hk', 'tw', 'th', 'my', 'ph', 'id', 'vn', 'pk', 'bd', 'ae', 'sa', 'il', 'tr', 'gr', 'pt', 'ie', 'info', 'biz', 'name', 'pro', 'mobi', 'asia', 'tel', 'travel', 'xxx', 'app', 'dev', 'online', 'site', 'website', 'space', 'cloud', 'tech', 'ai', 'tv', 'cc', 'ws', 'me', 'blog', 'shop', 'store', 'news', 'wiki', 'xyz'];
        
        if (!validTlds.includes(tld)) return false;
        
        return true;
    } catch { return false; }
}

// Check if input contains multiple URLs (comma or space separated)
function containsMultipleUrls(input) {
    const trimmed = input.trim();
    // Check for comma separation
    if (trimmed.includes(',')) return true;
    // Check for space separation (multiple URLs with spaces)
    const urlPattern = /(https?:\/\/[^\s]+)/g;
    const matches = trimmed.match(urlPattern);
    return matches && matches.length > 1;
}

// Enable/disable + and - buttons based on row input
function onRowInputChange(el) {
    const row = el.closest('.input-row');
    const fileInput = row.querySelector('.file-input');
    const urlInput = row.querySelector('.url-input');
    const addBtn = row.querySelector('.btn-add');
    const removeBtn = row.querySelector('.btn-remove-row');
    const hasFile = fileInput.files.length > 0;
    const urlVal = urlInput.value.trim();
    
    // Check if URL contains multiple URLs (comma or space separated)
    if (urlVal && containsMultipleUrls(urlVal)) {
        showValidation('❌ Please enter only one URL per field. Do not use commas or spaces to separate multiple URLs.', 'error');
        addBtn.disabled = true;
        removeBtn.disabled = true;
        return;
    }
    
    // Check if URL has multiple protocols
    if (urlVal && (urlVal.match(/https?:\/\//g) || []).length > 1) {
        showValidation('❌ Please enter only one URL. Do not concatenate multiple URLs.', 'error');
        addBtn.disabled = true;
        removeBtn.disabled = true;
        return;
    }
    
    // Check if URL format is invalid
    if (urlVal && !isValidUrl(urlVal)) {
        showValidation(`❌ Please enter a valid URL. Example: https://www.example.com`, 'error');
        addBtn.disabled = true;
        removeBtn.disabled = true;
        return;
    }
    
    const hasValidInput = hasFile || (urlVal && isValidUrl(urlVal));
    addBtn.disabled = !hasValidInput;
    removeBtn.disabled = !hasValidInput;
}

// Remove an input row
function removeInputRow(btn) {
    const container = document.getElementById('inputs-container');
    const rows = container.querySelectorAll('.input-row');
    if (rows.length > 1) {
        btn.closest('.input-row').remove();
    } else {
        const row = btn.closest('.input-row');
        row.querySelector('.file-input').value = '';
        row.querySelector('.url-input').value = '';
        row.querySelector('.btn-add').disabled = true;
        row.querySelector('.btn-remove-row').disabled = true;
    }
    // Re-evaluate button states on all remaining rows
    const updatedRows = container.querySelectorAll('.input-row');
    updatedRows.forEach(row => {
        const fileInput = row.querySelector('.file-input');
        const urlInput = row.querySelector('.url-input');
        const hasValidInput = fileInput.files.length > 0 || (urlInput.value.trim() && isValidUrl(urlInput.value.trim()));
        row.querySelector('.btn-add').disabled = !hasValidInput;
        row.querySelector('.btn-remove-row').disabled = updatedRows.length === 1 && !hasValidInput;
    });
}

// Add new input row
function addInputRow() {
    const currentCount = uploadedItems.length + document.querySelectorAll('.input-row').length;
    if (currentCount >= 5) {
        alert('❌ Maximum limit of 5 uploads reached.');
        return;
    }
    const container = document.getElementById('inputs-container');
    const newRow = document.createElement('div');
    newRow.className = 'input-row';
    newRow.innerHTML = `
        <input type="file" class="file-input" accept=".doc,.docx,.pdf,.txt" multiple onchange="onRowInputChange(this)">
        <input type="text" class="url-input" placeholder="Or enter webpage URL" oninput="onRowInputChange(this)">
        <button class="btn-add" onclick="addInputRow()" disabled>+</button>
        <button class="btn-remove-row" onclick="removeInputRow(this)" disabled>-</button>
    `;
    container.appendChild(newRow);
}

// Handle upload
function handleUpload() {
    const inputRows = document.querySelectorAll('.input-row');
    let hasInput = false;
    let duplicates = [];
    let errors = [];

    inputRows.forEach(row => {
        const fileInput = row.querySelector('.file-input');
        const urlInput = row.querySelector('.url-input');

        if (fileInput.files.length > 0) {
            Array.from(fileInput.files).forEach(file => {
                if (uploadedItems.length >= 5) {
                    showValidation('Maximum limit of 5 uploads reached.', 'error');
                    return;
                }
                if (file.size === 0) {
                    errors.push(`File "${file.name}" is empty.`);
                    return;
                }
                const ext = file.name.split('.').pop().toLowerCase();
                if (!['doc', 'docx', 'pdf', 'txt'].includes(ext)) {
                    errors.push(`Unsupported file type: "${file.name}". Please upload .doc, .docx, .pdf, or .txt files.`);
                    return;
                }
                const isDuplicate = uploadedItems.some(item =>
                    item.type === 'file' && item.name.toLowerCase() === file.name.toLowerCase()
                );
                if (isDuplicate) { duplicates.push(`File: ${file.name}`); return; }
                uploadedItems.push({ type: 'file', name: file.name, file: file });
                hasInput = true;
            });
        }

        if (urlInput.value.trim()) {
            if (uploadedItems.length >= 5) {
                showValidation('Maximum limit of 5 uploads reached.', 'error');
                return;
            }
            const url = urlInput.value.trim();
            
            // Check for multiple URLs (comma or space separated)
            if (containsMultipleUrls(url)) {
                errors.push('Please enter only one URL per field. Do not use commas or spaces to separate multiple URLs.');
                return;
            }
            
            if (!isValidUrl(url)) {
                errors.push(`Please enter a valid URL: "${url}"`);
                return;
            }
            const isDuplicate = uploadedItems.some(item =>
                item.type === 'url' && item.name.toLowerCase() === url.toLowerCase()
            );
            if (isDuplicate) { duplicates.push(`URL: ${url}`); return; }
            uploadedItems.push({ type: 'url', name: url });
            hasInput = true;
        }
    });

    if (errors.length > 0) {
        showValidation('❌ ' + errors[0], 'error');
        return;
    }
    if (duplicates.length > 0) {
        alert(`❌ Duplicate items detected!\n\n${duplicates.join('\n')}\n\nPlease remove duplicates and try again.`);
        showValidation(`${duplicates.length} duplicate item(s) found and not added`, 'error');
    }
    if (hasInput) {
        updateUploadedList();
        document.getElementById('generateBtn').disabled = false;
        showValidation(duplicates.length === 0 ? '✅ Items added successfully!' : '✅ Some items added (duplicates skipped)', 'success');
    } else if (duplicates.length === 0) {
        showValidation('❌ Please select files or enter URLs', 'error');
    }
}

// Update uploaded list display
function updateUploadedList() {
    const listDiv = document.getElementById('uploaded-list');
    listDiv.innerHTML = '<h3>Uploaded Items:</h3>';
    
    uploadedItems.forEach((item, index) => {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'uploaded-item';
        itemDiv.innerHTML = `
            <span>${item.type === 'file' ? '📄' : '🌐'} ${item.name}</span>
            <button class="btn-delete" onclick="deleteItem(${index})" title="Remove this item">✕</button>
        `;
        listDiv.appendChild(itemDiv);
    });
}

// Delete uploaded item
function deleteItem(index) {
    uploadedItems.splice(index, 1);
    updateUploadedList();
    
    // Disable generate button if no items left
    if (uploadedItems.length === 0) {
        document.getElementById('generateBtn').disabled = true;
    }
    
    showValidation('Item removed', 'success');
}

// Show validation message
function showValidation(message, type) {
    const validationMsg = document.getElementById('validation-message');
    validationMsg.textContent = message;
    validationMsg.className = `validation-message ${type}`;
    validationMsg.style.display = 'block';
    
    setTimeout(() => {
        validationMsg.style.display = 'none';
    }, 3000);
}

// Generate test cases
async function generateTestCases() {
    console.log('=== GENERATE TEST CASES BUTTON CLICKED ===');
    console.log('Uploaded items:', uploadedItems);
    
    if (uploadedItems.length === 0) {
        alert('Please upload files or add URLs first!');
        showValidation('No items to process', 'error');
        return;
    }
    
    const generateBtn = document.getElementById('generateBtn');
    const loading = document.getElementById('loading');
    
    generateBtn.disabled = true;
    loading.style.display = 'block';
    
    const formData = new FormData();
    
    uploadedItems.forEach(item => {
        if (item.type === 'file') {
            console.log('Adding file:', item.name);
            formData.append('files', item.file);
        } else {
            console.log('Adding URL:', item.name);
            formData.append('urls', item.name);
        }
    });
    
    console.log('Sending POST request to /upload endpoint...');
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Response data:', data);
        
        if (data.success) {
            loading.style.display = 'none';
            
            console.log('SUCCESS! Test cases generated:', data.results.length, 'scenarios');
            
            // Count total test cases
            let totalTestCases = 0;
            data.results.forEach(scenario => {
                totalTestCases += scenario.test_cases.length;
            });

            // Enable View and Download buttons
            document.getElementById('viewBtn').disabled = false;
            document.getElementById('downloadBtn').disabled = false;
            
            // Switch to output tab
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
            
            document.querySelector('[data-tab="output"]').classList.add('active');
            document.getElementById('output-tab').classList.add('active');
            
            // Clear results container - don't display automatically
            const resultsContainer = document.getElementById('results-container');
            resultsContainer.innerHTML = '<p style="text-align:center;padding:20px;color:#6B7280;">Click "View your TS & TC" button to preview the generated test cases.</p>';
            
            // Show success alert
            alert(`✅ Success!\n\nGenerated ${data.results.length} Test Scenarios with ${totalTestCases} Test Cases.\n\nClick "View your TS & TC" button to preview results.`);
            
            showValidation('Test cases generated successfully!', 'success');
        } else {
            console.log('FAILED:', data.message);
            alert('❌ Error: ' + data.message);
            loading.style.display = 'none';
            generateBtn.disabled = false;
            showValidation(data.message || 'Error generating test cases', 'error');
        }
    } catch (error) {
        console.error('ERROR during fetch:', error);
        let errorMsg = error.message;
        
        if (error instanceof TypeError) {
            errorMsg = 'Server is unreachable. Please check your connection and try again.';
        } else if (error.message.includes('Server error')) {
            errorMsg = `Server error occurred. ${error.message}`;
        }
        
        alert('❌ Error: ' + errorMsg);
        loading.style.display = 'none';
        generateBtn.disabled = false;
        showValidation('Error: ' + errorMsg, 'error');
    }
}

// View results
async function viewResults() {
    console.log('View Results button clicked - Loading results...');
    try {
        const response = await fetch('/get_results');
        const data = await response.json();
        
        console.log('Results data:', data);
        
        if (data.success && data.results && data.results.length > 0) {
            console.log('Displaying', data.results.length, 'scenarios');
            displayResults(data.results);
            alert(`✅ Loaded ${data.results.length} Test Scenarios for preview.`);
        } else {
            console.log('No results found');
            alert('⚠️ No results available. Please generate test cases first.');
            document.getElementById('results-container').innerHTML = '<p style="text-align:center;padding:20px;color:#6B7280;">No results available. Please upload documents/URLs and generate test cases first.</p>';
        }
    } catch (error) {
        console.error('Error loading results:', error);
        alert('❌ Error loading results: ' + error.message);
        document.getElementById('results-container').innerHTML = '<p style="text-align:center;padding:20px;color:#d32f2f;">Error loading results: ' + error.message + '</p>';
    }
}

// Display results in table
function displayResults(results) {
    const container = document.getElementById('results-container');
    
    if (!results || results.length === 0) {
        container.innerHTML = '<p style="text-align:center;padding:20px;color:#6B7280;">No test cases to display</p>';
        return;
    }
    
    let html = '<table class="results-table"><thead><tr>';
    html += '<th>TS#</th><th>Scenario Description</th><th>TC#</th>';
    html += '<th>Test Case Steps</th><th>Expected Results</th><th>Test Data</th>';
    html += '<th>Results</th><th>Defects</th><th>Comments</th>';
    html += '</tr></thead><tbody>';
    
    results.forEach(scenario => {
        if (scenario.test_cases && scenario.test_cases.length > 0) {
            scenario.test_cases.forEach(tc => {
                html += '<tr>';
                html += `<td>${scenario.ts_id}</td>`;
                html += `<td>${scenario.scenario_desc}</td>`;
                html += `<td>${tc.tc_id}</td>`;
                html += `<td style="white-space: pre-wrap;">${tc.steps}</td>`;
                html += `<td>${tc.expected}</td>`;
                html += `<td>${tc.test_data || ''}</td>`;
                html += `<td>${tc.results || ''}</td>`;
                html += `<td>${tc.defects || ''}</td>`;
                html += `<td>${tc.comments || ''}</td>`;
                html += '</tr>';
            });
        }
    });
    
    html += '</tbody></table>';
    container.innerHTML = html;
    
    console.log('Results displayed successfully');
}

// Download Excel
function downloadExcel() {
    try {
        // Generate timestamp in same format as server
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        
        const timestamp = `${year}-${month}-${day}_${hours}-${minutes}-${seconds}`;
        const filename = `H2O_AI_TestCases_${timestamp}.xlsx`;
        
        window.location.href = '/download_excel';
        
        // Show success message after a short delay
        setTimeout(() => {
            alert(`✅ Download Complete!\n\nYour test cases have been downloaded as an Excel file.\n\nFile name: ${filename}`);
        }, 1000);
    } catch (error) {
        alert('❌ Error downloading file: ' + error.message);
    }
}


// Keyboard Navigation
document.addEventListener('keydown', function(event) {
    // Escape key - Close modal
    if (event.key === 'Escape') {
        const modal = document.getElementById('helpModal');
        if (modal && modal.style.display === 'block') {
            closeHelpModal();
        }
    }
    
    // Alt + H - Open Help
    if (event.altKey && event.key === 'h') {
        event.preventDefault();
        openHelpModal();
    }
    
    // Alt + L - Logout
    if (event.altKey && event.key === 'l') {
        event.preventDefault();
        const logoutBtn = document.querySelector('.btn-logout');
        if (logoutBtn) {
            logoutBtn.click();
        }
    }
    
    // Alt + U - Upload
    if (event.altKey && event.key === 'u') {
        event.preventDefault();
        const uploadBtn = document.querySelector('.btn-upload');
        if (uploadBtn) {
            uploadBtn.click();
        }
    }
    
    // Alt + G - Generate
    if (event.altKey && event.key === 'g') {
        event.preventDefault();
        const generateBtn = document.getElementById('generateBtn');
        if (generateBtn && !generateBtn.disabled) {
            generateBtn.click();
        }
    }
    
    // Alt + V - View Results
    if (event.altKey && event.key === 'v') {
        event.preventDefault();
        const viewBtn = Array.from(document.querySelectorAll('.btn-primary')).find(btn => btn.textContent.includes('View'));
        if (viewBtn) {
            viewBtn.click();
        }
    }
    
    // Alt + D - Download
    if (event.altKey && event.key === 'd') {
        event.preventDefault();
        const downloadBtn = Array.from(document.querySelectorAll('.btn-primary')).find(btn => btn.textContent.includes('Download'));
        if (downloadBtn) {
            downloadBtn.click();
        }
    }
    
    // Arrow keys for tab navigation (only when not in input field)
    const tabButtons = document.querySelectorAll('.tab-btn');
    if (tabButtons.length > 0 && event.target.tagName !== 'INPUT' && event.target.tagName !== 'TEXTAREA') {
        const activeTab = document.querySelector('.tab-btn.active');
        let currentIndex = Array.from(tabButtons).indexOf(activeTab);
        
        if (event.key === 'ArrowRight') {
            event.preventDefault();
            currentIndex = (currentIndex + 1) % tabButtons.length;
            tabButtons[currentIndex].click();
            tabButtons[currentIndex].focus();
        } else if (event.key === 'ArrowLeft') {
            event.preventDefault();
            currentIndex = (currentIndex - 1 + tabButtons.length) % tabButtons.length;
            tabButtons[currentIndex].click();
            tabButtons[currentIndex].focus();
        }
    }
    
    // Arrow keys for guide tabs in modal
    const guideTabButtons = document.querySelectorAll('.guide-tab-btn');
    if (guideTabButtons.length > 0 && document.getElementById('helpModal').style.display === 'block') {
        const activeGuideTab = document.querySelector('.guide-tab-btn.active');
        let currentGuideIndex = Array.from(guideTabButtons).indexOf(activeGuideTab);
        
        if (event.key === 'ArrowRight') {
            event.preventDefault();
            currentGuideIndex = (currentGuideIndex + 1) % guideTabButtons.length;
            guideTabButtons[currentGuideIndex].click();
            guideTabButtons[currentGuideIndex].focus();
        } else if (event.key === 'ArrowLeft') {
            event.preventDefault();
            currentGuideIndex = (currentGuideIndex - 1 + guideTabButtons.length) % guideTabButtons.length;
            guideTabButtons[currentGuideIndex].click();
            guideTabButtons[currentGuideIndex].focus();
        }
    }
    
    // Enter key for buttons
    if (event.key === 'Enter') {
        if (event.target.classList.contains('btn-primary') || 
            event.target.classList.contains('btn-generate') ||
            event.target.classList.contains('btn-upload') ||
            event.target.classList.contains('btn-help') ||
            event.target.classList.contains('btn-logout')) {
            event.preventDefault();
            event.target.click();
        }
    }
});

// Add keyboard hints to buttons
document.addEventListener('DOMContentLoaded', function() {
    // Add title attributes for keyboard shortcuts
    const helpBtn = document.querySelector('.btn-help');
    if (helpBtn) {
        helpBtn.title = 'Help (Alt+H)';
    }
    
    const logoutBtn = document.querySelector('.btn-logout');
    if (logoutBtn) {
        logoutBtn.title = 'Logout (Alt+L)';
    }
    
    const uploadBtn = document.querySelector('.btn-upload');
    if (uploadBtn) {
        uploadBtn.title = 'Upload (Alt+U)';
    }
    
    const generateBtn = document.getElementById('generateBtn');
    if (generateBtn) {
        generateBtn.title = 'Generate Test Cases (Alt+G)';
    }
    
    // Add focus styles for better keyboard navigation visibility
    document.querySelectorAll('button, a, input').forEach(element => {
        element.addEventListener('focus', function() {
            this.style.outline = '2px solid var(--primary)';
            this.style.outlineOffset = '2px';
        });
        
        element.addEventListener('blur', function() {
            this.style.outline = 'none';
        });
    });
});
