# SUIVI Parcel Sending Service App

**SUIVI** is an online parcel sending service platform that connects **senders** with **riders** (and/or **parcel service companies**). Senders can request pickups, track deliveries, and conveniently complete transactions through integrated payment gateways. Riders (or courier companies) can manage assignments through a central dashboard, update parcel statuses, and communicate with users in real-time. Below are the two available implementations of SUIVI: **Flask** and **Django**.

---

## Table of Contents

1. [Features](#features)  
2. [System Requirements](#system-requirements)  
3. [Flask Version](#flask-version)  
   - [Key Technologies](#key-technologies---flask)  
   - [Project Structure](#project-structure---flask)  
   - [Installation](#installation---flask)  
   - [Database Setup](#database-setup---flask)  
   - [Running the Application](#running-the-application---flask)  
   - [Versioning](#versioning---flask)  
4. [Legal and Regulatory Considerations](#legal-and-regulatory-considerations)  
5. [License](#license)  
6. [Contact](#contact)  

---

## Features

1. **Homepage**  
   - A straightforward landing page that highlights the core services and functionalities.

2. **User Registration & Login**  
   - Senders (users) can register and log in to request pickups and manage their parcels.

3. **Parcel Sending Request Form**  
   - Users can fill out a form specifying the parcel details (size, weight, pickup/delivery locations).

4. **Riders & Parcel Service Companies Registration & Login**  
   - Riders and companies can manage their profiles, accept/reject deliveries, and track parcels in transit.

5. **Riders Dashboard**  
   - Tools to manage assigned pickups, track deliveries, update parcel status, and communicate with senders.

6. **Parcel Tracking**  
   - Real-time parcel status updates from pickup through to final delivery.

7. **Payment Integration**  
   - Seamless payment workflows using an integrated payment gateway.

8. **Rating and Feedback System**  
   - Users can rate and provide feedback on the services they received, aiding other users in decision-making.

9. **Mobile App Version**  
   - An Android version for on-the-go access to SUIVI's core features.

10. **Admin Panel**  
    - Centralized management of user accounts, company registrations, usage analytics, and issue resolution.

---

## System Requirements

- **Python 3.7+**  
- **PostgreSQL** (recommended)  
- **pip** or **pipenv** for managing Python dependencies  
- A suitable web server (for production deployment)  

---

## Flask Version

### Key Technologies - Flask

- **Flask** (Python web framework)  
- **SQLAlchemy** (database ORM)  
- **Flask-Migrate** (database migrations)  
- **PostgreSQL** (production-grade database)  
- **HTML/CSS/JavaScript** (frontend)  

### Project Structure - Flask

```bash
suivi/
├── Procfile
├── README.md
├── config.py
├── entry/
│   ├── __init__.py
│   ├── forms.py
│   ├── models.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── admin_routes.py
│   │   ├── auth_routes.py
│   │   ├── main_routes.py
│   │   ├── parcels.py
│   │   ├── password.py
│   │   └── rider_routes.py
│   ├── static/
│   │   ├── images/
│   │   ├── js/
│   │   └── styles/
│   ├── templates/
│   │   ├── *.html
│   └── sms_service.py
├── faqs.py
├── migrations/
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
├── requirements.txt
├── run.py
└── tailwind.config.js
```

### Installation - Flask

1. **Clone the repository** (or download the ZIP):

   ```bash
   git clone https://github.com/NjengaC/suivi.git
   cd suivi


2. Create and activate a virtual environment (recommended):
    ```bash
    python3 -m venv venv
    source venv/bin/activate     # On macOS/Linux
    venv\Scripts\activate.bat    # On Windows

    ```
3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
    Alternatively
    ```bash
    sudo ./flask_installs
    ```
    (Ensure flask_installs is executable and correctly references your environment.)
4. Login into postgresql and create the database
  ```bash
  sudo -u postgres psql
  ```
```bash
CREATE DATABASE suivi
\q
```
(Adjust as needed if you have different user privileges.)

5. Configure environment variables
    You may need to provide your database URI in an environment variable (e.g., DATABASE_URL):

    ```bash
    export DATABASE_URL="postgresql://postgres:password@localhost/suivi"
    ```
6. Navigate to the project's root directory and run the following commands to instantiate database.

   ```bash
   export FLASK_APP=run.py
   flask db init
   flask db migrate -m "Initial migration."
   flask db upgrade
   ```

## Running the Application - Flask
1. Start the Flask development server:

```bash
python3 run.py
```
2. Access the application in your browser:

```bash
http://127.0.0.1:8080
```
(Or whichever port is configured in your run.py.)

## Versioning - Flask
Current Version: 0.1 - Flask Framework
Future updates will increment version numbers accordingly.

## Legal and Regulatory Considerations

No legal and regulatory considerations until deployment!
