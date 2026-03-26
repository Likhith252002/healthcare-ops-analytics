"""
Configuration settings for healthcare operations analytics platform.
All magic numbers and distributions are defined here for easy modification.
"""

# Data Generation Volumes
DATA_GENERATION = {
    'num_patients': 1000,
    'num_physicians': 50,
    'num_encounters': 5000,
    'simulation_days': 90,  # Generate data for past 90 days
}

# Department Configuration
# Format: (department_name, bed_capacity, specialty_list)
DEPARTMENTS = [
    ('Emergency Department', 20, ['Emergency Medicine']),
    ('Intensive Care Unit', 15, ['Critical Care', 'Pulmonology']),
    ('Medical', 50, ['Internal Medicine', 'Cardiology', 'Nephrology']),
    ('Surgical', 40, ['General Surgery', 'Orthopedics', 'Neurosurgery']),
    ('Obstetrics', 25, ['Obstetrics', 'Gynecology']),
    ('Pediatrics', 30, ['Pediatrics', 'Neonatology']),
]

# Patient Demographics Distributions
DEMOGRAPHICS = {
    'age_range': (0, 95),
    'gender_distribution': {
        'M': 0.49,
        'F': 0.49,
        'Other': 0.02,
    },
    'insurance_distribution': {
        'Private': 0.45,
        'Medicare': 0.30,
        'Medicaid': 0.20,
        'Uninsured': 0.05,
    },
}

# Encounter Patterns
ENCOUNTER_PATTERNS = {
    'admission_type_distribution': {
        'Emergency': 0.40,
        'Scheduled': 0.50,
        'Transfer': 0.10,
    },
    'weekday_multiplier': {
        0: 1.2,  # Monday - higher volume
        1: 1.1,  # Tuesday
        2: 1.0,  # Wednesday
        3: 1.0,  # Thursday
        4: 0.9,  # Friday
        5: 0.7,  # Saturday - lower volume
        6: 0.7,  # Sunday - lower volume
    },
    'length_of_stay_range': (1, 10),  # days
}

# Chief Complaints (most common reasons for hospital admission)
CHIEF_COMPLAINTS = [
    'Chest pain',
    'Shortness of breath',
    'Abdominal pain',
    'Fever',
    'Headache',
    'Back pain',
    'Nausea and vomiting',
    'Dizziness',
    'Injury/Trauma',
    'Altered mental status',
]

# Logging Configuration
LOGGING = {
    'log_level': 'INFO',
    'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'log_file': 'logs/data_generation.log',
}
