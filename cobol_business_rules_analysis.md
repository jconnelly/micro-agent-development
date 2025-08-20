# COBOL Insurance Business Rules Analysis

## Summary
**COBOL File**: sample_legacy_insurance.cbl  
**Extracted Rules File**: extracted_rules_output.json  
**Expected Rules**: 24 business rules  
**Extracted Rules**: 14 rules  
**Missing Rules**: 10 rules (41.7% extraction gap)

---

## Complete Business Rules Inventory

### **VALIDATION RULES (Lines 89-154)**

1. **RULE_001: Minimum Age Requirement** ✅ *Extracted*
   - **Line**: 91-95
   - **Logic**: `IF APPLICANT-AGE < MIN-AGE (18)`
   - **Action**: REJECT - 'APPLICANT TOO YOUNG FOR INSURANCE'

2. **RULE_002: Auto Insurance Max Age** ✅ *Extracted*
   - **Line**: 98-102
   - **Logic**: `IF AUTO-POLICY AND APPLICANT-AGE > MAX-AGE-AUTO (80)`
   - **Action**: REJECT - 'EXCEEDS MAXIMUM AGE FOR AUTO INSURANCE'

3. **RULE_003: Life Insurance Max Age** ✅ *Extracted*
   - **Line**: 104-108
   - **Logic**: `IF LIFE-POLICY AND APPLICANT-AGE > MAX-AGE-LIFE (75)`
   - **Action**: REJECT - 'EXCEEDS MAXIMUM AGE FOR LIFE INSURANCE'

4. **RULE_004: Credit Score Minimum** ✅ *Extracted*
   - **Line**: 111-115
   - **Logic**: `IF CREDIT-SCORE < MIN-CREDIT-SCORE (600)`
   - **Action**: REJECT - 'CREDIT SCORE TOO LOW'

5. **RULE_005: Employment Status Check** ✅ *Extracted*
   - **Line**: 118-122
   - **Logic**: `IF EMPLOYMENT-STATUS = 'UNEMPLOYED'`
   - **Action**: REJECT - 'UNEMPLOYED APPLICANTS NOT ELIGIBLE'

6. **RULE_006: Auto Policy Validation Call** ✅ *Extracted (simplified)*
   - **Line**: 125-127
   - **Logic**: `IF AUTO-POLICY PERFORM AUTO-VALIDATION`
   - **Action**: Execute auto-specific validation rules

7. **RULE_007: Life Policy Validation Call** ✅ *Extracted (simplified)*
   - **Line**: 130-132
   - **Logic**: `IF LIFE-POLICY PERFORM LIFE-VALIDATION`
   - **Action**: Execute life-specific validation rules

8. **RULE_008: High-Risk State Review** ✅ *Extracted*
   - **Line**: 135-140
   - **Logic**: `IF (APPLICANT-STATE = 'FL' OR 'LA') AND AUTO-POLICY`
   - **Action**: PENDING - 'HIGH RISK STATE - MANUAL REVIEW REQUIRED'

9. **RULE_009: Income vs Coverage Validation** ✅ *Extracted*
   - **Line**: 143-149
   - **Logic**: `IF COVERAGE-AMOUNT > 500000 AND ANNUAL-INCOME < 100000`
   - **Action**: REJECT - 'INSUFFICIENT INCOME FOR COVERAGE AMOUNT'

10. **RULE_010: Default Approval** ✅ *Extracted*
    - **Line**: 151
    - **Logic**: Default case after all validations pass
    - **Action**: APPROVE policy

### **AUTO-SPECIFIC RULES (Lines 156-201)** - ❌ **2 MISSING**

11. **RULE_011: Minimum Driving Experience** ✅ *Extracted*
    - **Line**: 158-162
    - **Logic**: `IF DRIVING-YEARS < MIN-DRIVING-YEARS (2)`
    - **Action**: REJECT - 'INSUFFICIENT DRIVING EXPERIENCE'

12. **RULE_012: Maximum Accident History** ✅ *Extracted*
    - **Line**: 165-169
    - **Logic**: `IF ACCIDENT-COUNT > MAX-CLAIMS-ALLOWED (5)`
    - **Action**: REJECT - 'TOO MANY PREVIOUS ACCIDENTS'

13. **RULE_013: DUI Exclusion** ❌ **MISSING**
    - **Line**: 172-176
    - **Logic**: `IF HAS-DUI`
    - **Action**: REJECT - 'DUI HISTORY - NOT ELIGIBLE'

14. **RULE_014: Traffic Violation Limit** ❌ **MISSING**
    - **Line**: 179-183
    - **Logic**: `IF VIOLATION-COUNT > 3`
    - **Action**: REJECT - 'TOO MANY TRAFFIC VIOLATIONS'

