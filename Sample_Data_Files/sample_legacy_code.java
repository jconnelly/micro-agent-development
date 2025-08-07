// src/main/java/com/example/loan/LoanProcessor.java

package com.example.loan;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.Period;
import java.util.logging.Logger; // Functional: Logging utility
import java.util.List;
import java.util.Arrays;

public class LoanProcessor {

    private static final Logger logger = Logger.getLogger(LoanProcessor.class.getName()); // Functional: Logger instance

    // Business Rule: Minimum loan amount
    private static final BigDecimal MIN_LOAN_AMOUNT = new BigDecimal("1000.00");
    // Business Rule: Maximum loan amount for regular customers
    private static final BigDecimal MAX_LOAN_AMOUNT = new BigDecimal("50000.00");
    // Business Rule: Maximum loan amount for premium customers
    private static final BigDecimal MAX_LOAN_AMOUNT_PREMIUM = new BigDecimal("100000.00");
    // Business Rule: Maximum loan amount for first-time borrowers
    private static final BigDecimal MAX_LOAN_AMOUNT_FIRST_TIME = new BigDecimal("15000.00");
    // Business Rule: Minimum credit score for standard approval
    private static final int MIN_CREDIT_SCORE_STANDARD = 680;
    // Business Rule: Minimum credit score for high-risk approval
    private static final int MIN_CREDIT_SCORE_HIGH_RISK = 600;
    // Business Rule: Minimum credit score for first-time borrowers
    private static final int MIN_CREDIT_SCORE_FIRST_TIME = 620;
    // Business Rule: Maximum debt-to-income ratio
    private static final double MAX_DTI_RATIO = 0.40; // 40%
    // Business Rule: Maximum debt-to-income ratio for premium customers
    private static final double MAX_DTI_RATIO_PREMIUM = 0.50; // 50%
    // Business Rule: Minimum annual income requirement
    private static final BigDecimal MIN_ANNUAL_INCOME = new BigDecimal("25000.00");
    // Business Rule: Minimum annual income for premium loans
    private static final BigDecimal MIN_ANNUAL_INCOME_PREMIUM = new BigDecimal("75000.00");
    // Business Rule: Minimum age for loan application
    private static final int MIN_AGE = 18;
    // Business Rule: Maximum age for loan application
    private static final int MAX_AGE = 75;
    // Business Rule: Maximum age for long-term loans (>5 years)
    private static final int MAX_AGE_LONG_TERM = 65;
    // Business Rule: Minimum employment period in months
    private static final int MIN_EMPLOYMENT_MONTHS = 12;
    // Business Rule: Minimum employment period for self-employed in months
    private static final int MIN_EMPLOYMENT_MONTHS_SELF_EMPLOYED = 24;
    // Business Rule: Maximum loan term in years
    private static final int MAX_LOAN_TERM_YEARS = 30;
    // Business Rule: Minimum loan term in years
    private static final int MIN_LOAN_TERM_YEARS = 1;
    // Business Rule: Interest rate cap for premium customers
    private static final BigDecimal MAX_INTEREST_RATE_PREMIUM = new BigDecimal("0.08"); // 8%
    // Business Rule: Interest rate floor
    private static final BigDecimal MIN_INTEREST_RATE = new BigDecimal("0.035"); // 3.5%
    // Business Rule: Late payment penalty rate
    private static final BigDecimal LATE_PAYMENT_PENALTY_RATE = new BigDecimal("0.05"); // 5%

