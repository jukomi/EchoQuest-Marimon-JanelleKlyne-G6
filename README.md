# EchoQuest

A web application for tracking sachet-plastic avoidance and public-transport carbon savings among Filipino university students.

- **Developer**: Janelle Klyne R. Marimon
- **Course & Section**: IT317 - IM2 | Section G6
- **School**: Cebu Institute of Technology - University
- **Repository**: https://github.com/jukomi/EchoQuest-Marimon-JanelleKlyne-G6

---

## Core Feature: Quest Logger (Vertical Slice)

In Project Development 2, the Quest Logger feature was implemented as a full vertical slice across all layers:

1. **Database (Supabase / PostgreSQL)**:
   - `ActivityType`: Table of loggable habits (single-use sachets, jeepney, tricycle, bus, LRT/MRT) with per-log and daily caps.
   - `EmissionFactor`: Versioned conversion factors based on Philippine studies (GAIA, UNEP, DENR, DOTr).
   - `HabitLog`: Stores user logs with quantity, date, optional notes/photo proof, and computed savings (`plastic_saved_g`, `co2_saved_kg`).

2. **Backend (Django)**:
   - CRUD views (`log_list_view`, `log_create_view`, `log_detail_view`, `log_update_view`, `log_delete_view`).
   - `HabitLogForm` with validation for positive numbers, integer sachet counts, single log caps, daily limits, 7-day date restrictions, and image size checks.
   - Automatic calculation of saved plastic and CO2 on save based on the active emission factor for that date.

3. **Frontend (Django Templates + Bootstrap)**:
   - `templates/accounts/log_list.html`: Table of habit logs with total savings cards.
   - `templates/accounts/log_form.html`: Form to add or edit habit logs.
   - `templates/accounts/log_detail.html`: View details, notes, proof image, and savings breakdown.
   - `templates/accounts/log_confirm_delete.html`: Delete confirmation page.
   - Student & Admin Dashboards updated with live savings metrics.

---

## Setup and Running Locally

1. Clone the repo:
   ```bash
   git clone https://github.com/jukomi/EchoQuest-Marimon-JanelleKlyne-G6.git
   cd EchoQuest-Marimon-JanelleKlyne-G6
   ```

2. Create virtual environment and install packages:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Setup `.env` file:
   ```ini
   SECRET_KEY=your-secret-key
   DEBUG=True
   DB_NAME=postgres
   DB_USER=postgres
   DB_PASSWORD=your-db-password
   DB_HOST=your-supabase-host
   DB_PORT=5432
   ```

4. Run migrations and seed default data:
   ```bash
   python manage.py migrate
   python manage.py seed_data
   ```

5. Run server:
   ```bash
   python manage.py runserver
   ```
   Open `http://127.0.0.1:8000/` in your browser.

---

## Test Accounts

- **Admin**: `admin@echoquest.ph` | `AdminPass123!`
- **Student**: `student@cit.edu` | `StudentPass123!`

---

## Git Branches

- `main`: Clean release branch
- `develop`: Integration branch
- `feature/habit-models-and-factors`: Database models and seed command (merged to develop)
- `feature/quest-logger-ui`: CRUD views, forms, templates, and dashboard updates (merged to develop)