15. **RULE_015: High-Risk Vehicle for Young Drivers** ❌ **MISSING**
    - **Line**: 186-192
    - **Logic**: `IF (VEHICLE-TYPE = 'SPORTS' OR 'LUXURY') AND APPLICANT-AGE < 30`
    - **Action**: REJECT - 'HIGH RISK VEHICLE FOR YOUNG DRIVER'

16. **RULE_016: Old Vehicle Inspection** ❌ **MISSING**
    - **Line**: 195-198
    - **Logic**: `IF VEHICLE-AGE > 15`
    - **Action**: PENDING - 'OLD VEHICLE - INSPECTION REQUIRED'

### **LIFE-SPECIFIC RULES (Lines 203-231)** - ❌ **4 MISSING**

17. **RULE_017: Smoker Risk Assessment** ❌ **MISSING**
    - **Line**: 205-210
    - **Logic**: `IF IS-SMOKER AND APPLICANT-AGE > 50`
    - **Action**: PENDING - 'SMOKER OVER 50 - MEDICAL EXAM REQUIRED'

18. **RULE_018: High Coverage Financial Verification** ❌ **MISSING**
    - **Line**: 213-216
    - **Logic**: `IF COVERAGE-AMOUNT > 1000000`
    - **Action**: PENDING - 'HIGH COVERAGE - FINANCIAL VERIFICATION REQUIRED'

19. **RULE_019: Health Conditions Review** ❌ **MISSING**
    - **Line**: 219-222
    - **Logic**: `IF HEALTH-CONDITIONS NOT = SPACES`
    - **Action**: PENDING - 'HEALTH CONDITIONS - MEDICAL REVIEW REQUIRED'

20. **RULE_020: Beneficiary Requirement** ❌ **MISSING**
    - **Line**: 225-228
    - **Logic**: `IF BENEFICIARY-COUNT = 0`
    - **Action**: REJECT - 'AT LEAST ONE BENEFICIARY REQUIRED'

### **PREMIUM CALCULATION RULES (Lines 233-275)** - ❌ **4 MISSING**

21. **RULE_021: Young Driver Surcharge** ❌ **MISSING**
    - **Line**: 237-239
    - **Logic**: `IF AUTO-POLICY AND APPLICANT-AGE < YOUNG-DRIVER-AGE (25)`
    - **Action**: PREMIUM *= 1.50 (50% surcharge)

22. **RULE_022: Senior Driver Discount** ❌ **MISSING**
    - **Line**: 242-246
    - **Logic**: `IF AUTO-POLICY AND APPLICANT-AGE > SENIOR-DRIVER-AGE (65) AND MARRIED`
    - **Action**: PREMIUM *= 0.90 (10% discount)

23. **RULE_023: Smoker Surcharge** ❌ **MISSING**
    - **Line**: 249-252
    - **Logic**: `IF LIFE-POLICY AND IS-SMOKER`
    - **Action**: PREMIUM *= (1 + SMOKER-SURCHARGE-PCT/100) = 1.25 (25% surcharge)

24. **RULE_024: Multi-Policy Discount** ❌ **MISSING**
    - **Line**: 255-258
    - **Logic**: `IF MULTI-POLICY`
    - **Action**: PREMIUM *= (1 - MULTI-POLICY-DISCOUNT/100) = 0.90 (10% discount)

**NOTE**: The extracted file includes 2 additional rules (RULE_001_v2, RULE_002_v2) that appear to be from the premium calculation section but are incorrectly mapped.

---

## Gap Analysis

### **Missing Rule Categories:**

1. **Auto-Specific Rules (4 missing):**
   - DUI exclusion policy
   - Traffic violation limits  
   - High-risk vehicle restrictions
   - Old vehicle inspection requirements

2. **Life-Specific Rules (4 missing):**
   - Smoker health risk assessment
   - High coverage financial verification
   - Health conditions medical review
   - Beneficiary validation requirements

3. **Premium Calculation Rules (4 missing):**
   - Young driver surcharge (50%)
   - Senior married driver discount (10%)
   - Smoker surcharge for life insurance (25%)
   - Multi-policy discount (10%)

### **Extraction Issues:**
- **Incomplete coverage of AUTO-VALIDATION section**
- **Complete miss of LIFE-VALIDATION section**  
- **Complete miss of CALCULATE-PREMIUM section**
- **Possible chunking issues** affecting rule extraction completeness

### **Recommendations:**
1. **Improve chunking strategy** to ensure complete section coverage
2. **Add section-aware processing** to handle COBOL paragraph structure
3. **Implement rule validation** to cross-check expected vs extracted rule counts
4. **Enhanced prompt engineering** for COBOL-specific business rule extraction