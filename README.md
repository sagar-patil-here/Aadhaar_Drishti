# 🛡️ Aadhaar DRISHTI

**Digital Risk Identification System for High-Threat Infiltration**

A comprehensive fraud detection dashboard for analyzing Aadhaar enrollment datasets to detect infiltration, identity laundering, and ghost children fraud patterns.

---

## 🚀 Project Overview

Aadhaar DRISHTI is a full-stack security system built for government hackathons that analyzes Aadhaar enrollment data using three intelligent fraud detection algorithms (Tri-Shield Analysis):

1. **Shield 1: Migration Radar** - Detects suspicious infiltration patterns
2. **Shield 2: Laundering Detector** - Identifies potential identity theft
3. **Shield 3: Ghost Child Scanner** - Uncovers subsidy fraud schemes

### ✨ Key Features

- **Multi-file CSV Upload**: Drag-and-drop interface for uploading multiple datasets
- **Automatic Dataset Recognition**: Intelligent identification of enrolment, demographic, and biometric data
- **Real-time Analysis**: Fast, async processing using FastAPI
- **Interactive Visualizations**: Charts and tables showing high-risk districts
- **PDF Report Generation**: Official downloadable investigation reports
- **Modern UI**: Beautiful, responsive design with Tailwind CSS

---

## 🏗️ Tech Stack

### Frontend
- **React.js** - UI framework
- **Tailwind CSS** - Styling
- **Recharts** - Data visualization
- **Axios** - API communication
- **React Dropzone** - File upload