    /**
     * Processes a loan application to determine eligibility and suggested interest rate.
     */
    public LoanDecision processLoanApplication(String applicantName, BigDecimal loanAmount,
                                               int creditScore, BigDecimal annualIncome,
                                               BigDecimal monthlyDebtPayments, LocalDate applicationDate,
                                               LocalDate birthDate, String employmentType, 
                                               int employmentMonths, int loanTermYears,
                                               boolean isPremiumCustomer, boolean isFirstTimeBorrower,
                                               String loanPurpose, String collateralType,
                                               BigDecimal collateralValue, List<String> previousLoanDefaults) {

        logger.info("Processing loan application for: " + applicantName); // Functional: Log entry

        // Functional: Input validation
        if (loanAmount == null || loanAmount.compareTo(BigDecimal.ZERO) <= 0) {
            return new LoanDecision("REJECTED", "Loan amount must be positive.", "Invalid Input");
        }
        if (creditScore <= 0) {
            return new LoanDecision("REJECTED", "Credit score must be positive.", "Invalid Input");
        }
        if (annualIncome == null || annualIncome.compareTo(BigDecimal.ZERO) <= 0) {
            return new LoanDecision("REJECTED", "Annual income must be positive.", "Invalid Input");
        }

        // Business Rule: Age validation
        int age = Period.between(birthDate, LocalDate.now()).getYears();
        if (age < MIN_AGE) {
            return new LoanDecision("REJECTED", "Applicant must be at least 18 years old.", "Age Too Low");
        }
        if (age > MAX_AGE) {
            return new LoanDecision("REJECTED", "Applicant exceeds maximum age limit.", "Age Too High");
        }

        // Business Rule: Age restriction for long-term loans
        if (loanTermYears > 5 && age > MAX_AGE_LONG_TERM) {
            return new LoanDecision("REJECTED", "Age too high for long-term loans.", "Age Restriction");
        }

        // Business Rule: Loan term validation
        if (loanTermYears < MIN_LOAN_TERM_YEARS) {
            return new LoanDecision("REJECTED", "Loan term too short.", "Term Too Short");
        }
        if (loanTermYears > MAX_LOAN_TERM_YEARS) {
            return new LoanDecision("REJECTED", "Loan term exceeds maximum allowed.", "Term Too Long");
        }

        // Business Rule: Employment validation
        if (employmentType.equals("UNEMPLOYED")) {
            return new LoanDecision("REJECTED", "Unemployed applicants not eligible.", "Employment Issue");
        }
        if (employmentType.equals("SELF_EMPLOYED") && employmentMonths < MIN_EMPLOYMENT_MONTHS_SELF_EMPLOYED) {
            return new LoanDecision("REJECTED", "Self-employed applicants need minimum 24 months employment.", "Employment Duration");
        }
        if (!employmentType.equals("SELF_EMPLOYED") && employmentMonths < MIN_EMPLOYMENT_MONTHS) {
            return new LoanDecision("REJECTED", "Minimum 12 months employment required.", "Employment Duration");
        }

        // Business Rule: Income validation
        if (annualIncome.compareTo(MIN_ANNUAL_INCOME) < 0) {
            return new LoanDecision("REJECTED", "Annual income below minimum requirement.", "Income Too Low");
        }

        // Business Rule: Premium customer income requirement
        if (isPremiumCustomer && annualIncome.compareTo(MIN_ANNUAL_INCOME_PREMIUM) < 0) {
            return new LoanDecision("REJECTED", "Premium customers need higher income.", "Premium Income Requirement");
        }

        // Business Rule: Previous defaults check
        if (previousLoanDefaults != null && !previousLoanDefaults.isEmpty()) {
            if (previousLoanDefaults.size() > 2) {
                return new LoanDecision("REJECTED", "Too many previous loan defaults.", "Default History");
            }
            if (previousLoanDefaults.contains("RECENT_BANKRUPTCY")) {
                return new LoanDecision("REJECTED", "Recent bankruptcy on record.", "Bankruptcy History");
            }
            if (previousLoanDefaults.contains("FORECLOSURE")) {
                return new LoanDecision("REJECTED", "Foreclosure history present.", "Foreclosure History");
            }
        }

        // Business Rule: Loan purpose restrictions
        if (loanPurpose.equals("GAMBLING") || loanPurpose.equals("ILLEGAL_ACTIVITY")) {
            return new LoanDecision("REJECTED", "Loan purpose not acceptable.", "Purpose Restriction");
        }

        // Business Rule: Business loans require higher credit score
        if (loanPurpose.equals("BUSINESS") && creditScore < 650) {
            return new LoanDecision("REJECTED", "Business loans require higher credit score.", "Business Credit Requirement");
        }

        // Business Rule: Education loans have special DTI allowance
        double dtiLimit = MAX_DTI_RATIO;
        if (loanPurpose.equals("EDUCATION")) {
            dtiLimit = 0.45; // 45% for education loans
        }

        // Business Rule: Premium customer DTI allowance
        if (isPremiumCustomer) {
            dtiLimit = MAX_DTI_RATIO_PREMIUM;
        }

        // Business Rule: Check loan amount limits based on customer type
        BigDecimal maxAllowedAmount = MAX_LOAN_AMOUNT;
        if (isFirstTimeBorrower) {
            maxAllowedAmount = MAX_LOAN_AMOUNT_FIRST_TIME;
        } else if (isPremiumCustomer) {
            maxAllowedAmount = MAX_LOAN_AMOUNT_PREMIUM;
        }

        if (loanAmount.compareTo(MIN_LOAN_AMOUNT) < 0) {
            return new LoanDecision("REJECTED", "Requested loan amount is below minimum allowed.", "Amount Too Low");
        }
        if (loanAmount.compareTo(maxAllowedAmount) > 0) {
            return new LoanDecision("REJECTED", "Requested loan amount exceeds maximum allowed.", "Amount Too High");
        }

        // Business Rule: Collateral requirements for large loans
        if (loanAmount.compareTo(new BigDecimal("30000.00")) > 0 && 
            (collateralType == null || collateralType.equals("NONE"))) {
            return new LoanDecision("REJECTED", "Collateral required for loans over $30,000.", "Collateral Required");
        }

        // Business Rule: Collateral value must exceed loan amount
        if (collateralValue != null && collateralValue.compareTo(loanAmount) < 0) {
            return new LoanDecision("REJECTED", "Collateral value insufficient.", "Insufficient Collateral");
        }

        // Business Rule: Calculate Debt-to-Income Ratio
        double dtiRatio = monthlyDebtPayments.doubleValue() / (annualIncome.doubleValue() / 12.0);
        if (dtiRatio > dtiLimit) {
            return new LoanDecision("REJECTED", "Debt-to-income ratio exceeds maximum allowed.", "High DTI");
        }

        // Business Rule: Credit score requirements based on customer type
        int minCreditScore = MIN_CREDIT_SCORE_HIGH_RISK;
        if (isFirstTimeBorrower) {
            minCreditScore = MIN_CREDIT_SCORE_FIRST_TIME;
        }

        // Business Rule: Higher credit score required for unsecured loans
        if (collateralType == null || collateralType.equals("NONE")) {
            minCreditScore = Math.max(minCreditScore, 640);
        }

        // Business Rule: Luxury purchases require higher credit score
        if (loanPurpose.equals("LUXURY") || loanPurpose.equals("VACATION")) {
            minCreditScore = Math.max(minCreditScore, 700);
        }

        // Business Rule: Medical emergency loans have relaxed credit requirements
        if (loanPurpose.equals("MEDICAL_EMERGENCY")) {
            minCreditScore = Math.min(minCreditScore, 580);
        }

        // Business Rule: Determine eligibility based on credit score
        String decision = "PENDING_REVIEW";
        String reason = "Requires further human review.";
        BigDecimal interestRate = calculateInterestRate(creditScore, loanAmount, isPremiumCustomer, 
                                                       loanTermYears, collateralType, loanPurpose);

        if (creditScore >= MIN_CREDIT_SCORE_STANDARD) {
            decision = "APPROVED";
            reason = "Meets standard credit score requirements.";
        } else if (creditScore >= minCreditScore) {
            decision = "APPROVED_HIGH_RISK";
            reason = "Approved as high-risk due to lower credit score, higher interest rate applied.";
        } else {
            decision = "REJECTED";
            reason = "Credit score is too low for any loan approval.";
        }

        // Business Rule: Weekend applications require manual review
        if (applicationDate.getDayOfWeek().getValue() >= 6) { // Saturday or Sunday
            if (decision.equals("APPROVED")) {
                decision = "PENDING_REVIEW";
                reason = "Weekend applications require manual review.";
            }
        }

        // Business Rule: Large loan amounts require senior approval
        if (loanAmount.compareTo(new BigDecimal("75000.00")) > 0) {
            if (decision.equals("APPROVED")) {
                decision = "PENDING_SENIOR_APPROVAL";
                reason = "Large loan amounts require senior management approval.";
            }
        }

        // Business Rule: International applicants require additional verification
        if (applicantName.matches(".*[^\\p{ASCII}].*")) { // Contains non-ASCII characters
            if (decision.equals("APPROVED")) {
                decision = "PENDING_VERIFICATION";
                reason = "International applicants require additional verification.";
            }
        }

        // Functional: Log final decision
        logger.info("Application for " + applicantName + " resulted in: " + decision);

        return new LoanDecision(decision, reason, "Eligibility", interestRate);
    }

