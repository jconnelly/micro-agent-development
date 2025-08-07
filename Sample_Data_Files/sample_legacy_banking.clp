;; Banking Loan Approval Rules - JESS/CLIPS Format
;; Contains business rules for loan underwriting, credit assessment, and approval workflows

(deftemplate loan-application
   (slot application-id)
   (slot applicant-name)
   (slot loan-amount)
   (slot loan-type)
   (slot credit-score)
   (slot annual-income)
   (slot employment-years)
   (slot debt-to-income)
   (slot down-payment)
   (slot property-value)
   (slot bankruptcy-history)
   (slot foreclosure-history)
   (slot late-payments)
   (slot status (default "PENDING"))
   (slot approval-amount (default 0))
   (slot interest-rate (default 0))
   (multislot rejection-reasons)
   (multislot conditions))

(deftemplate credit-profile
   (slot application-id)
   (slot credit-score)
   (slot credit-history-length)
   (slot open-accounts)
   (slot credit-utilization)
   (slot recent-inquiries)
   (slot payment-history)
   (slot risk-category))

(deftemplate employment-verification
   (slot application-id)
   (slot employer-name)
   (slot employment-type)
   (slot years-employed)
   (slot income-verified)
   (slot income-stability))

;; Minimum credit score requirements by loan type
(defrule minimum-credit-score-conventional
   ?app <- (loan-application (loan-type "CONVENTIONAL")
                           (credit-score ?score&:(< ?score 620))
                           (status "PENDING"))
   =>
   (modify ?app (status "REJECTED")
               (rejection-reasons "Credit score below minimum 620 for conventional loan")))

(defrule minimum-credit-score-fha
   ?app <- (loan-application (loan-type "FHA")
                           (credit-score ?score&:(< ?score 580))
                           (status "PENDING"))
   =>
   (modify ?app (status "REJECTED")
               (rejection-reasons "Credit score below minimum 580 for FHA loan")))

(defrule minimum-credit-score-va
   ?app <- (loan-application (loan-type "VA")
                           (credit-score ?score&:(< ?score 600))
                           (status "PENDING"))
   =>
   (modify ?app (status "REJECTED")
               (rejection-reasons "Credit score below minimum 600 for VA loan")))

(defrule minimum-credit-score-jumbo
   ?app <- (loan-application (loan-type "JUMBO")
                           (credit-score ?score&:(< ?score 700))
                           (status "PENDING"))
   =>
   (modify ?app (status "REJECTED")
               (rejection-reasons "Credit score below minimum 700 for jumbo loan")))

;; Debt-to-income ratio rules
(defrule high-debt-to-income-conventional
   ?app <- (loan-application (loan-type "CONVENTIONAL")
                           (debt-to-income ?dti&:(> ?dti 43))
                           (status "PENDING"))
   =>
   (modify ?app (status "REJECTED")
               (rejection-reasons "Debt-to-income ratio exceeds 43% for conventional loan")))

(defrule high-debt-to-income-fha
   ?app <- (loan-application (loan-type "FHA")
                           (debt-to-income ?dti&:(> ?dti 57))
                           (status "PENDING"))
   =>
   (modify ?app (status "REJECTED")
               (rejection-reasons "Debt-to-income ratio exceeds 57% for FHA loan")))

(defrule moderate-debt-to-income-warning
   ?app <- (loan-application (debt-to-income ?dti&:(and (> ?dti 36) (< ?dti 43)))
                           (status "PENDING"))
   =>
   (modify ?app (conditions "Manual underwriting required - DTI between 36-43%")))

;; Employment stability requirements
(defrule insufficient-employment-history
   ?app <- (loan-application (employment-years ?years&:(< ?years 2))
                           (status "PENDING"))
   =>
   (modify ?app (status "REJECTED")
               (rejection-reasons "Minimum 2 years employment history required")))

