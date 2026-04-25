document.addEventListener('DOMContentLoaded', () => {
    const currentDeptSelect = document.getElementById('current_dept');
    const preferencesContainer = document.getElementById('preferences-container');
    
    if (currentDeptSelect) {
        currentDeptSelect.addEventListener('change', handleDepartmentChange);
    }

    const allDepts = ['CSE', 'CSE(AIML)', 'ENTC', 'CIVIL', 'MECHANICAL'];
    
    function handleDepartmentChange(e) {
        const currentDept = e.target.value;
        preferencesContainer.style.display = 'block';
        
        // Determine rules
        // CSE and CSE(AIML) get 3 choices max, and no 4th preference
        const isCseRelated = currentDept === 'CSE' || currentDept === 'CSE(AIML)';
        
        const pref4Group = document.getElementById('pref-4-group');
        const pref4Select = document.getElementById('pref-4-select');
        
        if (isCseRelated) {
            pref4Group.style.display = 'none';
            pref4Select.removeAttribute('required');
        } else {
            pref4Group.style.display = 'flex';
            pref4Select.setAttribute('required', 'true');
        }

        // Available departments excluding the current one
        const availableOptions = allDepts.filter(d => d !== currentDept);
        
        // Populate all preference dropdowns
        const prefSelects = document.querySelectorAll('.pref-select');
        prefSelects.forEach((select, index) => {
            // Keep the default disabled option
            select.innerHTML = `<option value="" disabled selected>Select Pref ${index + 1}</option>`;
            
            availableOptions.forEach(opt => {
                const optionElement = document.createElement('option');
                optionElement.value = opt;
                optionElement.textContent = opt;
                select.appendChild(optionElement);
            });
            
            // Add event listener to prevent duplicate selections across dropdowns
            select.removeEventListener('change', updateAvailableChoices);
            select.addEventListener('change', updateAvailableChoices);
        });
    }

    function updateAvailableChoices() {
        // Collect currently selected values
        const selectedValues = [];
        const prefSelects = document.querySelectorAll('.pref-select');
        
        prefSelects.forEach(select => {
            if (select.value && select.parentElement.style.display !== 'none') {
                selectedValues.push(select.value);
            }
        });

        // Disable options that are already selected in OTHER dropdowns
        prefSelects.forEach(select => {
            const options = select.querySelectorAll('option');
            options.forEach(opt => {
                if (opt.value === "") return; // Skip placeholder
                
                // If it's selected in another dropdown, disable it
                if (selectedValues.includes(opt.value) && select.value !== opt.value) {
                    opt.disabled = true;
                } else {
                    opt.disabled = false;
                }
            });
        });
    }
});
