<div align="center">

🧠 Cognitive Stress Monitoring & Learning Support System

An adaptive cognitive assessment and learning-support platform that combines timed cognitive testing, performance tracking, physiological stress data, and personalized learning insights.






Cognitive Assessment • Stress-Aware Analysis • Learning Support • Longitudinal Tracking

</div>

📌 Overview

The Cognitive Stress Monitoring & Learning Support System is a student-focused platform designed to bring cognitive assessment, performance analytics, physiological stress information, and learning support into one workflow.

The software provides a structured examination environment with Exam and Practice modes, Foundation and Advanced levels, timed questions, question navigation, automatic submission, performance history, and domain-focused learning resources.

The broader research direction extends this software workflow toward an adaptive embedded system that can combine physiological signals such as heart rate / HRV and temperature with short cognitive interaction tests. The accompanying patent specification describes individualized baselines, temporal trend analysis, adaptive thresholds, and closed-loop visual/audio feedback for cognitive overload and recovery.

Important: The web application and the embedded-system concept are related parts of the overall project. The patent describes the broader hardware architecture; the current public software repository documents the implemented assessment, data, and learning-support workflow.

🎯 Problem Statement

Traditional online assessments usually focus on the final score. They may not capture enough information about:

response speed and time spent on questions

performance patterns across repeated attempts

which cognitive domains need additional practice

changes in performance during a test

relationships between physiological signals and cognitive workload

stress-related patterns that occur during specific questions

This project addresses that gap by bringing assessment + timing + historical performance + optional physiological information + learning resources into a unified system.

✨ Key Features

Feature

Description

🔐 Supabase Authentication

Username/password signup and login with PBKDF2-SHA256 password hashing

🧪 Exam Mode

Controlled, timed assessment workflow

📝 Practice Mode

Practice-oriented assessment workflow

🎯 Foundation & Advanced

Two assessment levels

⏱️ Timed Testing

Countdown timer, progress tracking, and automatic submission

🧭 Question Palette

Direct navigation and visual question status

🖼️ Image-Based Questions

Supports visual and multiple-choice cognitive questions

📊 Performance History

Stores score, duration, date, assessment type, and optional stress information

🧠 Cognitive Domains

Logical reasoning, quantitative aptitude, verbal ability, and memory/focus

❤️ Physiological Data

Supports heart-rate, temperature, and stress-related records through the backend workflow

🔎 Stress-to-Question Mapping

Uses question timestamps and health-data timestamps to identify questions associated with elevated stress

📚 Learning Resources

Domain material, practice sheets, mock tests, and downloadable resources

🔄 Longitudinal Tracking

Enables comparison of assessment attempts over time

🛡️ Secrets Protection

Credentials are loaded from environment variables or Streamlit secrets and are excluded from version control

🧠 Cognitive Assessment Domains

The learning and assessment workflow is organized around four practical areas:

Domain

Example Areas

Logical Reasoning

Series, coding-decoding, blood relations, statements and conclusions

Quantitative Aptitude

Percentages, ratios, averages, speed/math, data interpretation

Verbal Ability

Vocabulary, sentence arrangement, comprehension, grammar

Memory & Focus

Number recall, word recall, image sequences, concentration exercises

🔄 Application Workflow

                    ┌──────────────────────┐
                    │        USER          │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Authentication       │
                    │ Signup / Login       │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Candidate Dashboard  │
                    └──────────┬───────────┘
                               │
                    ┌──────────┴───────────┐
                    ▼                      ▼
              ┌───────────┐          ┌───────────┐
              │   Exam    │          │  Practice │
              └─────┬─────┘          └─────┬─────┘
                    └──────────┬───────────┘
                               ▼
                    ┌──────────────────────┐
                    │ Foundation / Advanced│
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Timed Assessment     │
                    │ Questions + Timer    │
                    │ Palette + Navigation │
                    └──────────┬───────────┘
                               │
                  ┌────────────┴────────────┐
                  ▼                         ▼
          ┌──────────────┐          ┌──────────────┐
          │ Manual Submit│          │ Auto Submit  │
          └──────┬───────┘          └──────┬───────┘
                 └──────────────┬───────────┘
                                ▼
                    ┌──────────────────────┐
                    │ Score & Performance  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Supabase History     │
                    │ + Stress Information │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Learning Resources & │
                    │ Improvement Support  │
                    └──────────────────────┘

