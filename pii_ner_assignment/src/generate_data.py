import json
import random
from datetime import datetime, timedelta
import string

# Try to import names library, fallback to hardcoded list if not available
try:
    from names import get_first_name, get_last_name
    USE_NAMES_LIB = True
except ImportError:
    USE_NAMES_LIB = False
    print("Warning: 'names' library not found. Install with: pip install names")

# Try to import faker for realistic data generation
try:
    from faker import Faker
    fake = Faker()
    USE_FAKER = True
except ImportError:
    USE_FAKER = False
    print("Warning: 'faker' library not found. Install with: pip install faker")

# --- Global digit list ---
digits = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']

# --- Expanded name lists (fallback) ---
FIRST_NAMES = [
    'John', 'Jane', 'Ramesh', 'Priya', 'Michael', 'Sarah', 'Arjun', 'Anaya',
    'James', 'Emily', 'David', 'Jessica', 'Robert', 'Emma', 'William', 'Olivia',
    'Richard', 'Sophia', 'Joseph', 'Isabella', 'Thomas', 'Mia', 'Charles', 'Charlotte',
    'Christopher', 'Amelia', 'Daniel', 'Harper', 'Matthew', 'Evelyn', 'Anthony', 'Abigail',
    'Mark', 'Ella', 'Donald', 'Madison', 'Steven', 'Chloe', 'Paul', 'Ava',
    'Andrew', 'Scarlett', 'Joshua', 'Violet', 'Kenneth', 'Grace', 'Kevin', 'Cora',
    'Brian', 'Lily', 'Edward', 'Penelope', 'Ronald', 'Camila', 'Anthony', 'Riley',
    'Frank', 'Ariana', 'Ryan', 'Layla', 'Gary', 'Nora', 'Nicolas', 'Elena',
    'Eric', 'Aurora', 'Jonathan', 'Zoe', 'Stephen', 'Leah', 'Larry', 'Hannah',
    'Justin', 'Natalie', 'Scott', 'Sarah', 'Brandon', 'Victoria', 'Benjamin', 'Madison',
    'Raj', 'Deepak', 'Anil', 'Amit', 'Vikram', 'Sanjay', 'Ravi', 'Suresh',
    'Ahmed', 'Hassan', 'Ali', 'Omar', 'Youssef', 'Ibrahim', 'Mohammed', 'Karim',
    'Juan', 'Carlos', 'Miguel', 'Diego', 'Luis', 'Fernando', 'Antonio', 'Jorge',
    'Maria', 'Rosa', 'Carmen', 'Ana', 'Isabel', 'Gabriela', 'Sofia', 'Valentina'
]

LAST_NAMES = [
    'Smith', 'Doe', 'Patel', 'Sharma', 'Johnson', 'Williams', 'Kumar', 'Singh',
    'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Hernandez',
    'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson',
    'Martin', 'Lee', 'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 'Clark',
    'Ramirez', 'Lewis', 'Robinson', 'Walker', 'Young', 'Allen', 'King', 'Wright',
    'Scott', 'Torres', 'Peterson', 'Phillips', 'Campbell', 'Parker', 'Evans', 'Edwards',
    'Collins', 'Reeves', 'Stewart', 'Morris', 'Rogers', 'Morgan', 'Peterson', 'Cooper',
    'Varma', 'Gupta', 'Verma', 'Reddy', 'Rao', 'Iyer', 'Nair', 'Bhat',
    'Khan', 'Ahmed', 'Ali', 'Hassan', 'Hussein', 'Ibrahim', 'Malik', 'Rashid',
    'O\'Brien', 'Murphy', 'Kelly', 'Sullivan', 'Connor', 'McCarthy', 'Lynch', 'Donnelly'
]

