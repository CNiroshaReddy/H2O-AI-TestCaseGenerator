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

// Add new input row
function addInputRow() {
    const container = document.getElementById('inputs-container');
    const newRow = document.createElement('div');
    newRow.className = 'input-row';
    newRow.innerHTML = `
        <input type="file" class="file-input" accept=".doc,.docx,.pdf,.txt" multiple>
        <input type="text" class="url-input" placeholder="Or enter webpage URL">
        <button class="btn-add" onclick="addInputRow()">+</button>
    `;
    container.appendChild(newRow);
}

// Handle upload
function handleUpload() {
    const inputRows = document.querySelectorAll('.input-row');
    const validationMsg = document.getElementById('validation-message');
    let hasInput = false;
    let duplicates = [];
    
    inputRows.forEach(row => {
        const fileInput = row.querySelector('.file-input');
        const urlInput = row.querySelector('.url-input');
        
        if (fileInput.files.length > 0) {
            Array.from(fileInput.files).forEach(file => {
                const ext = file.name.split('.').pop().toLowerCase();
                if (['doc', 'docx', 'pdf', 'txt'].includes(ext)) {
                    // Check for duplicates
                    const isDuplicate = uploadedItems.some(item => 
                        item.type === 'file' && item.name.toLowerCase() === file.name.toLowerCase()
                    );
                    
                    if (isDuplicate) {
                        duplicates.push(`File: ${file.name}`);
                    } else {
                        uploadedItems.push({ type: 'file', name: file.name, file: file });
                        hasInput = true;
                    }
                } else {
                    showValidation('Unsupported file type: ' + file.name, 'error');
                }
            });
        }
        
        if (urlInput.value.trim()) {
            const url = urlInput.value.trim();
            // Check for duplicates
            const isDuplicate = uploadedItems.some(item => 
                item.type === 'url' && item.name.toLowerCase() === url.toLowerCase()
            );
            
            if (isDuplicate) {
                duplicates.push(`URL: ${url}`);
            } else {
                uploadedItems.push({ type: 'url', name: url });
                hasInput = true;
            }
        }
    });
    
    // Show duplicate error if any
    if (duplicates.length > 0) {
        alert(`❌ Duplicate items detected!\n\nThe following items are already uploaded:\n\n${duplicates.join('\n')}\n\nPlease remove duplicates and try again.`);
        showValidation(`${duplicates.length} duplicate item(s) found and not added`, 'error');
    }
    
    if (hasInput) {
        updateUploadedList();
        document.getElementById('generateBtn').disabled = false;
        if (duplicates.length === 0) {
            showValidation('✅ Items added successfully!', 'success');
        } else {
            showValidation('✅ Some items added (duplicates skipped)', 'success');
        }
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
        alert('❌ Error: ' + error.message);
        loading.style.display = 'none';
        generateBtn.disabled = false;
        showValidation('Error: ' + error.message, 'error');
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
