# 🔄 Restart Instructions - Backend Fixed!

## ✅ What Was Fixed

### Problem Identified:
Your actual CSV files have different column structures than expected:
- **Enrolment:** `age_0_5`, `age_5_17`, `age_18_greater` (not `Adult_Vol`, `Child_Vol`)
- **Demographic:** `demo_age_5_17`, `demo_age_17_` (not `Demographic_Vol`)
- **Biometric:** `bio_age_5_17`, `bio_age_17_` (not `Biometric_Vol`)

### What I Fixed:
✅ Updated backend to recognize your actual column names
✅ Added data aggregation by district and state
✅ Improved error handling and logging
✅ Enhanced frontend error messages

---

## 🚀 How to Restart

### Step 1: Stop Current Servers

**In Backend Terminal (Terminal 3):**
Press `Ctrl+C` to stop the backend server

**In Frontend Terminal (Terminal 2):**
Press `Ctrl+C` to stop the frontend server

### Step 2: Restart Backend

**In Terminal 3:**
```bash
cd /Users/sagarpatil/Work/Projects/Aadhaar_DRISHTI
source venv/bin/activate
cd backend
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 3: Restart Frontend

**In Terminal 2:**
```bash
cd /Users/sagarpatil/Work/Projects/Aadhaar_DRISHTI
npm start
```

Browser should auto-open to `http://localhost:3000`

---

## 🧪 Test Again

1. **Upload Files:**
   - Drag one or more CSV files from your `Datasets/` folder
   - You can upload:
     - Just enrolment file
     - Enrolment + Demographic
     - Enrolment + Demographic + Biometric
     - Any combination

2. **Click "Run Tri-Shield Analysis"**

3. **Check Console:**
   - Open browser Developer Tools (F12)
   - Click "Console" tab
   - You should see logs like:
     ```
     Uploading 1 file(s) to backend...
     - api_data_aadhar_enrolment_0_500000.csv (12345.67 KB)
     Sending request to: http://localhost:8000/analyze_trishield
     Response received: {success: true, data: {...}}
     ✓ Analysis complete: {total_threats: 45, ...}
     ```

4. **Check Backend Terminal:**
   - You should see:
     ```
     === Starting Tri-Shield Analysis ===
     Received 1 file(s)
     ✓ Identified ENROLMENT data: ... (1050 districts)
     ✓ Loaded 1 dataset(s)
     ✓ Analysis complete - Found 45 threats
     === Analysis Complete ===
     ```

---

## 🎯 What to Expect

After the fix, you should see:
- ✅ Summary cards with threat counts
- ✅ Bar chart showing top 5 risky districts
- ✅ Tables with detected fraud cases
- ✅ PDF download button

---

## 🐛 If Still Not Working

### Check 1: Backend Connection
Open browser console and look for errors:
- **"Network Error"** → Backend not running
- **"404"** → Wrong URL
- **"500"** → Server error (check backend terminal)

### Check 2: CORS Issues
If you see CORS errors in console:
1. Make sure backend shows: `CORS enabled`
2. Frontend should be on port 3000
3. Backend should be on port 8000

### Check 3: File Format
Make sure your CSV files have these columns:
- Enrolment: `date,state,district,pincode,age_0_5,age_5_17,age_18_greater`
- Demographic: `date,state,district,pincode,demo_age_5_17,demo_age_17_`
- Biometric: `date,state,district,pincode,bio_age_5_17,bio_age_17_`

---

## 📊 Verification Test

Run this to verify data processing works:
```bash
cd /Users/sagarpatil/Work/Projects/Aadhaar_DRISHTI
source venv/bin/activate
python test_backend.py
```

Should show:
```
✓ Enrolment Data Loaded: 500000 rows
✓ Demographic Data Loaded: 500000 rows
✓ Biometric Data Loaded: 500000 rows
✅ All data files can be processed correctly!
```

---

## 🎉 Once Working

You should see real fraud detection results based on:
- **Shield 1:** Districts with >90% adult enrollment
- **Shield 2:** Demographic/Biometric ratio discrepancies
- **Shield 3:** Child-only enrollments (ghost children)

---

**Need to restart? Follow these 3 steps:**
1. Stop both servers (Ctrl+C)
2. Restart backend with updated code
3. Restart frontend
4. Upload and analyze!
