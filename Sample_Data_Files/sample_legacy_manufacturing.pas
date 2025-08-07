program ManufacturingQualityControl;
{ Legacy Manufacturing Quality Control System - Pascal/Delphi
  Contains complex business rules for production quality validation,
  safety compliance, and inventory management }

type
  TProductType = (Electronics, Automotive, Medical, Consumer);
  TQualityGrade = (A, B, C, Reject);
  TShiftType = (Day, Night, Weekend);

var
  CurrentShift: TShiftType;
  ProductionQuota: Integer;
  DefectRate: Real;

{ Quality inspection business rules }
function ValidateProductQuality(ProductID: String; ProductType: TProductType; 
                               TestResults: Array of Real): TQualityGrade;
var
  i: Integer;
  FailureCount: Integer;
  AverageScore: Real;
  MinScore: Real;
  Grade: TQualityGrade;
begin
  FailureCount := 0;
  AverageScore := 0;
  MinScore := 100.0;
  
  { Calculate test statistics }
  for i := 0 to High(TestResults) do
  begin
    AverageScore := AverageScore + TestResults[i];
    if TestResults[i] < MinScore then
      MinScore := TestResults[i];
    if TestResults[i] < 70.0 then
      FailureCount := FailureCount + 1;
  end;
  
  AverageScore := AverageScore / Length(TestResults);
  
  { Medical device quality standards - strictest requirements }
  if ProductType = Medical then
  begin
    if (AverageScore >= 98.0) and (MinScore >= 95.0) and (FailureCount = 0) then
      Grade := A
    else if (AverageScore >= 95.0) and (MinScore >= 90.0) and (FailureCount <= 1) then
      Grade := B
    else if (AverageScore >= 90.0) and (MinScore >= 85.0) and (FailureCount <= 2) then
      Grade := C
    else
      Grade := Reject;
  end
  
  { Automotive parts - high reliability required }
  else if ProductType = Automotive then
  begin
    if (AverageScore >= 95.0) and (MinScore >= 90.0) and (FailureCount = 0) then
      Grade := A
    else if (AverageScore >= 90.0) and (MinScore >= 85.0) and (FailureCount <= 1) then
      Grade := B
    else if (AverageScore >= 85.0) and (MinScore >= 80.0) and (FailureCount <= 2) then
      Grade := C
    else
      Grade := Reject;
  end
  
  { Electronics - moderate standards }
  else if ProductType = Electronics then
  begin
    if (AverageScore >= 90.0) and (MinScore >= 85.0) and (FailureCount <= 1) then
      Grade := A
    else if (AverageScore >= 85.0) and (MinScore >= 80.0) and (FailureCount <= 2) then
      Grade := B
    else if (AverageScore >= 80.0) and (MinScore >= 75.0) and (FailureCount <= 3) then
      Grade := C
    else
      Grade := Reject;
  end
  
  { Consumer goods - basic standards }
  else
  begin
    if (AverageScore >= 85.0) and (MinScore >= 80.0) and (FailureCount <= 2) then
      Grade := A
    else if (AverageScore >= 80.0) and (MinScore >= 75.0) and (FailureCount <= 3) then
      Grade := B
    else if (AverageScore >= 75.0) and (MinScore >= 70.0) and (FailureCount <= 4) then
      Grade := C
    else
      Grade := Reject;
  end;
  
  { Weekend production requires higher standards due to reduced oversight }
  if CurrentShift = Weekend then
  begin
    if Grade = C then
      Grade := Reject;
    if (Grade = B) and (AverageScore < 88.0) then
      Grade := Reject;
  end;
  
  ValidateProductQuality := Grade;
end;

{ Inventory and production planning rules }
function CalculateProductionSchedule(ProductType: TProductType; CurrentInventory: Integer;
                                   DemandForecast: Integer; LeadTime: Integer): Integer;
var
  SafetyStock: Integer;
  ReorderPoint: Integer;
  ProductionNeeded: Integer;
  CapacityAdjustment: Real;