    /**
     * Business Rule: Calculates the suggested annual interest rate based on multiple factors.
     */
    private BigDecimal calculateInterestRate(int creditScore, BigDecimal loanAmount, 
                                           boolean isPremiumCustomer, int loanTermYears,
                                           String collateralType, String loanPurpose) {
        BigDecimal baseRate = new BigDecimal("0.05"); // 5% base

        // Business Rule: Credit score impact on interest rate
        if (creditScore < 600) {
            baseRate = baseRate.add(new BigDecimal("0.05")); // Add 5% for very low scores
        } else if (creditScore < 650) {
            baseRate = baseRate.add(new BigDecimal("0.03")); // Add 3% for low scores
        } else if (creditScore < 700) {
            baseRate = baseRate.add(new BigDecimal("0.01")); // Add 1% for fair scores
        } else if (creditScore >= 750) {
            baseRate = baseRate.subtract(new BigDecimal("0.005")); // Subtract 0.5% for excellent scores
        }

        // Business Rule: Large loan amount penalty
        if (loanAmount.compareTo(new BigDecimal("25000.00")) > 0) {
            baseRate = baseRate.add(new BigDecimal("0.01")); // Add 1% for larger loans
        }

        // Business Rule: Very large loan amount additional penalty
        if (loanAmount.compareTo(new BigDecimal("50000.00")) > 0) {
            baseRate = baseRate.add(new BigDecimal("0.015")); // Add additional 1.5%
        }

        // Business Rule: Premium customer discount
        if (isPremiumCustomer) {
            baseRate = baseRate.subtract(new BigDecimal("0.02")); // 2% discount
        }

        // Business Rule: Long-term loan rate adjustment
        if (loanTermYears > 10) {
            baseRate = baseRate.add(new BigDecimal("0.005")); // Add 0.5% for long terms
        }
        if (loanTermYears > 20) {
            baseRate = baseRate.add(new BigDecimal("0.01")); // Add additional 1% for very long terms
        }

        // Business Rule: Short-term loan rate adjustment
        if (loanTermYears <= 2) {
            baseRate = baseRate.subtract(new BigDecimal("0.005")); // Subtract 0.5% for short terms
        }

        // Business Rule: Collateral impact on interest rate
        if (collateralType != null) {
            if (collateralType.equals("REAL_ESTATE")) {
                baseRate = baseRate.subtract(new BigDecimal("0.015")); // 1.5% discount for real estate
            } else if (collateralType.equals("VEHICLE")) {
                baseRate = baseRate.subtract(new BigDecimal("0.01")); // 1% discount for vehicles
            } else if (collateralType.equals("SECURITIES")) {
                baseRate = baseRate.subtract(new BigDecimal("0.02")); // 2% discount for securities
            }
        } else {
            baseRate = baseRate.add(new BigDecimal("0.01")); // 1% penalty for unsecured loans
        }

        // Business Rule: Loan purpose impact on interest rate
        if (loanPurpose != null) {
            switch (loanPurpose) {
                case "HOME_IMPROVEMENT":
                    baseRate = baseRate.subtract(new BigDecimal("0.005")); // 0.5% discount
                    break;
                case "EDUCATION":
                    baseRate = baseRate.subtract(new BigDecimal("0.01")); // 1% discount
                    break;
                case "MEDICAL_EMERGENCY":
                    baseRate = baseRate.subtract(new BigDecimal("0.015")); // 1.5% discount
                    break;
                case "DEBT_CONSOLIDATION":
                    baseRate = baseRate.add(new BigDecimal("0.005")); // 0.5% penalty
                    break;
                case "LUXURY":
                case "VACATION":
                    baseRate = baseRate.add(new BigDecimal("0.02")); // 2% penalty
                    break;
                case "BUSINESS":
                    baseRate = baseRate.add(new BigDecimal("0.015")); // 1.5% penalty
                    break;
            }
        }

        // Business Rule: Rate boundaries
        if (baseRate.compareTo(MIN_INTEREST_RATE) < 0) {
            baseRate = MIN_INTEREST_RATE;
        }
        if (isPremiumCustomer && baseRate.compareTo(MAX_INTEREST_RATE_PREMIUM) > 0) {
            baseRate = MAX_INTEREST_RATE_PREMIUM;
        }

        // Functional: Ensure rate is not negative
        return baseRate.max(BigDecimal.ZERO);
    }