(defrule self-employed-income-verification
   ?app <- (loan-application (status "PENDING"))
   (employment-verification (application-id ?id)
                          (employment-type "SELF_EMPLOYED")
                          (income-verified FALSE))
   (test (eq ?id (fact-slot-value ?app application-id)))
   =>
   (modify ?app (conditions "Two years tax returns required for self-employed applicants")))

;; Down payment requirements
(defrule insufficient-down-payment-conventional
   ?app <- (loan-application (loan-type "CONVENTIONAL")
                           (loan-amount ?amount)
                           (down-payment ?down)
                           (status "PENDING"))
   (test (< (/ ?down ?amount) 0.05))  ; Less than 5% down
   =>
   (modify ?app (status "REJECTED")
               (rejection-reasons "Minimum 5% down payment required for conventional loan")))

(defrule pmi-required-conventional
   ?app <- (loan-application (loan-type "CONVENTIONAL")
                           (loan-amount ?amount)
                           (down-payment ?down)
                           (status "PENDING"))
   (test (< (/ ?down ?amount) 0.20))  ; Less than 20% down
   =>
   (modify ?app (conditions "Private Mortgage Insurance (PMI) required")))

(defrule insufficient-down-payment-jumbo
   ?app <- (loan-application (loan-type "JUMBO")
                           (loan-amount ?amount)
                           (down-payment ?down)
                           (status "PENDING"))
   (test (< (/ ?down ?amount) 0.20))  ; Less than 20% down
   =>
   (modify ?app (status "REJECTED")
               (rejection-reasons "Minimum 20% down payment required for jumbo loan")))

;; Loan-to-value ratio checks
(defrule high-loan-to-value
   ?app <- (loan-application (loan-amount ?amount)
                           (property-value ?value)
                           (status "PENDING"))
   (test (> (/ ?amount ?value) 0.95))  ; LTV over 95%
   =>
   (modify ?app (status "REJECTED")
               (rejection-reasons "Loan-to-value ratio exceeds maximum 95%")))

;; Bankruptcy history rules
(defrule recent-chapter-7-bankruptcy
   ?app <- (loan-application (bankruptcy-history "CHAPTER_7")
                           (status "PENDING"))
   ;; Assuming bankruptcy date is within last 4 years (simplified)
   =>
   (modify ?app (status "REJECTED")
               (rejection-reasons "Chapter 7 bankruptcy within last 4 years")))

(defrule recent-chapter-13-bankruptcy
   ?app <- (loan-application (bankruptcy-history "CHAPTER_13")
                           (status "PENDING"))
   ;; Assuming bankruptcy date is within last 2 years (simplified)
   =>
   (modify ?app (status "REJECTED")
               (rejection-reasons "Chapter 13 bankruptcy within last 2 years")))

;; Foreclosure history rules
(defrule recent-foreclosure
   ?app <- (loan-application (foreclosure-history TRUE)
                           (status "PENDING"))
   =>
   (modify ?app (status "REJECTED")
               (rejection-reasons "Foreclosure within last 7 years")))

;; Credit score based interest rate tiers
(defrule excellent-credit-rate
   ?app <- (loan-application (credit-score ?score&:(>= ?score 760))
                           (status "PENDING")
                           (interest-rate 0))
   =>
   (modify ?app (interest-rate 3.25)))

(defrule good-credit-rate
   ?app <- (loan-application (credit-score ?score&:(and (>= ?score 700) (< ?score 760)))
                           (status "PENDING")
                           (interest-rate 0))
   =>
   (modify ?app (interest-rate 3.50)))

(defrule fair-credit-rate
   ?app <- (loan-application (credit-score ?score&:(and (>= ?score 640) (< ?score 700)))
                           (status "PENDING")
                           (interest-rate 0))
   =>
   (modify ?app (interest-rate 3.875)))

(defrule below-average-credit-rate
   ?app <- (loan-application (credit-score ?score&:(and (>= ?score 580) (< ?score 640)))
                           (status "PENDING")
                           (interest-rate 0))
   =>
   (modify ?app (interest-rate 4.25)))