begin
  { Safety stock calculation based on product criticality }
  case ProductType of
    Medical:     SafetyStock := Round(DemandForecast * 0.30); { 30% safety stock }
    Automotive:  SafetyStock := Round(DemandForecast * 0.25); { 25% safety stock }
    Electronics: SafetyStock := Round(DemandForecast * 0.20); { 20% safety stock }
    Consumer:    SafetyStock := Round(DemandForecast * 0.15); { 15% safety stock }
  end;
  
  { Calculate reorder point }
  ReorderPoint := (DemandForecast * LeadTime div 30) + SafetyStock;
  
  { Determine production needed }
  ProductionNeeded := ReorderPoint - CurrentInventory;
  if ProductionNeeded < 0 then
    ProductionNeeded := 0;
  
  { Capacity adjustments based on shift and defect rates }
  CapacityAdjustment := 1.0;
  
  { Night shift operates at 85% efficiency }
  if CurrentShift = Night then
    CapacityAdjustment := CapacityAdjustment * 1.18; { Compensate for lower efficiency }
  
  { Weekend shift operates at 75% efficiency }
  if CurrentShift = Weekend then
    CapacityAdjustment := CapacityAdjustment * 1.33; { Compensate for lower efficiency }
  
  { Adjust for current defect rate }
  if DefectRate > 0.05 then { More than 5% defect rate }
    CapacityAdjustment := CapacityAdjustment * (1.0 + DefectRate);
  
  { Rush orders for critical medical devices }
  if (ProductType = Medical) and (CurrentInventory < SafetyStock div 2) then
    CapacityAdjustment := CapacityAdjustment * 1.5; { Expedite production }
  
  ProductionNeeded := Round(ProductionNeeded * CapacityAdjustment);
  
  { Cannot exceed daily production quota }
  if ProductionNeeded > ProductionQuota then
    ProductionNeeded := ProductionQuota;
  
  CalculateProductionSchedule := ProductionNeeded;
end;

{ Supplier qualification and approval rules }
function EvaluateSupplierQuality(SupplierID: String; DeliveryScore: Real;
                                QualityScore: Real; PriceCompetitive: Boolean;
                                CertificationLevel: Integer): Boolean;
var
  Approved: Boolean;
  MinDeliveryScore: Real;
  MinQualityScore: Real;
begin
  Approved := False;
  
  { Base requirements for all suppliers }
  MinDeliveryScore := 85.0;
  MinQualityScore := 90.0;
  
  { Medical device suppliers require highest standards }
  if CertificationLevel >= 3 then { ISO 13485 or equivalent }
  begin
    MinDeliveryScore := 95.0;
    MinQualityScore := 98.0;
    
    if (DeliveryScore >= MinDeliveryScore) and 
       (QualityScore >= MinQualityScore) then
      Approved := True;
  end
  
  { Automotive suppliers need IATF certification }
  else if CertificationLevel = 2 then { IATF 16949 }
  begin
    MinDeliveryScore := 90.0;
    MinQualityScore := 95.0;
    
    if (DeliveryScore >= MinDeliveryScore) and 
       (QualityScore >= MinQualityScore) and
       PriceCompetitive then
      Approved := True;
  end
  
  { General manufacturing suppliers }
  else if CertificationLevel = 1 then { ISO 9001 }
  begin
    if (DeliveryScore >= MinDeliveryScore) and 
       (QualityScore >= MinQualityScore) and
       PriceCompetitive then
      Approved := True;
  end;
  
  { Probationary approval for new suppliers with potential }
  if not Approved and (QualityScore >= 85.0) and (DeliveryScore >= 80.0) then
  begin
    { Allow 90-day trial period for promising suppliers }
    Approved := True; { Would set probationary flag in real system }
  end;
  
  EvaluateSupplierQuality := Approved;
end;

{ Environmental and safety compliance rules }
function CheckEnvironmentalCompliance(ProductType: TProductType; 
                                    EmissionLevel: Real;
                                    WasteGenerated: Real;
                                    EnergyUsage: Real): Boolean;
var
  Compliant: Boolean;
  MaxEmissions: Real;
  MaxWaste: Real;
  MaxEnergy: Real;
begin
  Compliant := True;
  
  { Set limits based on product type and regulations }
  case ProductType of
    Medical:
    begin
      MaxEmissions := 50.0;  { Lower limits for medical devices }
      MaxWaste := 25.0;
      MaxEnergy := 150.0;
    end;
    
    Automotive:
    begin
      MaxEmissions := 100.0;
      MaxWaste := 75.0;
      MaxEnergy := 300.0;
    end;
    
    Electronics:
    begin
      MaxEmissions := 75.0;
      MaxWaste := 50.0;
      MaxEnergy := 200.0;
    end;
    
    Consumer:
    begin
      MaxEmissions := 80.0;
      MaxWaste := 60.0;
      MaxEnergy := 250.0;
    end;
  end;
  
  { Check compliance against limits }
  if (EmissionLevel > MaxEmissions) or 
     (WasteGenerated > MaxWaste) or
     (EnergyUsage > MaxEnergy) then
    Compliant := False;
  
  { Additional restrictions during high pollution days }
  if GetEnvironmentalAlertLevel > 2 then { Function assumed to exist }
  begin
    MaxEmissions := MaxEmissions * 0.8; { Reduce by 20% }
    if EmissionLevel > MaxEmissions then
      Compliant := False;
  end;
  
  CheckEnvironmentalCompliance := Compliant;
end;

begin
  { Initialize production parameters }
  CurrentShift := Day;
  ProductionQuota := 1000;
  DefectRate := 0.03;
  
  WriteLn('Manufacturing Quality Control System Initialized');
  WriteLn('Current defect rate: ', DefectRate:0:3);
  WriteLn('Production quota: ', ProductionQuota);
end.