# --- Expanded city and location lists ---
CITIES = [
    'New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia',
    'San Antonio', 'San Diego', 'Dallas', 'San Jose', 'Austin', 'Jacksonville',
    'Fort Worth', 'Columbus', 'Indianapolis', 'Charlotte', 'San Francisco', 'Seattle',
    'Denver', 'Washington', 'Boston', 'Portland', 'Nashville', 'Las Vegas',
    'Memphis', 'New Orleans', 'Atlanta', 'Miami', 'London', 'Paris', 'Tokyo',
    'Beijing', 'Shanghai', 'Mumbai', 'Delhi', 'Bangalore', 'Hyderabad',
    'Singapore', 'Hong Kong', 'Dubai', 'Moscow', 'Berlin', 'Madrid',
    'Rome', 'Amsterdam', 'Bangkok', 'Toronto', 'Sydney', 'Melbourne',
    'Vancouver', 'Mexico City', 'Sao Paulo', 'Buenos Aires', 'Istanbul', 'Cairo'
]

LOCATIONS = [
    'Central Park', 'Times Square', 'Marine Drive', 'Eiffel Tower', 'Big Ben',
    'Opera House', 'CN Tower', 'Golden Gate Bridge', 'Statue of Liberty',
    'Empire State Building', 'Space Needle', 'Hollywood Sign', 'Lincoln Memorial',
    'White House', 'Buckingham Palace', 'Taj Mahal', 'Great Wall of China',
    'Colosseum', 'Leaning Tower of Pisa', 'Notre Dame', 'Sacre Coeur',
    'Tower Bridge', 'Tower of London', 'Westminster Abbey', 'St Pauls Cathedral',
    'Brandenburg Gate', 'Sagrada Familia', 'Prado Museum', 'Uffizi Gallery',
    'Vatican City', 'Peterhof Palace', 'Red Square', 'Kremlin', 'Mt Fuji',
    'Forbidden City', 'Summer Palace', 'Great Buddha', 'Angkor Wat',
    'Borobudur', 'Petra', 'Machu Picchu', 'Christ the Redeemer', 'Niagara Falls',
    'Banff National Park', 'Great Barrier Reef', 'Uluru', 'Rotorua',
    'Bali', 'Maldives', 'Lake Tahoe', 'Yellowstone', 'Grand Canyon',
    'Yosemite', 'Disneyland', 'Universal Studios', 'Las Vegas Strip',
    'Burj Khalifa', 'Palm Jumeirah', 'Kremlin Wall', 'Saint Basil Cathedral',
    'Louvre Museum', 'Versailles Palace', 'Arc de Triomphe', 'Pantheon',
    'Ponte Vecchio', 'Trevi Fountain', 'Spanish Steps', 'Colosseum Rome'
]

# --- Email domains (including more realistic ones) ---
EMAIL_DOMAINS = [
    'gmail dot com', 'yahoo dot com', 'example dot com', 'outlook dot com',
    'company dot com', 'hotmail dot com', 'mail dot com', 'aol dot com',
    'protonmail dot com', 'icloud dot com', 'live dot com', 'msn dot com',
    'yandex dot com', 'mail dot ru', 'domain dot org', 'business dot net',
    'work dot co dot uk', 'email dot co dot in', 'inbox dot com'
]

# Helper function to get names
def get_person_name():
    """Get a person name, using faker if available, else from hardcoded list."""
    if USE_FAKER:
        return fake.name()
    elif USE_NAMES_LIB:
        return f"{get_first_name()} {get_last_name()}"
    else:
        return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def get_first_name_only():
    """Get just a first name."""
    if USE_FAKER:
        return fake.first_name()
    elif USE_NAMES_LIB:
        return get_first_name()
    else:
        return random.choice(FIRST_NAMES)

def get_last_name_only():
    """Get just a last name."""
    if USE_FAKER:
        return fake.last_name()
    elif USE_NAMES_LIB:
        return get_last_name()
    else:
        return random.choice(LAST_NAMES)

def get_city():
    """Get a city name."""
    if USE_FAKER:
        return fake.city()
    else:
        return random.choice(CITIES)

