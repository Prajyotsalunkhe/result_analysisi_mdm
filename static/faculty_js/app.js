// Login Logic
const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const errorDiv = document.getElementById('loginError');
        
        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });

            if (response.ok) {
                localStorage.setItem('loggedIn', 'true');
                window.location.href = '/faculty_dashboard';
            } else {
                errorDiv.classList.remove('hidden');
            }
        } catch (err) {
            console.error('Login error:', err);
            errorDiv.classList.remove('hidden');
        }
    });
}

// Logout Logic
const logoutBtn = document.getElementById('logoutBtn');
if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('loggedIn');
        window.location.href = '/faculty_login';
    });
}

// Result Analysis Fetch
async function fetchResultsData() {
    const loader = document.getElementById('resultsLoader');
    const tableContainer = document.getElementById('resultsTableContainer');
    const errorDiv = document.getElementById('resultsError');
    const emptyDiv = document.getElementById('resultsEmpty');
    const tbody = document.getElementById('resultsTableBody');
    const headerRow1 = document.getElementById('resultsHeaderRow1');
    const headerRow2 = document.getElementById('resultsHeaderRow2');

    if (!loader) return;

    loader.classList.remove('hidden');
    tableContainer.classList.add('hidden');
    errorDiv.classList.add('hidden');
    emptyDiv.classList.add('hidden');
    tbody.innerHTML = '';

    try {
        const response = await fetch('/api/results');
        if (!response.ok) throw new Error('Network response was not ok');
        
        const res = await response.json();
        const data = res.data;

        loader.classList.add('hidden');

        if (data && data.length > 0) {
            // 1. Identify all unique subjects and their categories
            const subjectsMap = {}; // { "Subject Name": Set(["CIE", "TW", ...]) }
            data.forEach(item => {
                if (item.subjects && Array.isArray(item.subjects)) {
                    item.subjects.forEach(sub => {
                        if (!subjectsMap[sub.name]) subjectsMap[sub.name] = new Set();
                        subjectsMap[sub.name].add(sub.category);
                    });
                }
            });

            const sortedSubjects = Object.keys(subjectsMap).sort();
            
            // 2. Build the Headers
            // Clear dynamic parts (everything except PRN, Name, Overall)
            // PRN and Name are index 0, 1. Overall are at the end.
            const prnHeader = '<th rowspan="2">PRN</th>';
            const nameHeader = '<th rowspan="2">Name</th>';
            const overallTotalHeader = '<th rowspan="2">OVERALL Total</th>';
            const overallPercHeader = '<th rowspan="2">OVERALL %</th>';
            
            let row1Html = prnHeader + nameHeader;
            let row2Html = '';
            
            const columnStructure = []; // List of { subject, category }

            sortedSubjects.forEach(subName => {
                const categories = Array.from(subjectsMap[subName]).sort();
                row1Html += `<th colspan="${categories.length * 2}">${subName}</th>`;
                categories.forEach(cat => {
                    row2Html += `<th>${cat} Score</th><th>Status</th>`;
                    columnStructure.push({ name: subName, category: cat });
                });
            });
            
            row1Html += overallTotalHeader + overallPercHeader;
            
            headerRow1.innerHTML = row1Html;
            headerRow2.innerHTML = row2Html;

            // 3. Build the Rows
            data.forEach(item => {
                const tr = document.createElement('tr');
                
                // Fixed Metadata
                let rowHtml = `<td><span class="prn-text">${item.prn || 'N/A'}</span></td>`;
                rowHtml += `<td>${item.name || 'N/A'}</td>`;
                
                // Subject Scores
                columnStructure.forEach(col => {
                    const subData = (item.subjects || []).find(s => s.name === col.name && s.category === col.category);
                    if (subData) {
                        const statusClass = subData.status.toUpperCase() === 'PASS' ? 'badge-success' : 'badge-error';
                        rowHtml += `<td>${subData.score}</td>`;
                        rowHtml += `<td><span class="badge ${statusClass}">${subData.status}</span></td>`;
                    } else {
                        rowHtml += `<td>-</td><td>-</td>`;
                    }
                });
                
                // Overall Stats
                const summary = item.summary || {};
                rowHtml += `<td><strong>${summary.total_obtained || 0} / ${summary.out_of || 0}</strong></td>`;
                rowHtml += `<td><strong>${summary.percentage ? summary.percentage + '%' : 'N/A'}</strong></td>`;
                
                tr.innerHTML = rowHtml;
                tbody.appendChild(tr);
            });
            
            tableContainer.classList.remove('hidden');
        } else {
            emptyDiv.classList.remove('hidden');
        }

    } catch (error) {
        console.error('Fetch results error:', error);
        loader.classList.add('hidden');
        errorDiv.classList.remove('hidden');
    }
}

