# scripts/populate_state_data.py

from src.budget_sync import create_app, db
from src.budget_sync import StateInfo, StateTaxBracket


def populate_state_info():
    states = [
        ("AL", "Alabama"), ("AK", "Alaska"), ("AZ", "Arizona"), ("AR", "Arkansas"),
        ("CA", "California"), ("CO", "Colorado"), ("CT", "Connecticut"), ("DE", "Delaware"),
        ("FL", "Florida"), ("GA", "Georgia"), ("HI", "Hawaii"), ("ID", "Idaho"),
        ("IL", "Illinois"), ("IN", "Indiana"), ("IA", "Iowa"), ("KS", "Kansas"),
        ("KY", "Kentucky"), ("LA", "Louisiana"), ("ME", "Maine"), ("MD", "Maryland"),
        ("MA", "Massachusetts"), ("MI", "Michigan"), ("MN", "Minnesota"), ("MS", "Mississippi"),
        ("MO", "Missouri"), ("MT", "Montana"), ("NE", "Nebraska"), ("NV", "Nevada"),
        ("NH", "New Hampshire"), ("NJ", "New Jersey"), ("NM", "New Mexico"), ("NY", "New York"),
        ("NC", "North Carolina"), ("ND", "North Dakota"), ("OH", "Ohio"), ("OK", "Oklahoma"),
        ("OR", "Oregon"), ("PA", "Pennsylvania"), ("RI", "Rhode Island"), ("SC", "South Carolina"),
        ("SD", "South Dakota"), ("TN", "Tennessee"), ("TX", "Texas"), ("UT", "Utah"),
        ("VT", "Vermont"), ("VA", "Virginia"), ("WA", "Washington"), ("WV", "West Virginia"),
        ("WI", "Wisconsin"), ("WY", "Wyoming")
    ]

    # States with no income tax as of 2023
    no_tax_states = ['AK', 'FL', 'NV', 'NH', 'SD', 'TN', 'TX', 'WA', 'WY']

    # Flat tax states and their rates for 2023
    flat_tax_states = {
        'CO': 0.0444,
        'IL': 0.0499,
        'IN': 0.0315,
        'KY': 0.0500,
        'MA': 0.0500,
        'MI': 0.0425,
        'NC': 0.0499,
        'PA': 0.0307,
        'UT': 0.0485
    }

    for state_code, state_name in states:
        state_info = StateInfo(
            state_code=state_code,
            state_name=state_name,
            has_state_tax=(state_code not in no_tax_states)
        )
        db.session.add(state_info)

    db.session.commit()