    /**
     * Business Rule: Calculate late payment penalty
     */
    public BigDecimal calculateLatePenalty(BigDecimal outstandingBalance, int daysLate) {
        if (daysLate <= 0) {
            return BigDecimal.ZERO;
        }

        // Business Rule: Grace period for late payments
        if (daysLate <= 5) {
            return BigDecimal.ZERO; // 5-day grace period
        }

        // Business Rule: Progressive penalty rates
        BigDecimal penaltyRate = LATE_PAYMENT_PENALTY_RATE;
        if (daysLate > 30) {
            penaltyRate = penaltyRate.add(new BigDecimal("0.02")); // Additional 2% after 30 days
        }
        if (daysLate > 60) {
            penaltyRate = penaltyRate.add(new BigDecimal("0.03")); // Additional 3% after 60 days
        }

        // Business Rule: Minimum penalty amount
        BigDecimal penalty = outstandingBalance.multiply(penaltyRate);
        BigDecimal minPenalty = new BigDecimal("25.00");
        return penalty.max(minPenalty);
    }

    /**
     * Business Rule: Determine if refinancing is beneficial
     */
    public boolean isRefinancingBeneficial(BigDecimal currentRate, BigDecimal newRate, 
                                         BigDecimal remainingBalance, int remainingMonths) {
        // Business Rule: Minimum rate difference for refinancing
        BigDecimal rateDifference = currentRate.subtract(newRate);
        if (rateDifference.compareTo(new BigDecimal("0.005")) < 0) { // Less than 0.5% difference
            return false;
        }

        // Business Rule: Minimum time remaining for refinancing
        if (remainingMonths < 24) {
            return false;
        }

        // Business Rule: Minimum balance for refinancing
        if (remainingBalance.compareTo(new BigDecimal("10000.00")) < 0) {
            return false;
        }

        return true;
    }

    /**
     * Functional: Utility method to format a date.
     */
    public String formatDate(LocalDate date) {
        if (date == null) {
            return "N/A";
        }
        return date.toString(); // Simple ISO format
    }

    // Functional: Inner class for loan decision
    public static class LoanDecision {
        private String status;
        private String message;
        private String category;
        private BigDecimal suggestedInterestRate;

        public LoanDecision(String status, String message, String category) {
            this(status, message, category, null);
        }

        public LoanDecision(String status, String message, String category, BigDecimal suggestedInterestRate) {
            this.status = status;
            this.message = message;
            this.category = category;
            this.suggestedInterestRate = suggestedInterestRate;
        }

        // Getters (functional)
        public String getStatus() { return status; }
        public String getMessage() { return message; }
        public String getCategory() { return category; }
        public BigDecimal getSuggestedInterestRate() { return suggestedInterestRate; }

        @Override
        public String toString() {
            return "LoanDecision{" +
                   "status='" + status + '\'' +
                   ", message='" + message + '\'' +
                   ", category='" + category + '\'' +
                   ", suggestedInterestRate=" + (suggestedInterestRate!= null? suggestedInterestRate.toPlainString() : "N/A") +
                   '}';
        }
    }
}