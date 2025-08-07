      *================================================================
      * INSURANCE POLICY VALIDATION PROGRAM
      * LEGACY MAINFRAME SYSTEM - CIRCA 1985
      * CONTAINS EMBEDDED BUSINESS RULES FOR POLICY APPROVAL
      *================================================================
       IDENTIFICATION DIVISION.
       PROGRAM-ID. INSVALID.
       AUTHOR. LEGACY-SYSTEMS-TEAM.
       DATE-WRITTEN. 01/15/1985.
       DATE-COMPILED.

       ENVIRONMENT DIVISION.
       CONFIGURATION SECTION.
       SOURCE-COMPUTER. IBM-370.
       OBJECT-COMPUTER. IBM-370.

       DATA DIVISION.
       WORKING-STORAGE SECTION.

      * Business Rule Constants
       77  MIN-AGE                    PIC 99 VALUE 18.
       77  MAX-AGE-LIFE               PIC 99 VALUE 75.
       77  MAX-AGE-AUTO               PIC 99 VALUE 80.
       77  MIN-DRIVING-YEARS          PIC 99 VALUE 02.
       77  MAX-CLAIMS-ALLOWED         PIC 99 VALUE 05.
       77  MIN-CREDIT-SCORE           PIC 999 VALUE 600.
       77  MAX-PREMIUM-AUTO           PIC 9(6)V99 VALUE 5000.00.
       77  MAX-PREMIUM-LIFE           PIC 9(7)V99 VALUE 50000.00.
       77  HIGH-RISK-THRESHOLD        PIC 99 VALUE 65.
       77  YOUNG-DRIVER-AGE           PIC 99 VALUE 25.
       77  SENIOR-DRIVER-AGE          PIC 99 VALUE 65.
       77  DUI-EXCLUSION-YEARS        PIC 99 VALUE 05.
       77  SMOKER-SURCHARGE-PCT       PIC 99V99 VALUE 25.00.
       77  MULTI-POLICY-DISCOUNT      PIC 99V99 VALUE 10.00.

       01  POLICY-APPLICATION.
           05  APPLICANT-INFO.
               10  APPLICANT-NAME         PIC X(30).
               10  APPLICANT-AGE          PIC 99.
               10  APPLICANT-STATE        PIC X(2).
               10  CREDIT-SCORE           PIC 999.
               10  MARITAL-STATUS         PIC X(1).
                   88  MARRIED            VALUE 'M'.
                   88  SINGLE             VALUE 'S'.
               10  EMPLOYMENT-STATUS      PIC X(10).
               10  ANNUAL-INCOME          PIC 9(7)V99.
           05  POLICY-DETAILS.
               10  POLICY-TYPE            PIC X(4).
                   88  AUTO-POLICY        VALUE 'AUTO'.
                   88  LIFE-POLICY        VALUE 'LIFE'.
                   88  HOME-POLICY        VALUE 'HOME'.
               10  COVERAGE-AMOUNT        PIC 9(7)V99.
               10  REQUESTED-PREMIUM      PIC 9(6)V99.
               10  POLICY-TERM-YEARS      PIC 99.
           05  AUTO-SPECIFIC.
               10  DRIVING-YEARS          PIC 99.
               10  ACCIDENT-COUNT         PIC 99.
               10  VIOLATION-COUNT        PIC 99.
               10  DUI-HISTORY            PIC X(1).
                   88  HAS-DUI            VALUE 'Y'.
               10  VEHICLE-TYPE           PIC X(10).
               10  VEHICLE-AGE            PIC 99.
           05  LIFE-SPECIFIC.
               10  SMOKER-FLAG            PIC X(1).
                   88  IS-SMOKER          VALUE 'Y'.
               10  HEALTH-CONDITIONS      PIC X(50).
               10  BENEFICIARY-COUNT      PIC 99.
           05  EXISTING-POLICIES.
               10  HAS-OTHER-POLICIES     PIC X(1).
                   88  MULTI-POLICY       VALUE 'Y'.
               10  OTHER-POLICY-COUNT     PIC 99.

       01  VALIDATION-RESULTS.
           05  POLICY-STATUS              PIC X(10).
               88  APPROVED               VALUE 'APPROVED'.
               88  REJECTED               VALUE 'REJECTED'.
               88  PENDING                VALUE 'PENDING'.
           05  REJECTION-REASON           PIC X(50).
           05  CALCULATED-PREMIUM         PIC 9(6)V99.
           05  RISK-RATING                PIC X(10).

       PROCEDURE DIVISION.
       MAIN-PROGRAM.
           PERFORM VALIDATE-APPLICATION
           PERFORM CALCULATE-PREMIUM
           PERFORM DISPLAY-RESULTS
           STOP RUN.

       VALIDATE-APPLICATION.
      * Business Rule: Minimum age requirement
           IF APPLICANT-AGE < MIN-AGE
               MOVE 'REJECTED' TO POLICY-STATUS
               MOVE 'APPLICANT TOO YOUNG FOR INSURANCE' TO REJECTION-REASON
               GO TO VALIDATION-EXIT
           END-IF.

      * Business Rule: Maximum age restrictions by policy type
           IF AUTO-POLICY AND APPLICANT-AGE > MAX-AGE-AUTO
               MOVE 'REJECTED' TO POLICY-STATUS
               MOVE 'EXCEEDS MAXIMUM AGE FOR AUTO INSURANCE' TO REJECTION-REASON
               GO TO VALIDATION-EXIT
           END-IF.

           IF LIFE-POLICY AND APPLICANT-AGE > MAX-AGE-LIFE
               MOVE 'REJECTED' TO POLICY-STATUS
               MOVE 'EXCEEDS MAXIMUM AGE FOR LIFE INSURANCE' TO REJECTION-REASON
               GO TO VALIDATION-EXIT
           END-IF.

      * Business Rule: Credit score requirement
           IF CREDIT-SCORE < MIN-CREDIT-SCORE
               MOVE 'REJECTED' TO POLICY-STATUS
               MOVE 'CREDIT SCORE TOO LOW' TO REJECTION-REASON
               GO TO VALIDATION-EXIT
           END-IF.

      * Business Rule: Employment status validation
           IF EMPLOYMENT-STATUS = 'UNEMPLOYED'
               MOVE 'REJECTED' TO POLICY-STATUS
               MOVE 'UNEMPLOYED APPLICANTS NOT ELIGIBLE' TO REJECTION-REASON
               GO TO VALIDATION-EXIT
           END-IF.

      * Business Rule: Auto insurance specific validations
           IF AUTO-POLICY
               PERFORM AUTO-VALIDATION
           END-IF.

      * Business Rule: Life insurance specific validations
           IF LIFE-POLICY
               PERFORM LIFE-VALIDATION
           END-IF.

      * Business Rule: State restrictions
           IF APPLICANT-STATE = 'FL' OR APPLICANT-STATE = 'LA'
               IF AUTO-POLICY
                   MOVE 'PENDING' TO POLICY-STATUS
                   MOVE 'HIGH RISK STATE - MANUAL REVIEW REQUIRED' TO REJECTION-REASON
               END-IF
           END-IF.

      * Business Rule: Income verification for high coverage
           IF COVERAGE-AMOUNT > 500000
               IF ANNUAL-INCOME < 100000
                   MOVE 'REJECTED' TO POLICY-STATUS
                   MOVE 'INSUFFICIENT INCOME FOR COVERAGE AMOUNT' TO REJECTION-REASON
                   GO TO VALIDATION-EXIT
               END-IF
           END-IF.

           MOVE 'APPROVED' TO POLICY-STATUS.

       VALIDATION-EXIT.
           EXIT.

       AUTO-VALIDATION.
      * Business Rule: Minimum driving experience
           IF DRIVING-YEARS < MIN-DRIVING-YEARS
               MOVE 'REJECTED' TO POLICY-STATUS
               MOVE 'INSUFFICIENT DRIVING EXPERIENCE' TO REJECTION-REASON
               GO TO AUTO-VALIDATION-EXIT
           END-IF.

      * Business Rule: Maximum claims history
           IF ACCIDENT-COUNT > MAX-CLAIMS-ALLOWED
               MOVE 'REJECTED' TO POLICY-STATUS
               MOVE 'TOO MANY PREVIOUS ACCIDENTS' TO REJECTION-REASON
               GO TO AUTO-VALIDATION-EXIT
           END-IF.

      * Business Rule: DUI exclusion period
           IF HAS-DUI
               MOVE 'REJECTED' TO POLICY-STATUS
               MOVE 'DUI HISTORY - NOT ELIGIBLE' TO REJECTION-REASON
               GO TO AUTO-VALIDATION-EXIT
           END-IF.

      * Business Rule: Violation count restrictions
           IF VIOLATION-COUNT > 3
               MOVE 'REJECTED' TO POLICY-STATUS
               MOVE 'TOO MANY TRAFFIC VIOLATIONS' TO REJECTION-REASON
               GO TO AUTO-VALIDATION-EXIT
           END-IF.

      * Business Rule: High-risk vehicle types
           IF VEHICLE-TYPE = 'SPORTS' OR VEHICLE-TYPE = 'LUXURY'
               IF APPLICANT-AGE < 30
                   MOVE 'REJECTED' TO POLICY-STATUS
                   MOVE 'HIGH RISK VEHICLE FOR YOUNG DRIVER' TO REJECTION-REASON
                   GO TO AUTO-VALIDATION-EXIT
               END-IF
           END-IF.

      * Business Rule: Vehicle age restrictions
           IF VEHICLE-AGE > 15
               MOVE 'PENDING' TO POLICY-STATUS
               MOVE 'OLD VEHICLE - INSPECTION REQUIRED' TO REJECTION-REASON
           END-IF.

       AUTO-VALIDATION-EXIT.
           EXIT.

       LIFE-VALIDATION.
      * Business Rule: Smoker health risk assessment
           IF IS-SMOKER
               IF APPLICANT-AGE > 50
                   MOVE 'PENDING' TO POLICY-STATUS
                   MOVE 'SMOKER OVER 50 - MEDICAL EXAM REQUIRED' TO REJECTION-REASON
               END-IF
           END-IF.

      * Business Rule: High coverage amount restrictions
           IF COVERAGE-AMOUNT > 1000000
               MOVE 'PENDING' TO POLICY-STATUS
               MOVE 'HIGH COVERAGE - FINANCIAL VERIFICATION REQUIRED' TO REJECTION-REASON
           END-IF.

      * Business Rule: Health condition exclusions
           IF HEALTH-CONDITIONS NOT = SPACES
               MOVE 'PENDING' TO POLICY-STATUS
               MOVE 'HEALTH CONDITIONS - MEDICAL REVIEW REQUIRED' TO REJECTION-REASON
           END-IF.

      * Business Rule: Beneficiary validation
           IF BENEFICIARY-COUNT = 0
               MOVE 'REJECTED' TO POLICY-STATUS
               MOVE 'AT LEAST ONE BENEFICIARY REQUIRED' TO REJECTION-REASON
           END-IF.

       LIFE-VALIDATION-EXIT.
           EXIT.

       CALCULATE-PREMIUM.
           MOVE REQUESTED-PREMIUM TO CALCULATED-PREMIUM.

      * Business Rule: Young driver surcharge
           IF AUTO-POLICY AND APPLICANT-AGE < YOUNG-DRIVER-AGE
               COMPUTE CALCULATED-PREMIUM = CALCULATED-PREMIUM * 1.50
           END-IF.

      * Business Rule: Senior driver discount
           IF AUTO-POLICY AND APPLICANT-AGE > SENIOR-DRIVER-AGE
               IF MARRIED
                   COMPUTE CALCULATED-PREMIUM = CALCULATED-PREMIUM * 0.90
               END-IF
           END-IF.

      * Business Rule: Smoker surcharge for life insurance
           IF LIFE-POLICY AND IS-SMOKER
               COMPUTE CALCULATED-PREMIUM = CALCULATED-PREMIUM * 
                   (1 + SMOKER-SURCHARGE-PCT / 100)
           END-IF.

      * Business Rule: Multi-policy discount
           IF MULTI-POLICY
               COMPUTE CALCULATED-PREMIUM = CALCULATED-PREMIUM * 
                   (1 - MULTI-POLICY-DISCOUNT / 100)
           END-IF.

      * Business Rule: Premium caps by policy type
           IF AUTO-POLICY AND CALCULATED-PREMIUM > MAX-PREMIUM-AUTO
               MOVE MAX-PREMIUM-AUTO TO CALCULATED-PREMIUM
           END-IF.

           IF LIFE-POLICY AND CALCULATED-PREMIUM > MAX-PREMIUM-LIFE
               MOVE MAX-PREMIUM-LIFE TO CALCULATED-PREMIUM
           END-IF.

      * Business Rule: High-risk state surcharge
           IF APPLICANT-STATE = 'FL' OR APPLICANT-STATE = 'CA'
               COMPUTE CALCULATED-PREMIUM = CALCULATED-PREMIUM * 1.15
           END-IF.

       CALCULATE-PREMIUM-EXIT.
           EXIT.

       DISPLAY-RESULTS.
           DISPLAY 'POLICY APPLICATION RESULTS:'
           DISPLAY 'APPLICANT: ' APPLICANT-NAME
           DISPLAY 'STATUS: ' POLICY-STATUS
           DISPLAY 'PREMIUM: $' CALCULATED-PREMIUM
           IF NOT APPROVED
               DISPLAY 'REASON: ' REJECTION-REASON
           END-IF.

       DISPLAY-RESULTS-EXIT.
           EXIT.