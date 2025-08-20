# Manual COBOL Business Rule Analysis

## Actual Business Rules in sample_legacy_insurance.cbl

After careful manual analysis of the COBOL code, here are the **24 actual business rules**:

### VALIDATE-APPLICATION Section (8 rules)
1. **Line 91-95**: Minimum age requirement (AGE < 18 → REJECT)
2. **Line 98-102**: Auto insurance maximum age (AUTO + AGE > 80 → REJECT)  
3. **Line 104-108**: Life insurance maximum age (LIFE + AGE > 75 → REJECT)
4. **Line 111-115**: Credit score requirement (CREDIT < 600 → REJECT)
5. **Line 118-122**: Employment status validation (UNEMPLOYED → REJECT)
6. **Line 135-140**: High-risk state review (FL/LA + AUTO → PENDING)
7. **Line 143-149**: Income vs coverage validation (COVERAGE > 500K + INCOME < 100K → REJECT)
8. **Line 151**: Default approval if all validations pass

### AUTO-VALIDATION Section (6 rules)
9. **Line 158-162**: Minimum driving experience (DRIVING-YEARS < 2 → REJECT)
10. **Line 165-169**: Maximum claims history (ACCIDENTS > 5 → REJECT)
11. **Line 172-176**: DUI exclusion (HAS-DUI → REJECT)
12. **Line 179-183**: Violation count restrictions (VIOLATIONS > 3 → REJECT)
13. **Line 186-192**: High-risk vehicle for young drivers (SPORTS/LUXURY + AGE < 30 → REJECT)
14. **Line 195-198**: Vehicle age inspection requirement (VEHICLE-AGE > 15 → PENDING)

### LIFE-VALIDATION Section (4 rules)  
15. **Line 205-210**: Smoker health risk assessment (SMOKER + AGE > 50 → PENDING)
16. **Line 213-216**: High coverage financial verification (COVERAGE > 1M → PENDING)
17. **Line 219-222**: Health conditions medical review (HEALTH-CONDITIONS present → PENDING)
18. **Line 225-228**: Beneficiary requirement (BENEFICIARY-COUNT = 0 → REJECT)

### CALCULATE-PREMIUM Section (6 rules)
19. **Line 237-239**: Young driver surcharge (AUTO + AGE < 25 → PREMIUM * 1.50)
20. **Line 242-246**: Senior married driver discount (AUTO + AGE > 65 + MARRIED → PREMIUM * 0.90)
21. **Line 249-252**: Smoker life insurance surcharge (LIFE + SMOKER → PREMIUM * 1.25)
22. **Line 255-258**: Multi-policy discount (MULTI-POLICY → PREMIUM * 0.90)
23. **Line 261-263**: Auto premium cap (AUTO + PREMIUM > 5000 → CAP at 5000)
24. **Line 265-267**: Life premium cap (LIFE + PREMIUM > 50000 → CAP at 50000)

### Additional Rules Found (2 bonus rules - not in original count)
25. **Line 270-272**: High-risk state surcharge (FL/CA → PREMIUM * 1.15)
26. **Line 282-284**: Display rejection reason logic

## Rule Categories Analysis

### Validation Rules (11 total)
- Age requirements (3): Min age, Auto max age, Life max age
- Financial validation (2): Credit score, Income vs coverage  
- Personal validation (3): Employment, DUI history, Beneficiary requirement
- Risk assessment (3): State restrictions, Health conditions, Vehicle age

### Calculation Rules (6 total)  
- Surcharges (3): Young driver, Smoker, High-risk state
- Discounts (2): Senior married, Multi-policy
- Caps (2): Auto premium cap, Life premium cap

### Decision Rules (4 total)
- Driving validation (2): Experience, Violations
- Risk factors (2): Accident history, High-risk vehicles

### Workflow Rules (3 total)
- Section routing (2): AUTO-VALIDATION, LIFE-VALIDATION calls
- Default approval (1): Final approval logic

## Expected Pattern Matches

The RuleCompletenessAnalyzer should find **24 rules** (not 47). The current patterns are too broad and catching:
- Comment lines without actual rules
- Data definitions that aren't business logic  
- Multiple matches per single rule
- Non-business procedural code

## Recommended Pattern Refinements

1. **Focus on IF statements with business conditions**
2. **Include COMPUTE statements with business calculations**
3. **Exclude pure data movement without business logic**
4. **Require action keywords like REJECT, PENDING, or calculation operators**