def get_location():
    """Get a location/landmark."""
    if USE_FAKER:
        return f"{fake.city()} {random.choice(['Museum', 'Tower', 'Park', 'Garden', 'Plaza'])}"
    else:
        return random.choice(LOCATIONS)

# --- Entity generators ---
def gen_credit_card():
    """Generates a 16-digit credit card number spelled out."""
    return ' '.join(random.choices(digits, k=16))

def gen_credit_card_partial():
    """Generates last 4 digits of credit card."""
    return ' '.join(random.choices(digits, k=4))

def gen_credit_card_prefix():
    """Generates first 4 digits of credit card."""
    return ' '.join(random.choices(digits, k=4))

def gen_phone():
    """Generates a 10-digit phone number."""
    return f"area code {random.randint(100,999)} {' '.join(random.choices(digits, k=7))}"

def gen_phone_variant():
    """Generates phone in different formats."""
    formats = [
        f"plus one {random.randint(100,999)} {' '.join(random.choices(digits, k=7))}",
        f"{random.randint(100,999)} {' '.join(random.choices(digits, k=7))}",
        f"call {random.randint(100,999)} {' '.join(random.choices(digits, k=7))} extension {random.randint(1,9999)}",
        f"reach me at {random.randint(100,999)} {' '.join(random.choices(digits, k=7))}",
        f"dial {random.randint(100,999)} {' '.join(random.choices(digits, k=7))}"
    ]
    return random.choice(formats)

def gen_email(name):
    """Generates an email address."""
    clean_name = name.lower().replace(' ', ' dot ')
    return f"{clean_name} at {random.choice(EMAIL_DOMAINS)}"

def gen_email_variant(name):
    """Generates email with number suffix."""
    clean_name = name.lower().replace(' ', ' dot ')
    suffix = random.randint(1, 999)
    return f"{clean_name}{suffix} at {random.choice(EMAIL_DOMAINS)}"

def gen_email_firstname_only(first_name):
    """Email with just first name."""
    clean_name = first_name.lower()
    return f"{clean_name} at {random.choice(EMAIL_DOMAINS)}"

def gen_person_name():
    """Generates a full name."""
    return get_person_name()

def gen_person_name_partial():
    """Generates just a first name."""
    return get_first_name_only()

def gen_person_name_last():
    """Generates just a last name."""
    return get_last_name_only()

def gen_date():
    """Generates a random date within the last 5 years."""
    start_date = datetime(2020, 1, 1)
    delta = timedelta(days=random.randint(0, 1825))
    date = start_date + delta
    return f"{date.month} {date.day} {date.year}"

def gen_date_variant():
    """Generates date in different formats."""
    start_date = datetime(2020, 1, 1)
    delta = timedelta(days=random.randint(0, 1825))
    date = start_date + delta
    month_names = ['january', 'february', 'march', 'april', 'may', 'june',
                   'july', 'august', 'september', 'october', 'november', 'december']
    formats = [
        f"{date.month}/{date.day}/{date.year}",
        f"{month_names[date.month-1]} {date.day} {date.year}",
        f"{date.day} {month_names[date.month-1]} {date.year}"
    ]
    return random.choice(formats)

def gen_date_partial():
    """Generates just month and year."""
    start_date = datetime(2020, 1, 1)
    delta = timedelta(days=random.randint(0, 1825))
    date = start_date + delta
    return f"{date.month}/{date.year}"

# Map placeholders to generators and labels
GENERATORS = {
    'phone': (gen_phone, 'PHONE'),
    'phone_var': (gen_phone_variant, 'PHONE'),
    'cc': (gen_credit_card, 'CREDIT_CARD'),
    'cc_partial': (gen_credit_card_partial, 'CREDIT_CARD'),
    'cc_prefix': (gen_credit_card_prefix, 'CREDIT_CARD'),
    'email': (gen_email, 'EMAIL'),
    'email_var': (gen_email_variant, 'EMAIL'),
    'email_fname': (gen_email_firstname_only, 'EMAIL'),
    'name': (gen_person_name, 'PERSON_NAME'),
    'name_partial': (gen_person_name_partial, 'PERSON_NAME'),
    'name_last': (gen_person_name_last, 'PERSON_NAME'),
    'date': (gen_date, 'DATE'),
    'date_var': (gen_date_variant, 'DATE'),
    'date_partial': (gen_date_partial, 'DATE'),
    'city': (get_city, 'CITY'),
    'loc': (get_location, 'LOCATION'),
}

