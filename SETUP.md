# LITE - Linux Investigation & Triage Environment
## Development Setup Guide

### Quick Start

#### Option 1: Using Batch Script (Windows)
```bash
# Double-click or run from command prompt
start_lite.bat
```

#### Option 2: Using PowerShell Script (Recommended)
```powershell
# Run from PowerShell
.\start_lite.ps1
```

### Manual Setup (First Time)

1. **Create Virtual Environment**
   ```bash
   python -m venv venv
   ```

2. **Activate Virtual Environment**
   ```bash
   # Windows Command Prompt
   venv\Scripts\activate.bat
   
   # Windows PowerShell
   .\venv\Scripts\Activate.ps1
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Application**
   ```bash
   python app.py
   ```

### Environment Configuration

The application uses a `.env` file for configuration. Key settings include:

- **FLASK_DEBUG**: Enable/disable debug mode
- **SECRET_KEY**: Flask secret key for sessions
- **DATABASE_URL**: Database connection string (SQLite by default)
- **MAX_CONTENT_LENGTH**: Maximum file upload size
- **UPLOAD_FOLDER**: Directory for uploaded files

### Database

- **Development**: Uses SQLite (`lite_dev.db`) - no setup required
- **Production**: Configure PostgreSQL in `.env` file

### File Structure

```
LITE/
├── .env                    # Environment variables
├── start_lite.bat         # Windows batch startup script
├── start_lite.ps1         # PowerShell startup script
├── app.py                 # Main application entry point
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── lite_dev.db           # SQLite database (auto-created)
├── app/
│   ├── routes/           # Flask route handlers
│   ├── templates/        # HTML templates
│   ├── static/          # CSS, JS, images
│   ├── utils/           # Utility functions
│   ├── models.py        # Database models
│   ├── database.py      # Database operations
│   └── ingestion.py     # Data ingestion logic
└── uploads/             # Uploaded case files
```

### Troubleshooting

#### Common Issues

1. **Virtual Environment Not Found**
   - Run: `python -m venv venv`
   - Then activate and install dependencies

2. **Dependencies Missing**
   - Run: `pip install -r requirements.txt`

3. **Database Connection Error**
   - Check `.env` file configuration
   - For development, SQLite is used automatically

4. **Port Already in Use**
   - Change port in `app.py` or stop other Flask applications

#### Getting Help

- Check the application logs in the terminal
- Ensure Python 3.8+ is installed
- Verify all dependencies are installed correctly

### Development Workflow

1. **Start Development Server**
   ```bash
   .\start_lite.ps1  # or start_lite.bat
   ```

2. **Access Application**
   - Open browser to: http://127.0.0.1:5000

3. **Stop Server**
   - Press `Ctrl+C` in terminal

4. **Make Changes**
   - Edit files in `app/` directory
   - Server auto-reloads in debug mode

### Production Deployment

1. **Set Environment Variables**
   ```bash
   FLASK_ENV=production
   FLASK_DEBUG=0
   DATABASE_URL=postgresql://user:pass@host:port/db
   ```

2. **Use Production WSGI Server**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

### Security Notes

- Change `SECRET_KEY` in production
- Use PostgreSQL for production databases
- Configure proper file upload limits
- Enable HTTPS in production
- Review and update dependencies regularly