def populate_tax_brackets():
    # 2023 Tax Brackets for each state
    tax_brackets = {
        'AL': [
            (0, 0.02),
            (500, 0.04),
            (3000, 0.05)
        ],
        'AZ': [
            (0, 0.0259),
            (28653, 0.0334),
            (57305, 0.0417),
            (171843, 0.045)
        ],
        'AR': [
            (0, 0.02),
            (4300, 0.04),
            (8500, 0.0535)
        ],
        'CA': [
            (0, 0.01),
            (10099, 0.02),
            (23942, 0.04),
            (37788, 0.06),
            (52455, 0.08),
            (66295, 0.093),
            (338639, 0.103),
            (406364, 0.113),
            (677275, 0.123),
            (1000000, 0.133)
        ],
        'CT': [
            (0, 0.03),
            (10000, 0.05),
            (50000, 0.055),
            (100000, 0.06),
            (200000, 0.065),
            (250000, 0.069),
            (500000, 0.0699)
        ],
        'DE': [
            (0, 0.022),
            (5000, 0.039),
            (10000, 0.048),
            (20000, 0.052),
            (25000, 0.0555),
            (60000, 0.066)
        ],
        'GA': [
            (0, 0.01),
            (750, 0.02),
            (2250, 0.03),
            (3750, 0.04),
            (5250, 0.05),
            (7000, 0.0575)
        ],
        'HI': [
            (0, 0.014),
            (2400, 0.032),
            (4800, 0.055),
            (9600, 0.064),
            (14400, 0.068),
            (19200, 0.072),
            (24000, 0.076),
            (36000, 0.079),
            (48000, 0.0825),
            (150000, 0.09),
            (175000, 0.10),
            (200000, 0.11)
        ],
        'ID': [
            (0, 0.01),
            (1568, 0.03),
            (3136, 0.045),
            (4704, 0.06)
        ],
        'IA': [
            (0, 0.044),
            (6000, 0.048),
            (30000, 0.068),
            (75000, 0.0784)
        ],
        'KS': [
            (0, 0.031),
            (15000, 0.0525),
            (30000, 0.057)
        ],
        'LA': [
            (0, 0.0185),
            (12500, 0.035),
            (50000, 0.0425)
        ],
        'ME': [
            (0, 0.058),
            (24500, 0.0675),
            (58050, 0.0715)
        ],
        'MD': [
            (0, 0.02),
            (1000, 0.03),
            (2000, 0.04),
            (3000, 0.0475),
            (100000, 0.05),
            (125000, 0.0525),
            (150000, 0.055),
            (250000, 0.0575)
        ],
        'MN': [
            (0, 0.0535),
            (28080, 0.068),
            (92230, 0.0785),
            (171220, 0.0985)
        ],
        'MS': [
            (0, 0.04),
            (5000, 0.05)
        ],
        'MO': [
            (0, 0.015),
            (1121, 0.02),
            (2242, 0.025),
            (3363, 0.03),
            (4484, 0.035),
            (5605, 0.04),
            (6726, 0.045),
            (7847, 0.05),
            (8968, 0.054)
        ],
        'MT': [
            (0, 0.01),
            (3300, 0.02),
            (5800, 0.03),
            (8900, 0.04),
            (12000, 0.05),
            (15400, 0.06),
            (19800, 0.065)
        ],
        'NE': [
            (0, 0.0246),
            (3340, 0.0351),
            (19990, 0.0501),
            (32210, 0.0684)
        ],
        'NJ': [
            (0, 0.014),
            (20000, 0.0175),
            (35000, 0.035),
            (40000, 0.0553),
            (75000, 0.0637),
            (500000, 0.0897),
            (1000000, 0.1075)
        ],
        'NM': [
            (0, 0.017),
            (5500, 0.032),
            (11000, 0.047),
            (16000, 0.049),
            (210000, 0.059)
        ],
        'NY': [
            (0, 0.04),
            (8500, 0.045),
            (11700, 0.0525),
            (13900, 0.059),
            (80650, 0.0597),
            (215400, 0.0633),
            (1077550, 0.0685),
            (5000000, 0.0965),
            (25000000, 0.103)
        ],
        'ND': [
            (0, 0.011),
            (41775, 0.0204),
            (101050, 0.0227),
            (210825, 0.0264),
            (458350, 0.029)
        ],
        'OH': [
            (25000, 0.0277),
            (44250, 0.0323),
            (88450, 0.0369),
            (110650, 0.0369)
        ],
        'OK': [
            (0, 0.0025),
            (1000, 0.0075),
            (2500, 0.0175),
            (3750, 0.0275),
            (4900, 0.0375),
            (7200, 0.0475)
        ],
        'OR': [
            (0, 0.0475),
            (3750, 0.0675),
            (9450, 0.0875),
            (125000, 0.099)
        ],
        'RI': [
            (0, 0.0375),
            (68200, 0.0475),
            (155050, 0.0599)
        ],
        'SC': [
            (0, 0.03),
            (3200, 0.04),
            (6410, 0.05),
            (9620, 0.06),
            (12820, 0.07)
        ],
        'VT': [
            (0, 0.0335),
            (40950, 0.066),
            (99200, 0.076),
            (206950, 0.0875)
        ],
        'VA': [
            (0, 0.02),
            (3000, 0.03),
            (5000, 0.05),
            (17000, 0.0575)
        ],
        'WV': [
            (0, 0.03),
            (10000, 0.04),
            (25000, 0.045),
            (40000, 0.06),
            (60000, 0.065)
        ],
        'WI': [
            (0, 0.0354),
            (13810, 0.0465),
            (27630, 0.0530),
            (304170, 0.0765)
        ]
    }

    # Add flat tax states
    flat_tax_states = {
        'CO': [(0, 0.0444)],
        'IL': [(0, 0.0499)],
        'IN': [(0, 0.0315)],
        'KY': [(0, 0.0500)],
        'MA': [(0, 0.0500)],
        'MI': [(0, 0.0425)],
        'NC': [(0, 0.0499)],
        'PA': [(0, 0.0307)],
        'UT': [(0, 0.0485)]
    }

    # Merge flat tax states into main tax brackets
    tax_brackets.update(flat_tax_states)

    # Populate the database
    for state, brackets in tax_brackets.items():
        for bracket_floor, rate in brackets:
            bracket = StateTaxBracket(
                state=state,
                tax_year=2023,
                bracket_floor=bracket_floor,
                rate=rate
            )
            db.session.add(bracket)

    db.session.commit()


def main():
    app = create_app()
    with app.app_context():
        print("Starting database population...")
        print("Populating state information...")
        populate_state_info()
        print("Populating tax brackets...")
        populate_tax_brackets()
        print("Database population completed!")


if __name__ == '__main__':
    main()