# --- Expanded and diverse templates ---
templates = [
    # Simple entities
    "Call me at {phone}.",
    "My credit card is {cc}.",
    "Email me at {email}.",
    "I am {name}, born on {date}.",
    "Visiting {city} near {loc}.",
    
    # Realistic STT with fillers
    "Um, like, my card number {cc} and phone {phone}. Born {date} in {city}. Met {name} at {loc}. Send to {email}.",
    "Yeah so uh my, my phone number is {phone} and you can email me at {email}.",
    "So like contact me at {phone} or my email which is {email}.",
    
    # Partial card numbers
    "Um the last four of my card is {cc_partial}, sorry {cc_partial}.",
    "Just charge the last four {cc_partial} to the card.",
    "Can you confirm the ending {cc_partial}?",
    "Starting with {cc_prefix}, ending with {cc_partial}.",
    
    # Date variations
    "I was born on {date_var}, yeah {date_var}.",
    "The appointment is on {date_var}.",
    "Valid through {date_partial}.",
    
    # Location-focused
    "I am currently at {loc} in {city}.",
    "We met at {loc}.",
    "Heading to {loc} this week.",
    "From {city}, been to {loc} many times.",
    
    # Name variations
    "My name is {name_partial}, {name_partial}.",
    "This is {name} calling.",
    "Just tell {name_last} about it.",
    "Ask for {name_partial} when you call.",
    
    # Phone variants
    "You can reach me at {phone_var}.",
    "Call me on {phone_var}.",
    
    # Email variants
    "My backup email is {email_var}.",
    "Contact {email_fname} please.",
    
    # Complex, noisy patterns
    "Okay so, so my information: name is {name}, phone {phone}, email {email}, and I was born {date} in {city}.",
    "The confirmation code is uh {cc_partial} on the card ending in {cc_partial}.",
    "You can reach me at {phone} or text me or email at {email}.",
    
    # Short implicit entities
    "{name} here, calling from {city}.",
    "Send the details to {email}.",
    "My number is {phone_var}.",
    
    # Repetition (common in STT)
    "Call me, call me at {phone}.",
    "The email is {email}, that's {email}.",
    "So my card is {cc}, that's {cc}.",
    
    # With location context
    "I work near {loc} in {city}.",
    "When I visit {loc} in {city}, call me at {phone}.",
    "The office near {loc} has my number as {phone}.",
    
    # Multiple entity interactions
    "Hi {name}, your order to {city} is ready. Call {phone} or email {email}.",
    "Confirm delivery to {city} near {loc} for {name}. Use card ending {cc_partial}.",
    "Call me {name} at {phone}, I moved to {city} near {loc}.",
    
    # Address-style patterns (implicit)
    "{name} lives in {city}, works at {loc}.",
    "Shipped to {city}, contact {name} at {phone}.",
    
    # Transaction-style
    "Transaction: {name}, amount confirmed for card {cc_partial}.",
    "Receipt: {email}, date {date_var}, amount charged.",
    "Booking confirmed for {name} on {date_var} in {city}.",
    
    # Support ticket style
    "Customer: {name}, email {email}, phone {phone}. Issue in {city}.",
    "Support request from {email}, call back {phone_var}.",
    
    # Informal conversation
    "So yeah my email is {email} and call me at {phone}.",
    "Like, I'm {name} from {city}, my number is {phone}.",
    "Hey this is {name}, I'll be in {city} until {date_var}.",
    
    # Confirmation style
    "Confirming: {name}, phone {phone}, email {email}.",
    "Account holder {name}, card {cc}, expires {date_partial}.",
    
    # Schedule/booking
    "Book for {name} on {date} at {loc} in {city}.",
    "Reservation under {name}, arrive {date_var}.",
    
    # Multiple names/entities
    "Tell {name} to call {name_partial} at {phone}.",
    
    # Technical/reference numbers
    "Reference: {name} - {phone} - {email}.",
    "Account {name}, pin {cc_partial}, verify {email}.",
    
    # Confirmation repeated
    "That's {email}, correct? {email}.",
    "Phone number is {phone}, got it {phone}?",
    
    # Mixed formal/informal
    "Customer {name_last} can be reached at {phone} or {email}.",
    "Please send confirmation to {email} for {name}.",
]

