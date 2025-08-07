PATIENT ; Healthcare Patient Management System - MUMPS
    ; This system contains complex business rules for patient eligibility,
    ; treatment authorization, and billing validation
    
CHECKELIG(PATID,TREATCD) ; Check patient eligibility for treatment
    NEW RESULT,AGE,INSURANCE,PREAUTH,COPAY
    SET RESULT=0
    
    ; Get patient demographics
    SET AGE=$$GETAGE(PATID)
    SET INSURANCE=$$GETINS(PATID)
    
    ; Age-based treatment restrictions
    IF TREATCD="PEDIATRIC" DO
    . IF AGE<18 SET RESULT=1
    . IF AGE>=65,$$HASMedicare(PATID) SET RESULT=1
    
    ; Insurance coverage validation
    IF TREATCD="SURGERY" DO
    . IF INSURANCE="PREMIUM" SET RESULT=1
    . IF INSURANCE="BASIC",$$PREAUTH(PATID,TREATCD) SET RESULT=1
    
    ; Mental health parity requirements
    IF TREATCD="MENTAL_HEALTH" DO
    . IF $$MENTALDAYS(PATID)<30 SET RESULT=1
    . IF $$INPATIENT(PATID)>7 SET RESULT=0 ; Limit inpatient stays
    
    ; Substance abuse treatment rules
    IF TREATCD="SUBSTANCE_ABUSE" DO
    . IF $$PRIORAUTH(PATID,"SA") SET RESULT=1
    . IF $$DAYSINTREAT(PATID)>90 SET RESULT=0 ; 90-day limit per year
    
    ; Emergency treatment override
    IF $$EMERGENCY(TREATCD) SET RESULT=1
    
    QUIT RESULT

CALCCOPAY(PATID,TREATCD,COST) ; Calculate patient copay based on insurance and treatment
    NEW COPAY,DEDUCTIBLE,COINSURE,MAXOOP
    SET COPAY=0
    
    ; Get insurance details
    SET DEDUCTIBLE=$$GETDEDUCT(PATID)
    SET COINSURE=$$GETCOINS(PATID)
    SET MAXOOP=$$GETMAXOOP(PATID)
    
    ; Preventive care - no copay
    IF $$ISPREVENT(TREATCD) QUIT 0
    
    ; Apply deductible first
    IF $$YTDPAID(PATID)<DEDUCTIBLE DO
    . SET COPAY=COPAY+(DEDUCTIBLE-$$YTDPAID(PATID))
    . IF COPAY>COST SET COPAY=COST
    
    ; Apply coinsurance to remaining amount
    IF COST>COPAY DO
    . SET COPAY=COPAY+((COST-COPAY)*(COINSURE/100))
    
    ; Check maximum out-of-pocket limit
    IF ($$YTDPAID(PATID)+COPAY)>MAXOOP DO
    . SET COPAY=MAXOOP-$$YTDPAID(PATID)
    . IF COPAY<0 SET COPAY=0
    
    ; Senior citizen discount (65+)
    IF $$GETAGE(PATID)>=65 SET COPAY=COPAY*0.8
    
    ; Low-income adjustment
    IF $$INCOME(PATID)<25000 SET COPAY=COPAY*0.5
    
    QUIT COPAY

VALIDATEMEDS(PATID,MEDLIST) ; Validate medication prescriptions
    NEW I,MED,VALID,ALLERGIES,INTERACTIONS
    SET VALID=1
    SET ALLERGIES=$$GETALLERG(PATID)
    
    ; Check each medication
    FOR I=1:1:$LENGTH(MEDLIST,",") DO  QUIT:'VALID
    . SET MED=$PIECE(MEDLIST,",",I)
    . 
    . ; Check allergies
    . IF $$ISALLERGIC(ALLERGIES,MED) DO
    . . WRITE "ALLERGY ALERT: Patient allergic to ",MED,!
    . . SET VALID=0
    . 
    . ; Age-based medication restrictions
    . IF $$GETAGE(PATID)<18,$$ISADULTONLY(MED) DO
    . . WRITE "AGE RESTRICTION: ",MED," not approved for pediatric use",!
    . . SET VALID=0
    . 
    . ; Pregnancy category warnings
    . IF $$ISPREGNANT(PATID),$$PREGCAT(MED)="X" DO
    . . WRITE "PREGNANCY WARNING: ",MED," contraindicated in pregnancy",!
    . . SET VALID=0
    . 
    . ; Drug interactions
    . SET INTERACTIONS=$$CHECKINTERACT($$CURRENTMEDS(PATID),MED)
    . IF INTERACTIONS'="" DO
    . . WRITE "DRUG INTERACTION: ",MED," interacts with: ",INTERACTIONS,!
    . . SET VALID=0
    . 
    . ; Kidney function dosing adjustment
    . IF $$CREATININE(PATID)>2.0,$$RENALDOSE(MED) DO
    . . WRITE "RENAL DOSING: Adjust ",MED," for kidney function",!
    
    QUIT VALID

BILLINGAUTH(PATID,PROCCODE,DIAGCODE) ; Authorize billing for procedure
    NEW AUTH,COVERED,PRIOR,FREQ
    SET AUTH=0
    
    ; Check if procedure is covered
    SET COVERED=$$ISCOVERED($$GETINS(PATID),PROCCODE)
    IF 'COVERED QUIT 0
    
    ; Prior authorization requirements
    IF $$NEEDSAUTH(PROCCODE) DO
    . SET PRIOR=$$HASPRIORAUTH(PATID,PROCCODE)
    . IF 'PRIOR QUIT 0
    
    ; Frequency limitations
    SET FREQ=$$GETFREQLIMIT(PROCCODE)
    IF FREQ>0 DO
    . IF $$PROCCOUNT(PATID,PROCCODE,365)>=FREQ QUIT 0 ; Annual limit
    
    ; Medical necessity validation
    IF '$$MEDNECESSARY(DIAGCODE,PROCCODE) DO
    . WRITE "MEDICAL NECESSITY: Diagnosis does not support procedure",!
    . QUIT 0
    
    ; Cosmetic procedure exclusions
    IF $$ISCOSMETIC(PROCCODE),'$$RECONSTRUCTIVE(DIAGCODE) QUIT 0
    
    ; Experimental treatment exclusions
    IF $$ISEXPERIMENTAL(PROCCODE),'$$CLINICALTRIAL(PATID) QUIT 0
    
    SET AUTH=1
    QUIT AUTH