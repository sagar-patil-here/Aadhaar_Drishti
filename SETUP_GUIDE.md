# 🚀 Quick Setup Guide - Aadhaar DRISHTI

## ⚡ Fastest Way to Get Started

### Option 1: Using Helper Scripts (Recommended)

**Step 1: Make scripts executable**
```bash
chmod +x start_backend.sh start_frontend.sh
```

**Step 2: Start Backend (Terminal 1)**
```bash
./start_backend.sh
```

**Step 3: Start Frontend (Terminal 2)**
```bash
./start_frontend.sh
```

### Option 2: Manual Setup

**Terminal 1 - Backend:**
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start server
cd backend && python main.py
```

**Terminal 2 - Frontend:**
```bash
# Install dependencies
npm install

# Start development server
npm start
```

## ✅ Verification

1. Backend running at: **http://localhost:8000**
   - Visit this URL to see: `{"message": "Aadhaar DRISHTI API is running"}`

2. Frontend running at: **http://localhost:3000**
   - You should see the DRISHTI dashboard

## 📊 Test with Sample Data

1. Navigate to your `Datasets/` folder
2. Select CSV files from:
   - `api_data_aadhar_enrolment/`
   - `api_data_aadhar_demographic/`
   - `api_data_aadhar_biometric/`
3. Drag and drop them into the dashboard
4. Click "🛡️ Run Tri-Shield Analysis"
5. View results and download PDF report

## 🐛 Common Issues

### Port Already in Use

**Backend (8000):**
```bash
lsof -ti:8000 | xargs kill -9
```

**Frontend (3000):**
```bash
lsof -ti:3000 | xargs kill -9
```

### Module Not Found

**Python:**
```bash
pip install --upgrade -r requirements.txt
```

**Node:**
```bash
rm -rf node_modules package-lock.json
npm install
```

## 🎯 What to Expect

After successful setup, you'll have:
- ✅ A fully functional fraud detection dashboard
- ✅ Real-time CSV analysis capabilities
- ✅ Interactive data visualizations
- ✅ PDF report generation
- ✅ Professional government-grade UI

## 📞 Need Help?

Check the main `README.md` for detailed documentation and troubleshooting.

---

**Ready to detect fraud? Let's go! 🛡️**