# Generate N examples
def generate_examples(n, split='train'):
    examples = []
    for i in range(n):
        template = random.choice(templates)
        
        # Generate all required values
        name_value = gen_person_name()
        first_name_value = gen_first_name_only()
        
        pii_values = {
            'phone': gen_phone(),
            'phone_var': gen_phone_variant(),
            'cc': gen_credit_card(),
            'cc_partial': gen_credit_card_partial(),
            'cc_prefix': gen_credit_card_prefix(),
            'name': name_value,
            'name_partial': first_name_value,
            'name_last': gen_person_name_last(),
            'date': gen_date(),
            'date_var': gen_date_variant(),
            'date_partial': gen_date_partial(),
            'city': get_city(),
            'loc': get_location(),
            'email': gen_email(name_value),
            'email_var': gen_email_variant(name_value),
            'email_fname': gen_email_firstname_only(first_name_value),
        }

        # Only include values that are in the template
        context_data = {}
        for placeholder in pii_values.keys():
            if '{' + placeholder + '}' in template:
                context_data[placeholder] = pii_values[placeholder]

        # Format and lowercase
        full_text = template.format(**context_data).lower()
        
        entities = []
        # Annotate entities
        for placeholder, value in context_data.items():
            _, label = GENERATORS[placeholder]
            search_value = value.lower()
            
            # Find all occurrences
            start = 0
            while True:
                start_index = full_text.find(search_value, start)
                if start_index == -1:
                    break
                
                end_index = start_index + len(search_value)
                
                entities.append({
                    "start": start_index, 
                    "end": end_index, 
                    "label": label
                })
                
                start = end_index

        examples.append({
            "id": f"utt_{i:04d}",
            "text": full_text,
            "entities": entities
        })
    return examples

# Fix function name
def gen_first_name_only():
    return get_first_name_only()

# Run generation with significantly increased data
train = generate_examples(3000, 'train')    # 3x original
dev = generate_examples(600, 'dev')         # 4x original
test = generate_examples(400, 'test')       # 4x original

# Write data
import os
os.makedirs('data', exist_ok=True)

print("Writing training data...")
with open('data/train.jsonl', 'w') as f:
    for ex in train: 
        json.dump(ex, f)
        f.write('\n')

print("Writing development data...")
with open('data/dev.jsonl', 'w') as f:
    for ex in dev: 
        json.dump(ex, f) 
        f.write('\n')

print("Writing test data...")
with open('data/test.jsonl', 'w') as f:
    for ex in test: 
        ex_no_entities = {k: v for k, v in ex.items() if k != 'entities'}
        json.dump(ex_no_entities, f) 
        f.write('\n')

print(f"\nSuccessfully generated {len(train)} training, {len(dev)} development, and {len(test)} test examples.")
print("Files saved in the 'data/' directory.")
print(f"\nLibrary status:")
print(f"  Faker: {'✓ Available' if USE_FAKER else '✗ Not available (optional, install with: pip install faker)'}")
print(f"  Names: {'✓ Available' if USE_NAMES_LIB else '✗ Not available (optional, install with: pip install names)'}")