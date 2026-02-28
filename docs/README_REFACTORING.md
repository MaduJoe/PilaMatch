# Frontend Code Refactoring Documentation

## Overview
The PilaMatch frontend has been refactored from a single 2000+ line `app.py` file into a modular structure for better maintainability and organization.

## New Directory Structure

```
frontend/
├── app.py                    # Main application entry point (200 lines)
├── app_original_backup.py    # Backup of original monolithic file
│
├── pages/                    # Page modules for each step
│   ├── __init__.py
│   ├── auth.py              # Login/Signup page
│   ├── step1_profile.py     # Profile completion
│   ├── step2_jobs.py        # Job finding/creation
│   ├── step3_offers.py      # Offers/Applications
│   ├── step4_contracts.py   # Contract management
│   └── step5_complete.py    # Completion & Reviews
│
├── components/              # Reusable UI components
│   ├── __init__.py
│   ├── progress.py         # Progress bar and navigation
│   └── map.py             # Kakao map display
│
├── utils/                  # Utilities and constants
│   ├── __init__.py
│   ├── constants.py       # App constants (steps, regions, etc.)
│   └── helpers.py         # Helper functions
│
└── api_client.py          # API client (existing)
```

## Module Breakdown

### Main App (`app.py`)
- **Lines**: ~200 (reduced from 2000+)
- **Responsibilities**:
  - Application entry point
  - Authentication check
  - Page routing
  - Header rendering

### Page Modules (`pages/`)

#### `auth.py`
- Login and signup forms
- User authentication flow

#### `step1_profile.py`
- Instructor/Studio profile forms
- Phone/Business verification
- Premium membership management
- Deposit management

#### `step2_jobs.py`
- `render_find_jobs_step()`: Job browsing for instructors
- `render_create_job_step()`: Job posting for studios
- Matching score calculation display

#### `step3_offers.py`
- `render_offers_step()`: Offer management for instructors
- `render_applicants_step()`: Application review for studios
- Offer sending/accepting flow

#### `step4_contracts.py`
- Contract listing and management
- Dual-signature implementation
- Contract status tracking
- No-show reporting

#### `step5_complete.py`
- Completed contracts display
- Review writing/editing
- Rating system
- Settlement information

### Component Modules (`components/`)

#### `progress.py`
- `render_progress_bar()`: Visual progress tracker
- `render_step_navigation()`: Step navigation buttons

#### `map.py`
- `render_kakao_map()`: Kakao Map integration for region display

### Utility Modules (`utils/`)

#### `constants.py`
- `INSTRUCTOR_STEPS`, `STUDIO_STEPS`: Step definitions
- `SEOUL_REGIONS`: Seoul district coordinates
- `RATE_PRESETS`: Hourly rate options
- `CONTRACT_TERMS`: Contract terms text

#### `helpers.py`
- `get_client()`: Get API client instance
- `logout()`: Clear session
- `init_session_state()`: Initialize session variables
- `get_user_progress()`: Calculate user's current step

## Benefits of Refactoring

1. **Maintainability**: Each module has a single responsibility
2. **Readability**: Easier to find and understand specific functionality
3. **Reusability**: Components can be reused across pages
4. **Testing**: Individual modules can be tested separately
5. **Collaboration**: Multiple developers can work on different modules
6. **Performance**: Smaller files load and parse faster

## Migration Notes

- The original `app.py` has been backed up as `app_original_backup.py`
- All functionality has been preserved
- No changes to Docker configuration required
- Frontend continues to run on port 8501

## Usage

No changes required for running the application:

```bash
docker-compose up frontend
```

## Future Improvements

1. Add unit tests for individual modules
2. Create shared form components
3. Implement error boundary components
4. Add module-level documentation
5. Consider using Streamlit's multipage app feature

## Code Statistics

| File | Lines | Description |
|------|-------|-------------|
| Original app.py | 2000+ | Monolithic file |
| New app.py | ~200 | Main orchestrator |
| step1_profile.py | ~350 | Profile management |
| step2_jobs.py | ~300 | Job management |
| step3_offers.py | ~400 | Offer management |
| step4_contracts.py | ~450 | Contract management |
| step5_complete.py | ~350 | Review management |
| **Total** | ~2050 | Modular structure |

The slight increase in total lines is due to:
- Module imports
- Better code organization
- Improved documentation