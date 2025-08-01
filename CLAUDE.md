# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Youth Cognitive Assessment Platform (认知能力评估平台) - a full-stack application that provides cognitive ability testing for children including reading fluency, attention screening, and calculation fluency tests.

**Architecture:**
- **Frontend**: Vue 3 + Element Plus + Vite
- **Backend**: FastAPI + SQLModel + MySQL
- **Database**: MySQL 8.0 with Docker support
- **Package Management**: Frontend (npm/pnpm), Backend (uv/pip)

## Essential Commands

### Frontend Development
```bash
# Development server with hot reload
npm run dev

# Build for production
npm run build

# Preview built application
npm run preview

# Start both frontend and backend concurrently
npm start
```

### Backend Development
```bash
# Navigate to backend directory
cd backend

# Start FastAPI server (development mode with auto-reload)
python run.py
# or
python main.py

# Initialize database and load test data
python init_db.py

# Run tests
pytest

# Code quality tools (optional dependencies)
black .           # Format code
isort .           # Sort imports
flake8 .          # Lint code
mypy .            # Type checking
```

### Database Setup
```bash
# Start MySQL 8.0 in Docker
docker run -d --name mysql-8-app -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=meng123456 \
  -e MYSQL_DATABASE=appdb \
  -e MYSQL_USER=meng \
  -e MYSQL_PASSWORD=meng123456 \
  -v mysql_data:/var/lib/mysql \
  mysql:8.0.39 \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_unicode_ci \
  --default-authentication-plugin=mysql_native_password
```

### Package Management
```bash
# Frontend dependencies
npm install
# or
pnpm install

# Backend dependencies (using uv - preferred)
uv pip install -r pyproject.toml
# or traditional pip
pip install -e .
```

## Code Architecture

### Backend Structure
- **Modular Design**: Each test type (reading fluency, attention, calculation) is a separate app module
- **Apps Directory**: `/backend/apps/` contains modules like `reading_fluency/`, `attention_test/`, `calculation_test/`
- **Module Pattern**: Each app has `models.py` (SQLModel), `router.py` (FastAPI routes), `service.py` (business logic)
- **Database**: SQLModel ORM with MySQL, base models in `database.py`
- **Configuration**: Centralized in `config.py` with Pydantic settings

### Frontend Structure
- **Vue 3 Composition API**: Modern Vue.js with `<script setup>` syntax
- **Component Library**: Element Plus for UI components
- **Routing**: Vue Router for SPA navigation
- **Experiment Framework**: jsPsych integration for psychological experiments

### Key Integration Points
- **API Proxy**: Vite dev server proxies `/api/*` to FastAPI backend on port 3000
- **Static Files**: FastAPI serves built frontend from `/dist` directory
- **Database Models**: SQLModel provides type-safe database operations
- **Test Data**: CSV files in `/backend/data/` for experiment stimuli

### Testing Systems
1. **Reading Fluency** (`reading_fluency/`): Word/sentence reading tasks
2. **Attention Test** (`attention_test/`): Visual attention screening
3. **Calculation Test** (`calculation_test/`): Math fluency assessment
4. **OralReadingFluency Test**(`oral_reading_fluency/`): oral reading fluency assessment

## Development Notes

- **Database Initialization**: Run `python init_db.py` to create tables and load test data
- **API Documentation**: Available at `http://localhost:3000/api/docs` when backend is running
- **Frontend Development**: Use `npm run dev` for hot-reload development server
- **Production Build**: Frontend builds to `/dist`, served by FastAPI as static files
- **Environment**: Python 3.10+, Node.js 16+, MySQL 8.0+

## File Locations

- **Backend Entry**: `backend/main.py` or `backend/run.py`
- **Frontend Entry**: `src/main.js`
- **Database Config**: `backend/config.py`
- **Test Data**: `backend/data/*.csv`
- **Components**: `src/components/`
- **API Routes**: `backend/apps/*/router.py`