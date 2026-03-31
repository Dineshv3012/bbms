# 🩸 Blood Bank Management System (BBMS)

A robust, full-stack management system designed to streamline blood bank operations, from donor management to real-time inventory tracking and predictive analytics.

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)

## 🌟 Key Features

- **🔐 Secure Authentication**: Integrated user login and signup with password hashing.
- **📊 Real-time Dashboard**: Comprehensive overview of inventory status and recent activities.
- **🩸 Donor Management**: Manage donor records and blood groups.
- **📦 Inventory Tracking**: Monitor blood stock levels and expired units.
- **📝 Blood Requests**: Manage incoming requests from hospitals and patients.
- **👥 Staff Administration**: Manage staff permissions and access levels.
- **🔍 Analytics & Predictions**: Powered by `numpy` for trend analysis and demand forecasting.
- **📍 Blood Locator**: Locate compatible blood units across different centers.
- **📜 Activity Logs**: Full audit trail of all transactions and changes.

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **Database**: MySQL (via SQLAlchemy)
- **Frontend**: HTML5, Tailwind CSS, JavaScript
- **Forms**: Flask-WTF
- **Analytics**: NumPy
- **Styling**: Modern interactive design with glassmorphism and smooth animations.

## 🚀 Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Dineshv3012/bbms.git
   cd bbms
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Database Initialization**:
   The application uses MySQL by default (configured in `config.py`). Ensure your MySQL server is running and the database specified in the connection string exists.
   The app will automatically create necessary tables on the first run.

4. **Run the application**:
   ```bash
   python app.py
   ```
   Open [http://localhost:5000](http://localhost:5000) in your browser.

## 📂 Project Structure

```text
bbms/
├── app.py              # Main application entry point
├── models.py           # SQLAlchemy Database models
├── config.py           # App configuration settings
├── routes/             # Blueprint-based modular routes
├── utils/              # Utility functions and analytics
├── templates/          # HTML templates (Jinja2)
├── static/             # Assets (CSS/JS/Uploads)
└── requirements.txt    # Python dependencies
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.


##    Website Link
```bash
https://bbms-tau.vercel.app/
```