The current assessment screenshots demonstrate a 45-question, 25-minute assessment interface.

🏗️ System Architecture

Software Layer

┌──────────────────────────────────────────────────────────┐
│                    Streamlit Web App                     │
├──────────────────────────────────────────────────────────┤
│ Authentication │ Dashboard │ Assessment │ Resources     │
├──────────────────────────────────────────────────────────┤
│ Question Generation │ Scoring │ Timing │ History        │
├──────────────────────────────────────────────────────────┤
│ Stress Analysis │ Recommendations │ Performance Logic   │
├──────────────────────────────────────────────────────────┤
│                    Supabase Backend                      │
│ users │ questions │ health_data │ test_history          │
└──────────────────────────────────────────────────────────┘

Embedded-System Research Layer

The accompanying patent specification describes a desk-mounted cognitive monitoring architecture:

Heart Rate / HRV ─┐
                  ├──► Signal Processing
Temperature ──────┤
                  │
Push Button ──────┘
                        │
                        ▼
                 Cognitive Analysis
                        │
                        ▼
                 Baseline Learning
                        │
                        ▼
                  Trend Analysis
                        │
                        ▼
                 Adaptive Thresholds
                        │
                        ▼
                Feedback / Intervention
                    ┌───┴───┐
                    ▼       ▼
                   LED    Buzzer
                    │       │
                    └───┬───┘
                        ▼
                Recovery Verification
                        │
                        ▼
                  Updated Baseline

The patent specification describes this as a closed-loop, non-invasive, curriculum-independent approach for detecting cognitive overload and progressive cognitive decline during study sessions.

🗄️ Supabase Data Model

The current software uses Supabase as its persistent backend.

users

Stores application accounts.

users
├── id
├── username
├── password_hash
└── created_at

Passwords are stored as hashes rather than plaintext passwords.

questions

Stores question timing information used to associate questions with physiological records.

questions
├── qid
├── st_time
└── en_time

health_data

Stores physiological and stress-related records.

health_data
├── stress
├── stress_level
├── temperature
├── heart_rate
└── created_at

test_history

Stores assessment performance history.

test_history
├── username
├── score
├── time_taken_seconds
├── date
├── type
└── stress (optional)

Stress-to-Question Correlation

Question start/end timestamps are compared with health-data timestamps. Questions occurring during HIGH or MODERATE stress periods can therefore be identified for further analysis and recommendation generation.

🔐 Authentication & Security

Authentication is Supabase-only in the current version.

Password protection

Passwords are hashed using PBKDF2-SHA256 through Passlib.

Plaintext passwords are not stored in the database.

No public default username/password is required.

Configuration

Supabase credentials are read from:

environment variables, or

Streamlit secrets

Example:

SUPABASE_URL = "your_supabase_url"
SUPABASE_ANON_KEY = "your_supabase_anon_key"
SUPABASE_SERVICE_ROLE_KEY = "your_service_role_key"

Never commit real credentials or service-role keys.

Do not commit:

.env
.streamlit/secrets.toml
users.db
.local_users.json
API keys
service-role keys

🛠️ Technology Stack

Layer

Technology

Language

Python

Web Framework

Streamlit

Database

Supabase / PostgreSQL

Authentication

Passlib + PBKDF2-SHA256

Data Processing

Pandas / NumPy

Machine Learning

scikit-learn

Model Persistence

joblib

Hardware Communication

PySerial

Embedded Controller Concept

ESP32 / Arduino

Physiological Inputs

Heart Rate / HRV, Temperature

Version Control

Git / GitHub

📁 Project Structure

Cognitive-Stress-Monitoring-and-Learning-Support-System/
│
├── mini project code/
│   ├── app/
│   │   ├── app.py
│   │   ├── login.py
│   │   ├── supabase_db.py
│   │   ├── predict.py
│   │   ├── question_generator.py
│   │   ├── gemini_analysis.py
│   │   ├── groq_client.py
│   │   └── hf_client.py
│   │
│   ├── data/
│   │   ├── dataset.csv
│   │   ├── questions.json
│   │   ├── _final_qns_extracted.txt
│   │   └── images/
│   │
│   ├── model/
│   │   └── train_model.py
│   │
│   ├── database/
│   │   └── database.py
│   │
│   ├── tests/
│   │   └── cognitive_test.py
│   │
│   └── requirements.txt
│
├── docs/
│   └── ARCHITECTURE.md
│
├── screenshots/
│   ├── README.md
│   └── cognitive-assessment-system-pages-updated/
│       ├── home-page.png
│       ├── dashboard-page.png
│       ├── dashboard-test-selection-page.png
│       ├── login-page.png
│       ├── signup-page.png
│       ├── resources-page.png
│       ├── assessment-page.png
│       ├── assessment-question-page.png
│       └── assessment-final-question-page.png
│
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── CONTRIBUTORS.md
├── CHANGELOG.md
├── FILE_REFERENCE_GUIDE.md
└── .gitignore

