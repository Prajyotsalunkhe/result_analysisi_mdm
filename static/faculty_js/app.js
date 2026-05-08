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
            data.forEach(item => {
                const tr = document.createElement('tr');
                
                // Assuming summary has total_obtained, out_of, percentage
                const summary = item.summary || {};
                const totalMarks = `${summary.total_obtained || 0} / ${summary.out_of || 0}`;
                const percentage = summary.percentage ? `${summary.percentage}%` : 'N/A';
                
                // Determine overall status from subjects or hardcoded if not present
                // Simple logic: if any subject failed, overall fail
                let statusBadge = '';
                let isPass = true;
                if (item.subjects && Array.isArray(item.subjects)) {
                    isPass = item.subjects.every(sub => sub.status && sub.status.toUpperCase() === 'PASS');
                }
                
                if (isPass) {
                    statusBadge = '<span class="badge badge-success">PASS</span>';
                } else {
                    statusBadge = '<span class="badge badge-error">FAIL</span>';
                }

                tr.innerHTML = `
                    <td><strong>${item.prn || 'N/A'}</strong></td>
                    <td>${item.name || 'N/A'}</td>
                    <td>${item.dept || 'N/A'}</td>
                    <td>${item.sem || 'N/A'}</td>
                    <td>${totalMarks}</td>
                    <td>${percentage}</td>
                    <td>${statusBadge}</td>
                `;
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

// MDM Allocation Fetch
async function fetchMdmData() {
    const loader = document.getElementById('mdmLoader');
    const tableContainer = document.getElementById('mdmTableContainer');
    const errorDiv = document.getElementById('mdmError');
    const emptyDiv = document.getElementById('mdmEmpty');
    const theadRow = document.getElementById('mdmTableHead');
    const tbody = document.getElementById('mdmTableBody');

    if (!loader) return;

    loader.classList.remove('hidden');
    tableContainer.classList.add('hidden');
    errorDiv.classList.add('hidden');
    emptyDiv.classList.add('hidden');
    theadRow.innerHTML = '';
    tbody.innerHTML = '';

    try {
        const response = await fetch('/api/mdm_preferences');
        if (!response.ok) throw new Error('Network response was not ok');
        
        const res = await response.json();
        const data = res.data;

        loader.classList.add('hidden');

        if (data && data.length > 0) {
            // Dynamically create headers based on first item keys (ignoring id)
            let columns = new Set();
            data.forEach(item => {
                Object.keys(item).forEach(key => {
                    if(key !== 'id') columns.add(key);
                });
            });
            
            const colArray = Array.from(columns);
            
            // Add ID column first
            theadRow.innerHTML += `<th>Document ID</th>`;
            colArray.forEach(col => {
                theadRow.innerHTML += `<th>${col.replace(/_/g, ' ').toUpperCase()}</th>`;
            });

            data.forEach(item => {
                const tr = document.createElement('tr');
                let rowHtml = `<td><span class="badge" style="background: rgba(255,255,255,0.1)">${item.id}</span></td>`;
                
                colArray.forEach(col => {
                    rowHtml += `<td>${item[col] || '-'}</td>`;
                });
                
                tr.innerHTML = rowHtml;
                tbody.appendChild(tr);
            });
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