### Backend
- **Python FastAPI** - Fast, async API framework
- **Pandas** - Data processing and analysis
- **FPDF** - PDF report generation
- **Uvicorn** - ASGI server

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** (v16 or higher) - [Download](https://nodejs.org/)
- **Python** (v3.8 or higher) - [Download](https://www.python.org/)
- **npm** or **yarn** - Comes with Node.js

---

## 🔧 Installation & Setup

### Step 1: Clone or Navigate to Project Directory

```bash
cd /Users/sagarpatil/Work/Projects/Aadhaar_DRISHTI
```

### Step 2: Backend Setup

1. **Create a virtual environment** (recommended):

```bash
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

2. **Install Python dependencies**:

```bash
pip install -r requirements.txt
```

3. **Start the backend server**:

```bash
cd backend
python main.py
```

Or using uvicorn directly:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

✅ Backend should now be running at: **http://localhost:8000**

### Step 3: Frontend Setup

1. **Install Node.js dependencies**:

```bash
npm install
```

2. **Start the React development server**:

```bash
npm start
```

✅ Frontend should now be running at: **http://localhost:3000**

---

## 🎯 Usage Guide

### 1. Upload Datasets

- Navigate to **http://localhost:3000**
- Drag and drop your CSV files or click to browse
- Upload any combination of:
  - **Enrolment Data** (contains `Adult_Vol`, `Child_Vol`)
  - **Demographic Data** (contains `Demographic_Vol`)
  - **Biometric Data** (contains `Biometric_Vol`)

### 2. Run Analysis

- Click the **"🛡️ Run Tri-Shield Analysis"** button
- Wait for processing (typically 2-5 seconds)
- View results in real-time

### 3. Review Results

The dashboard displays:
- **Summary Cards**: Total threats, infiltration cases, laundering cases, ghost children
- **Top 5 High-Risk Districts**: Interactive bar chart
- **Detailed Tables**: Separate tables for each shield's findings

### 4. Download PDF Report

- Click **"📄 Download Official PDF Report"**
- A comprehensive PDF investigation report will be generated and downloaded
- Report includes all findings, tables, and risk assessments

---

## 📊 Tri-Shield Analysis Logic

### Shield 1: Migration Radar (Infiltration Detection)

**Input**: Enrolment Data  
**Rule**: `Adult_Ratio > 0.90 AND Total_Volume > 100`  
**Flags**: Districts with abnormally high adult-to-child ratios

```python
Adult_Ratio = Adult_Vol / (Adult_Vol + Child_Vol)
if Adult_Ratio > 0.90 and Total_Vol > 100:
    Flag as "High Risk Infiltration"
```

### Shield 2: Laundering Detector (Identity Theft)

**Input**: Demographic + Biometric Data  
**Rule**: `Laundering_Ratio > 20`  
**Flags**: Discrepancies between demographic and biometric enrollments

```python
Laundering_Ratio = Demographic_Vol / Biometric_Vol
if Laundering_Ratio > 20:
    Flag as "Identity Laundering"
```

### Shield 3: Ghost Child Scanner (Subsidy Fraud)

**Input**: Enrolment Data  
**Rule**: `Child_Vol > 500 AND Adult_Vol == 0`  
**Flags**: Suspicious child-only enrollments

```python
if Child_Vol > 500 and Adult_Vol == 0:
    Flag as "Ghost Children Fraud"
```

---

## 📁 Project Structure

```
Aadhaar_DRISHTI/
├── backend/
│   └── main.py                 # FastAPI application with all endpoints
├── src/
│   ├── App.js                  # Main React component
│   ├── Dashboard.js            # Main dashboard UI
│   ├── index.js                # React entry point
│   ├── index.css               # Tailwind CSS imports
│   └── App.css                 # Custom styles
├── public/
│   └── index.html              # HTML template
├── Datasets/                   # Your CSV datasets
│   ├── api_data_aadhar_biometric/
│   ├── api_data_aadhar_demographic/
│   └── api_data_aadhar_enrolment/
├── requirements.txt            # Python dependencies
├── package.json                # Node.js dependencies
├── tailwind.config.js          # Tailwind configuration
├── postcss.config.js           # PostCSS configuration
└── README.md                   # This file
```

---

## 🔌 API Endpoints

### POST `/analyze_trishield`

Analyzes uploaded CSV files using Tri-Shield algorithms.

**Request**: Multipart form data with CSV files  
**Response**: JSON with analysis results

```json
{
  "success": true,
  "message": "Tri-Shield Analysis Complete",
  "data": {
    "shield1_results": [...],
    "shield2_results": [...],
    "shield3_results": [...],
    "summary": {
      "total_threats": 45,
      "infiltration_cases": 20,
      "laundering_cases": 15,
      "ghost_children_cases": 10
    }
  }
}
```

### POST `/generate_report`

Generates a PDF investigation report.

**Request**: JSON with analysis results  
**Response**: PDF file (application/pdf)

### GET `/`

Health check endpoint.

---

## 🐛 Troubleshooting

### Backend Issues

**Port 8000 already in use:**
```bash
# Kill existing process
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn backend.main:app --reload --port 8001
```

**Module not found errors:**
```bash
pip install --upgrade -r requirements.txt
```

### Frontend Issues

**Port 3000 already in use:**
```bash
# Will prompt to use a different port automatically
# Or manually specify:
PORT=3001 npm start
```

**Dependency issues:**
```bash
rm -rf node_modules package-lock.json
npm install
```

**CORS errors:**
- Ensure backend is running on port 8000
- Check CORS settings in `backend/main.py`

---

## 🚀 Production Deployment

### Backend (FastAPI)

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend (React)

```bash
# Build for production
npm run build

# Serve with a static server
npx serve -s build -l 3000
```

---

## 📝 Sample Data Format

### Enrolment Data CSV
```csv
District,State,Adult_Vol,Child_Vol
Mumbai,Maharashtra,15000,1000
Delhi,Delhi,12000,800
```

### Demographic Data CSV
```csv
District,State,Demographic_Vol
Mumbai,Maharashtra,16000
Delhi,Delhi,12500
```

### Biometric Data CSV
```csv
District,State,Biometric_Vol
Mumbai,Maharashtra,15800
Delhi,Delhi,12300
```

---

## 🔐 Security Considerations

- This is a demonstration project for hackathons
- In production, add authentication and authorization
- Implement rate limiting on API endpoints
- Use HTTPS for all communications
- Encrypt sensitive data at rest and in transit
- Add input validation and sanitization

---

## 🤝 Contributing

This is a hackathon project. For improvements:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

This project is created for educational and hackathon purposes.

---

## 👥 Team

Built for Government Security Hackathon

---

## 🎓 Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Pandas Guide](https://pandas.pydata.org/docs/)
- [Recharts Examples](https://recharts.org/)

---

## ⚡ Quick Start (TL;DR)

```bash
# Terminal 1 - Backend
pip install -r requirements.txt
cd backend && python main.py

# Terminal 2 - Frontend
npm install
npm start

# Open browser: http://localhost:3000
```

---

## 📞 Support

For issues or questions:
- Check the troubleshooting section
- Review API endpoint documentation
- Ensure all dependencies are installed correctly

---

**🛡️ Stay Vigilant. Stay Secure. DRISHTI is watching.**