Local authentication files, local databases, and deployment secrets are intentionally excluded from the public repository.

🚀 Installation & Setup

1. Clone the Repository

git clone https://github.com/Akaash84/Cognitive-Stress-Monitoring-and-Learning-Support-System.git
cd Cognitive-Stress-Monitoring-and-Learning-Support-System

2. Create a Virtual Environment

Windows

python -m venv .venv
.venv\Scripts\activate

macOS / Linux

python3 -m venv .venv
source .venv/bin/activate

3. Install Dependencies

pip install -r "mini project code/requirements.txt"

4. Configure Supabase

Create the secrets file locally:

mini project code/.streamlit/secrets.toml

Add your own Supabase configuration:

SUPABASE_URL = "your_supabase_url"
SUPABASE_ANON_KEY = "your_supabase_anon_key"
SUPABASE_SERVICE_ROLE_KEY = "your_service_role_key"

Do not commit this file.

5. Run the Application

cd "mini project code"
streamlit run app/app.py

The application normally opens at:

http://localhost:8501

👨‍💻 How to Use

1. Create an Account

Open the application.

Select Signup.

Enter a username and password.

Create the account.

Log in with the newly created account.

2. Open the Dashboard

Choose:

Mode
├── Exam
└── Practice

Level
├── Foundation
└── Advanced

Then select Start Test.

3. Complete the Assessment

During an assessment you can:

select an answer

move between questions

use the question palette

monitor progress

monitor remaining time

move using Previous / Next

submit manually

allow automatic submission when the timer expires

4. Review Performance

The system can store and use:

score

time taken

assessment date

assessment type

historical attempts

optional stress information

5. Use Learning Resources

The Resources section provides material for:

Logical Reasoning

Quantitative Aptitude

Verbal Ability

Memory & Focus

practice sheets

mock tests

downloadable question resources

📸 Application Screenshots

🏠 Home Page

The home page introduces the platform, timed assessment workflow, performance tracking, and learning-support purpose.



📊 Candidate Dashboard

The dashboard provides the entry point for starting assessments and selecting the test workflow.



🎯 Test Selection

Users can select Exam / Practice and choose the Foundation / Advanced assessment level.



🔐 Login

The login page provides username/password authentication.



📝 Signup

New users can create an account before accessing the assessment dashboard.



📚 Learning Resources

The Resources page organizes learning material and practice activities across multiple cognitive domains.



🧪 Assessment Workspace

The assessment interface provides the timed examination environment, question palette, progress tracking, navigation, and submission controls.



❓ Assessment Question

The platform supports multiple-choice and image-based cognitive questions.



🏁 Final Question & Submission

The final-question screen demonstrates answer selection, question status, navigation, and final submission.



🔬 Research & Embedded-System Concept

The project is associated with the research concept:

Adaptive Embedded System for Real-Time Cognitive Stress Monitoring and Learning Optimization

The Indian patent application associated with the concept is:

Field

Details

Application No.

202641017456

Publication No.

IN202641017456 A1

Filing Date

17 February 2026

Publication Date

27 February 2026

Applicant

Vallurupalli Nageswara Rao Vignana Jyothi Institute of Engineering and Technology

IPC

A61B5/16, G16H20/70

The specification describes a desk-mounted system integrating:

heart-rate / pulse sensing

temperature sensing

push-button cognitive interaction

an embedded controller

signal processing

cognitive stress computation

personalized baseline learning

temporal trend analysis

adaptive thresholds

visual indicators

audio alerts

recovery verification

The patent specification describes the system as a closed-loop approach that can detect cognitive overload and progressive cognitive decline during active study sessions and provide adaptive micro-interventions.

Inventors listed in the application

Mr. Karnam Akhil

Dr. S. Nagini

Manda Akaash

Malladi Sri Raksha

Malapati Pavan

