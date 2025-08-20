# Linux Investigation Triage Environment (LITE)

A Flask-based web application for digital forensics case management and artifact analysis. LITE provides a centralized platform for managing forensic investigations, ingesting JSON artifacts, and visualizing case data.

## Features

- **Case Management**: Create and manage traige cases
- **Artifact Ingestion**: Import and process JSON triage artifacts
- **Data Visualization**: Interactive dashboards and charts
- **PostgreSQL Backend**: Robust database for forensic data storage
- **Web Interface**: User-friendly web-based interface

## Prerequisites

- Python 3.8+
- PostgreSQL 14+
- Windows PowerShell (for setup scripts)

## Quick Start

### 1. Database Setup

1. Install PostgreSQL on your system
2. Ensure PostgreSQL service is running
3. Run the database setup script:
   ```powershell
   .\setup_postgres.ps1
   ```
4. Enter your PostgreSQL password when prompted

### 2. Application Setup

1. Clone the repository
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure environment variables in `.env`:
   ```
   POSTGRES_PASSWORD=your_postgres_password
   ```
4. Start the application:
   ```powershell
   .\start_lite.ps1
   ```

## Configuration

The application uses PostgreSQL exclusively. Configure database connection in `.env`:

```
DATABASE_URL=postgresql://postgres:password@localhost:5432/lite_forensics
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=lite_forensics
```

## Usage

1. Access the web interface at `http://localhost:5000`
2. Create a new forensic case
3. Upload JSON artifact files
4. View case dashboard and analysis

## Project Structure

- `app/` - Flask application modules
- `app/routes/` - Web route handlers
- `app/templates/` - HTML templates
- `app/static/` - CSS, JavaScript, images
- `setup_postgres.sql` - Database schema
- `database_schema.sql` - Table definitions

## Support

For setup issues or questions, refer to `SETUP.md` for detailed installation instructions.