async function downloadResultsExcel() {
    const btn = document.getElementById('downloadResultsExcelBtn');
    const originalText = btn.textContent;
    btn.textContent = 'Downloading...';
    btn.disabled = true;

    try {
        window.location.href = '/api/download_results_excel';
        setTimeout(() => {
            btn.textContent = originalText;
            btn.disabled = false;
        }, 2000);
    } catch (error) {
        console.error('Download error:', error);
        alert('Failed to download Excel file.');
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

// MDM Allocation Fetch
async function fetchMdmData() {
    const loader = document.getElementById('mdmLoader');
    const tableContainer = document.getElementById('mdmTableContainer');
    const errorDiv = document.getElementById('mdmError');
    const emptyDiv = document.getElementById('mdmEmpty');
    const tbody = document.getElementById('mdmTableBody');
    const tableTitle = document.getElementById('tableTitle');

    // Stats elements
    const statTotal = document.getElementById('statTotal');
    const statAllocated = document.getElementById('statAllocated');
    const statWaitlisted = document.getElementById('statWaitlisted');
    const statRejected = document.getElementById('statRejected');

    if (!loader) return;

    loader.classList.remove('hidden');
    tableContainer.classList.add('hidden');
    errorDiv.classList.add('hidden');
    emptyDiv.classList.add('hidden');
    tbody.innerHTML = '';

    try {
        const response = await fetch('/api/mdm_preferences');
        if (!response.ok) throw new Error('Network response was not ok');
        
        const res = await response.json();
        const data = res.data;

        loader.classList.add('hidden');

        if (data && data.length > 0) {
            let allocatedCount = 0;
            let waitlistedCount = 0;
            let rejectedCount = 0;

            data.forEach(item => {
                if (item.Status === 'ALLOCATED') allocatedCount++;
                else if (item.Status === 'WAITLISTED') waitlistedCount++;
                else if (item.Status === 'REJECTED') rejectedCount++;

                const tr = document.createElement('tr');
                
                const statusClass = item.Status === 'ALLOCATED' ? 'status-badge' : 'status-badge waitlisted-badge';
                
                tr.innerHTML = `
                    <td><span class="prn-text">${item.PRN || '-'}</span></td>
                    <td>${item.Name || '-'}</td>
                    <td>${item.Marks || '0'}</td>
                    <td>${item.Percentage || '-'}</td>
                    <td>${item['Current Dept'] || '-'}</td>
                    <td><span class="allotted-minor">${item['Allocated Minor'] || '-'}</span></td>
                    <td>${item['Preference Used'] || '-'}</td>
                    <td><span class="${statusClass}">${item.Status || 'WAITLISTED'}</span></td>
                `;
                tbody.appendChild(tr);
            });

            // Update Stats
            statTotal.textContent = data.length;
            statAllocated.textContent = allocatedCount;
            statWaitlisted.textContent = waitlistedCount;
            statRejected.textContent = rejectedCount;
            
            if(tableTitle) tableTitle.textContent = `Allocated Students (${allocatedCount})`;

            tableContainer.classList.remove('hidden');
        } else {
            emptyDiv.classList.remove('hidden');
        }

    } catch (error) {
        console.error('Fetch MDM error:', error);
        loader.classList.add('hidden');
        errorDiv.classList.remove('hidden');
    }
}

async function downloadMdmExcel() {
    const btn = document.getElementById('downloadExcelBtn');
    const originalText = btn.textContent;
    btn.textContent = 'Downloading...';
    btn.disabled = true;

    try {
        window.location.href = '/api/download_mdm_excel';
        setTimeout(() => {
            btn.textContent = originalText;
            btn.disabled = false;
        }, 2000);
    } catch (error) {
        console.error('Download error:', error);
        alert('Failed to download Excel file.');
        btn.textContent = originalText;
        btn.disabled = false;
    }
}