;; Income verification rules
(defrule high-income-fast-track
   ?app <- (loan-application (annual-income ?income&:(> ?income 150000))
                           (credit-score ?score&:(>= ?score 740))
                           (debt-to-income ?dti&:(< ?dti 28))
                           (status "PENDING"))
   =>
   (modify ?app (conditions "Eligible for fast-track processing")))

(defrule low-income-additional-review
   ?app <- (loan-application (annual-income ?income&:(< ?income 40000))
                           (status "PENDING"))
   =>
   (modify ?app (conditions "Additional income documentation required")))

;; Asset verification requirements
(defrule large-loan-asset-verification
   ?app <- (loan-application (loan-amount ?amount&:(> ?amount 500000))
                           (status "PENDING"))
   =>
   (modify ?app (conditions "Bank statements and asset verification required for loans over $500,000")))

;; First-time homebuyer programs
(defrule first-time-buyer-benefits
   ?app <- (loan-application (status "PENDING"))
   ;; Assuming first-time buyer flag exists (simplified)
   =>
   (modify ?app (conditions "Eligible for first-time homebuyer programs and grants")))

;; Jumbo loan specific rules
(defrule jumbo-loan-requirements
   ?app <- (loan-application (loan-type "JUMBO")
                           (status "PENDING")
                           (credit-score ?score)
                           (debt-to-income ?dti))
   (test (and (>= ?score 700) (< ?dti 38)))
   =>
   (modify ?app (conditions "Additional cash reserves equal to 6 months payments required")))

;; Investment property rules
(defrule investment-property-requirements
   ?app <- (loan-application (status "PENDING"))
   ;; Assuming property type is investment (simplified)
   =>
   (modify ?app (conditions "Investment property requires 25% down payment and 6 months reserves")))

;; Multiple late payments penalty
(defrule excessive-late-payments
   ?app <- (loan-application (late-payments ?late&:(> ?late 6))
                           (status "PENDING"))
   =>
   (modify ?app (status "REJECTED")
               (rejection-reasons "More than 6 late payments in last 12 months")))

;; Final approval rule - all conditions met
(defrule loan-approval
   ?app <- (loan-application (status "PENDING")
                           (loan-amount ?amount)
                           (interest-rate ?rate&:(> ?rate 0)))
   ;; No rejection reasons exist
   (not (loan-application (application-id ?id) 
                         (rejection-reasons ~nil)))
   =>
   (modify ?app (status "APPROVED")
               (approval-amount ?amount)))

;; Conditional approval rule
(defrule conditional-approval
   ?app <- (loan-application (status "PENDING")
                           (interest-rate ?rate&:(> ?rate 0))
                           (conditions ?cond&~nil))
   ;; Has conditions but no rejection reasons
   (not (loan-application (application-id ?id)
                         (rejection-reasons ~nil)))
   =>
   (modify ?app (status "CONDITIONALLY_APPROVED")))

;; Credit utilization impact
(defrule high-credit-utilization
   ?app <- (loan-application (status "PENDING"))
   (credit-profile (application-id ?id)
                  (credit-utilization ?util&:(> ?util 0.75)))
   (test (eq ?id (fact-slot-value ?app application-id)))
   =>
   (modify ?app (conditions "High credit utilization - consider paying down balances before closing")))

;; Recent credit inquiries warning
(defrule excessive-credit-inquiries
   ?app <- (loan-application (status "PENDING"))
   (credit-profile (application-id ?id)
                  (recent-inquiries ?inq&:(> ?inq 6)))
   (test (eq ?id (fact-slot-value ?app application-id)))
   =>
   (modify ?app (conditions "Multiple recent credit inquiries may indicate credit shopping or financial stress")))

(printout t "Banking Loan Approval Rules Loaded" crlf)
(printout t "System ready for loan application processing" crlf)