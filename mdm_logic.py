import pandas as pd

def map_column_to_branch(col_name):
    # Maps column headers from the excel file to the standard branch keys
    col_name_upper = col_name.strip().upper()
    if 'CSE (AIML)' in col_name_upper or 'AIML' in col_name_upper:
        return 'AIML'
    elif 'CSE' in col_name_upper:
        return 'CSE'
    elif 'ETC' in col_name_upper or 'ENTC' in col_name_upper:
        return 'ENTC'
    elif 'MECH' in col_name_upper:
        return 'MECHANICAL'
    elif 'CIVIL' in col_name_upper:
        return 'CIVIL'
    return None

def seat_allotment(df):
    # Input is now a DataFrame directly

    # Ensure 'Total Marks' exists, if not we cannot sort
    if 'Total Marks' in df.columns:
        # Sort students by Total Marks in descending order, so higher scorers get preference
        df_sorted = df.sort_values(by='Total Marks', ascending=False).reset_index(drop=True)
    else:
        # If no Total Marks column is found, preserve original order
        df_sorted = df.copy()

    # Branch seat capacities
    seats = {
        'CSE': 120,
        'ENTC': 70,
        'AIML': 70,
        'CIVIL': 70,
        'MECHANICAL': 70
    }

    # Initialize seat allotment columns
    df_sorted['Allocated Minor'] = ''
    df_sorted['Seat Allotted'] = False
    df_sorted['Preference Used'] = '-'
    df_sorted['Status'] = 'WAITLISTED'

    # Keep track of how many seats have been allotted per branch
    allotted_counts = {branch: 0 for branch in seats.keys()}

    # Assign seats based on student preferences
    for i in range(len(df_sorted)):
        # Extract the student's preferences from the row
        student_prefs = []
        for col in df_sorted.columns:
            col_upper = col.strip().upper()
            val = str(df_sorted.at[i, col]).strip().upper()
            
            # Case 1: Web format - Column is "PREFERENCE 1", Value is "CSE"
            if col_upper.startswith("PREFERENCE"):
                try:
                    pref_num = int(col_upper.replace("PREFERENCE", "").strip())
                    branch_key = map_column_to_branch(val)
                    if branch_key:
                        student_prefs.append((pref_num, branch_key))
                except ValueError:
                    continue
            
            # Case 2: Excel format - Column is "CSE", Value is "PREFERENCE 1"
            elif val.startswith("PREFERENCE"):
                try:
                    pref_num = int(val.replace("PREFERENCE", "").strip())
                    if pref_num > 0:
                        branch_key = map_column_to_branch(col)
                        if branch_key:
                            student_prefs.append((pref_num, branch_key))
                except ValueError:
                    continue
        
        # Sort preferences so we try 'PREFERENCE 1' first, then 'PREFERENCE 2', etc.
        student_prefs.sort(key=lambda x: x[0])


        # Try to allocate a seat based on ordered preferences
        for pref_num, desired_branch in student_prefs:
            if allotted_counts[desired_branch] < seats[desired_branch]:
                df_sorted.at[i, 'Allocated Minor'] = desired_branch
                df_sorted.at[i, 'Seat Allotted'] = True
                df_sorted.at[i, 'Preference Used'] = f"PREFERENCE {pref_num}"
                df_sorted.at[i, 'Status'] = 'ALLOCATED'
                allotted_counts[desired_branch] += 1
                break  # Stop checking further preferences once a seat is allotted

    # Students who don't get seats remain with empty branch and Seat Allotted = False
    return df_sorted