Mahendra Architha

🧩 Hardware Concept

The broader embedded-system concept can use:

Component

Role

Heart Rate / Pulse Sensor

Measures pulse-related physiological changes

Temperature Sensor

Measures temperature variation associated with fatigue

Push Button

Captures short cognitive interaction responses

ESP32 / Embedded Controller

Data acquisition and local processing

Signal Processing

Filtering, normalization, feature extraction

Cognitive Analysis

Computes cognitive stress indicators

Baseline Learning

Builds individualized reference profiles

Trend Analysis

Detects progressive deviations

LED Indicators

Visual cognitive-state feedback

Buzzer

Audio overload / alert feedback

The patent specification identifies LM35 / DS18B20 as possible temperature sensors and an ESP32 as a possible embedded controller.

🤖 ML & AI Direction

The project also includes an analytical layer intended to connect assessment performance and stress information.

Machine Learning

The project materials describe a trained Random Forest approach for performance classification using factors such as:

assessment score

time taken

cognitive domain

stress level

AI-Assisted Recommendations

The broader project concept uses AI services to analyze questions attempted during elevated-stress periods and support personalized, domain-specific learning recommendations.

The exact availability of external AI integrations depends on the configured project modules and API credentials.

📈 What the System Enables

The combined workflow is designed to support:

For Students

realistic exam-style practice

timed cognitive assessments

performance history

identification of weaker areas

domain-specific learning resources

stress-aware learning insights

For Research

correlation of question timing with physiological data

longitudinal performance tracking

cognitive-domain analysis

personalized baseline modeling

adaptive cognitive feedback research

For Educational Environments

structured assessment workflows

scalable cloud-backed storage

repeat-attempt analysis

learning-resource integration

potential future integration with low-cost embedded sensing

🧪 Example Closed-Loop Research Workflow

1. Sense
   ↓
2. Process physiological signals
   ↓
3. Analyze cognitive state
   ↓
4. Compare with personalized baseline
   ↓
5. Detect stress / deviation
   ↓
6. Trigger adaptive feedback
   ↓
7. Verify recovery
   ↓
8. Update baseline
   ↓
9. Continue monitoring

This closed-loop concept is described in the associated patent specification and is the broader research direction behind the software platform.

🛡️ Privacy & Responsible Use

This project is intended for educational and research use.

Physiological and stress-related measurements should be treated as sensitive information. Deployments should:

protect Supabase credentials

restrict database access appropriately

avoid committing secrets

collect physiological data only with appropriate consent

clearly communicate how collected data is used

avoid treating stress classifications as medical diagnoses

This system is not a medical diagnostic device. Stress-related outputs should be interpreted as software/research indicators rather than clinical diagnoses.

🧭 Current Scope & Future Direction

Current software scope

Streamlit web application

Supabase-backed authentication

timed cognitive assessments

Foundation / Advanced levels

Exam / Practice workflows

question timing

assessment history

learning resources

stress-related backend data integration

Future research direction

deeper real-time hardware integration

richer HRV analysis

stronger personalized baseline models

improved temporal stress mapping

adaptive study recommendations

closed-loop intervention validation

educator / research dashboards

expanded longitudinal analytics

📚 Documentation

Additional project documentation:

docs/ARCHITECTURE.md

CONTRIBUTING.md

CHANGELOG.md

FILE_REFERENCE_GUIDE.md

🤝 Contributing

Contributions are welcome.

A typical contribution workflow is:

git checkout -b feature/your-feature
git add .
git commit -m "Add: your feature"
git push origin feature/your-feature

Then open a Pull Request describing:

what changed

why it changed

how it was tested

any configuration changes required

Please review CONTRIBUTING.md before contributing.

📄 License

This project is distributed under the license included in LICENSE.

👥 Project Contributors

See CONTRIBUTORS.md for the contributor list.

⭐ Project Summary

Cognitive Stress Monitoring & Learning Support System brings together:

Cognitive Assessment
        +
Performance Tracking
        +
Physiological Stress Data
        +
Question-Level Timing
        +
Learning Resources
        +
ML / AI Analysis
        +
Adaptive Embedded-System Research

The goal is to move beyond score-only assessment toward a more context-aware, personalized, and research-oriented learning-support platform.

<div align="center">

🧠 Assess • Monitor • Understand • Improve

Built for cognitive assessment, stress-aware learning support, and adaptive educational technology research.

</div>
