#!/usr/bin/perl
# Legacy Retail Management System - Perl
# Contains business rules for pricing, inventory, customer management,
# and promotional campaigns in a retail environment

use strict;
use warnings;

# Customer loyalty and pricing rules
sub calculate_customer_discount {
    my ($customer_id, $purchase_amount, $loyalty_tier, $purchase_history) = @_;
    my $discount_rate = 0;
    my $base_discount = 0;
    
    # Loyalty tier discounts
    if ($loyalty_tier eq 'PLATINUM') {
        $base_discount = 0.15;  # 15% for platinum members
    } elsif ($loyalty_tier eq 'GOLD') {
        $base_discount = 0.10;  # 10% for gold members
    } elsif ($loyalty_tier eq 'SILVER') {
        $base_discount = 0.05;  # 5% for silver members
    } else {
        $base_discount = 0.02;  # 2% for regular customers
    }
    
    # Purchase volume bonuses
    if ($purchase_amount > 1000) {
        $discount_rate = $base_discount + 0.05;  # Additional 5% for large purchases
    } elsif ($purchase_amount > 500) {
        $discount_rate = $base_discount + 0.03;  # Additional 3% for medium purchases
    } elsif ($purchase_amount > 200) {
        $discount_rate = $base_discount + 0.01;  # Additional 1% for small purchases
    } else {
        $discount_rate = $base_discount;
    }
    
    # Frequent shopper bonus (more than 10 purchases in 90 days)
    if ($purchase_history->{purchases_90_days} > 10) {
        $discount_rate += 0.03;  # Additional 3% for frequent shoppers
    }
    
    # New customer incentive (first purchase)
    if ($purchase_history->{total_purchases} == 1) {
        $discount_rate += 0.10;  # 10% first-time buyer discount
    }
    
    # Senior citizen discount (age 65+)
    if (defined $purchase_history->{age} && $purchase_history->{age} >= 65) {
        $discount_rate += 0.05;  # Additional 5% senior discount
    }
    
    # Student discount with valid ID
    if (defined $purchase_history->{student_status} && $purchase_history->{student_status} eq 'VERIFIED') {
        $discount_rate += 0.08;  # 8% student discount
    }
    
    # Employee discount
    if (defined $purchase_history->{employee} && $purchase_history->{employee} eq 'TRUE') {
        $discount_rate = 0.25;  # 25% employee discount (overrides other discounts)
    }
    
    # Cap maximum discount at 30%
    $discount_rate = 0.30 if $discount_rate > 0.30;
    
    return $discount_rate;
}

# Inventory management and reorder rules
sub check_reorder_requirements {
    my ($product_id, $current_stock, $sales_velocity, $lead_time, $category) = @_;
    my %reorder_info = (
        'reorder_needed' => 0,
        'reorder_quantity' => 0,
        'priority' => 'NORMAL'
    );
    
    # Calculate safety stock based on product category
    my $safety_stock_days = 7;  # Default 7 days
    if ($category eq 'PERISHABLE') {
        $safety_stock_days = 3;   # Only 3 days for perishables
    } elsif ($category eq 'SEASONAL') {
        $safety_stock_days = 14;  # 14 days for seasonal items
    } elsif ($category eq 'ELECTRONICS') {
        $safety_stock_days = 10;  # 10 days for electronics
    } elsif ($category eq 'LUXURY') {
        $safety_stock_days = 21;  # 21 days for luxury items (slower turnover)
    }
    
    my $safety_stock = $sales_velocity * $safety_stock_days;
    my $reorder_point = ($sales_velocity * $lead_time) + $safety_stock;
    
    # Check if reorder is needed
    if ($current_stock <= $reorder_point) {
        $reorder_info{'reorder_needed'} = 1;
        
        # Calculate Economic Order Quantity (EOQ) - simplified
        my $carrying_cost_rate = 0.15;  # 15% annual carrying cost
        my $order_cost = 50;            # $50 per order
        my $annual_demand = $sales_velocity * 365;
        
        # EOQ formula: sqrt(2 * annual_demand * order_cost / carrying_cost_rate)
        my $eoq = sqrt(2 * $annual_demand * $order_cost / $carrying_cost_rate);
        
        # Adjust EOQ based on category constraints
        if ($category eq 'PERISHABLE') {
            # Limit perishable orders to 30 days supply maximum
            my $max_perishable = $sales_velocity * 30;
            $eoq = $max_perishable if $eoq > $max_perishable;
        }
        
        # Calculate order quantity (EOQ - current_stock + buffer)
        $reorder_info{'reorder_quantity'} = int($eoq - $current_stock + ($safety_stock * 0.5));
        $reorder_info{'reorder_quantity'} = 1 if $reorder_info{'reorder_quantity'} < 1;
        
        # Set priority based on stock level urgency
        if ($current_stock <= ($safety_stock * 0.5)) {
            $reorder_info{'priority'} = 'URGENT';
        } elsif ($current_stock <= $safety_stock) {
            $reorder_info{'priority'} = 'HIGH';
        }
        
        # Holiday season adjustments (November-December)
        my ($month) = (localtime)[4];  # 0-based month
        if ($month >= 10 && $month <= 11) {  # Nov-Dec
            $reorder_info{'reorder_quantity'} = int($reorder_info{'reorder_quantity'} * 1.5);
        }
    }
    
    return %reorder_info;
}

# Dynamic pricing rules based on market conditions
sub calculate_dynamic_pricing {
    my ($product_id, $base_price, $competitor_prices, $inventory_level, $sales_velocity) = @_;
    my $adjusted_price = $base_price;
    my $price_change_reason = "";
    
    # Competitor price matching rules
    if (@$competitor_prices > 0) {
        my $avg_competitor_price = 0;
        my $min_competitor_price = $competitor_prices->[0];
        
        foreach my $price (@$competitor_prices) {
            $avg_competitor_price += $price;
            $min_competitor_price = $price if $price < $min_competitor_price;
        }
        $avg_competitor_price /= scalar(@$competitor_prices);
        
        # Match lowest competitor if we're more than 5% higher
        if ($base_price > ($min_competitor_price * 1.05)) {
            $adjusted_price = $min_competitor_price * 0.99;  # Price slightly below competitor
            $price_change_reason = "Competitive pricing adjustment";
        }
    }
    
    # Inventory-based pricing adjustments
    my $inventory_days_supply = $inventory_level / $sales_velocity;
    
    if ($inventory_days_supply > 60) {
        # Excess inventory - reduce price to move stock
        $adjusted_price = $adjusted_price * 0.85;  # 15% discount
        $price_change_reason = "Excess inventory clearance";
    } elsif ($inventory_days_supply < 7) {
        # Low inventory - increase price to slow demand
        $adjusted_price = $adjusted_price * 1.15;  # 15% premium
        $price_change_reason = "Low inventory premium";
    }
    
    # Demand-based adjustments
    my $demand_trend = calculate_demand_trend($product_id);  # Assume this function exists
    if ($demand_trend > 1.2) {
        # High demand - can increase price
        $adjusted_price = $adjusted_price * 1.08;  # 8% increase
        $price_change_reason = "High demand pricing";
    } elsif ($demand_trend < 0.8) {
        # Low demand - decrease price to stimulate sales
        $adjusted_price = $adjusted_price * 0.92;  # 8% decrease
        $price_change_reason = "Demand stimulation pricing";
    }
    
    # Seasonal adjustments
    my ($month, $day) = (localtime)[4,3];
    if ($month == 11 && $day > 20) {  # Black Friday period
        $adjusted_price = $adjusted_price * 0.75;  # 25% off
        $price_change_reason = "Black Friday promotion";
    } elsif ($month == 0 && $day < 15) {  # Post-holiday clearance
        $adjusted_price = $adjusted_price * 0.60;  # 40% off
        $price_change_reason = "Post-holiday clearance";
    }
    
    # Minimum margin protection (never go below 20% gross margin)
    my $cost = get_product_cost($product_id);  # Assume this function exists
    my $min_price = $cost * 1.25;  # 25% markup minimum
    if ($adjusted_price < $min_price) {
        $adjusted_price = $min_price;
        $price_change_reason = "Minimum margin protection";
    }
    
    # Maximum price increase limit (never more than 50% above base price)
    my $max_price = $base_price * 1.50;
    if ($adjusted_price > $max_price) {
        $adjusted_price = $max_price;
        $price_change_reason = "Maximum price limit applied";
    }
    
    return ($adjusted_price, $price_change_reason);
}

# Customer segmentation and targeted marketing rules
sub determine_marketing_segment {
    my ($customer_data) = @_;
    my @segments = ();
    
    my $age = $customer_data->{age} || 0;
    my $income = $customer_data->{annual_income} || 0;
    my $purchase_frequency = $customer_data->{purchases_per_year} || 0;
    my $avg_order_value = $customer_data->{avg_order_value} || 0;
    my $categories = $customer_data->{preferred_categories} || [];
    
    # Age-based segments
    if ($age >= 18 && $age <= 25) {
        push @segments, "GEN_Z";
    } elsif ($age >= 26 && $age <= 41) {
        push @segments, "MILLENNIAL";
    } elsif ($age >= 42 && $age <= 57) {
        push @segments, "GEN_X";
    } elsif ($age >= 58) {
        push @segments, "BOOMER";
    }
    
    # Income-based segments
    if ($income >= 100000) {
        push @segments, "HIGH_INCOME";
    } elsif ($income >= 50000) {
        push @segments, "MIDDLE_INCOME";
    } else {
        push @segments, "BUDGET_CONSCIOUS";
    }
    
    # Shopping behavior segments
    if ($purchase_frequency >= 24) {  # More than twice per month
        push @segments, "FREQUENT_SHOPPER";
    } elsif ($purchase_frequency >= 12) {  # Monthly shopper
        push @segments, "REGULAR_SHOPPER";
    } else {
        push @segments, "OCCASIONAL_SHOPPER";
    }
    
    # Value-based segments
    if ($avg_order_value >= 200) {
        push @segments, "HIGH_VALUE";
    } elsif ($avg_order_value >= 75) {
        push @segments, "MEDIUM_VALUE";
    } else {
        push @segments, "LOW_VALUE";
    }
    
    # Category preference segments
    foreach my $category (@$categories) {
        if ($category eq 'ELECTRONICS') {
            push @segments, "TECH_ENTHUSIAST";
        } elsif ($category eq 'FASHION') {
            push @segments, "FASHION_FORWARD";
        } elsif ($category eq 'HOME_GARDEN') {
            push @segments, "HOME_IMPROVER";
        } elsif ($category eq 'SPORTS') {
            push @segments, "FITNESS_FOCUSED";
        }
    }
    
    # Lifestyle segments based on purchase patterns
    if (grep(/ORGANIC/, @$categories) || grep(/HEALTH/, @$categories)) {
        push @segments, "HEALTH_CONSCIOUS";
    }
    
    if (grep(/LUXURY/, @$categories) && $avg_order_value >= 300) {
        push @segments, "LUXURY_BUYER";
    }
    
    # Remove duplicates and return
    my %seen = ();
    @segments = grep { !$seen{$_}++ } @segments;
    
    return @segments;
}

# Return and refund policy rules
sub validate_return_request {
    my ($order_id, $product_id, $purchase_date, $reason, $condition) = @_;
    my %return_response = (
        'approved' => 0,
        'refund_amount' => 0,
        'restocking_fee' => 0,
        'reason' => ''
    );
    
    my $days_since_purchase = calculate_days_since($purchase_date);  # Assume function exists
    my $category = get_product_category($product_id);  # Assume function exists
    my $original_price = get_order_item_price($order_id, $product_id);  # Assume function exists
    
    # Standard return window - 30 days for most items
    my $return_window = 30;
    
    # Category-specific return windows
    if ($category eq 'ELECTRONICS') {
        $return_window = 15;  # Electronics have shorter return window
    } elsif ($category eq 'CLOTHING') {
        $return_window = 60;  # Clothing has longer return window
    } elsif ($category eq 'PERISHABLE') {
        $return_window = 3;   # Perishables have very short window
    } elsif ($category eq 'CUSTOM') {
        $return_window = 0;   # Custom items non-returnable
    }
    
    # Check if within return window
    if ($days_since_purchase > $return_window) {
        $return_response{'reason'} = "Return request exceeds $return_window day limit";
        return %return_response;
    }
    
    # Evaluate return reason and condition
    my $refund_percentage = 1.0;  # Full refund by default
    my $restocking_fee_rate = 0;
    
    if ($reason eq 'DEFECTIVE') {
        # Full refund for defective items, no restocking fee
        $refund_percentage = 1.0;
        $restocking_fee_rate = 0;
    } elsif ($reason eq 'NOT_AS_DESCRIBED') {
        # Full refund if item not as described
        $refund_percentage = 1.0;
        $restocking_fee_rate = 0;
    } elsif ($reason eq 'CHANGED_MIND') {
        # Restocking fee for change of mind returns
        if ($condition eq 'UNOPENED') {
            $refund_percentage = 1.0;
            $restocking_fee_rate = 0.10;  # 10% restocking fee
        } elsif ($condition eq 'OPENED_UNUSED') {
            $refund_percentage = 0.85;    # 15% reduction for opened items
            $restocking_fee_rate = 0.10;
        } else {
            $return_response{'reason'} = "Used items not eligible for return due to change of mind";
            return %return_response;
        }
    } elsif ($reason eq 'SIZE_ISSUE') {
        # Size exchanges typically allowed for clothing
        if ($category eq 'CLOTHING') {
            $refund_percentage = 1.0;
            $restocking_fee_rate = 0;
        } else {
            $refund_percentage = 0.90;  # 10% reduction for non-clothing size issues
            $restocking_fee_rate = 0.05;
        }
    }
    
    # Calculate final amounts
    $return_response{'approved'} = 1;
    $return_response{'refund_amount'} = $original_price * $refund_percentage;
    $return_response{'restocking_fee'} = $original_price * $restocking_fee_rate;
    $return_response{'refund_amount'} -= $return_response{'restocking_fee'};
    $return_response{'reason'} = "Return approved";
    
    return %return_response;
}

# Placeholder functions (would be implemented in full system)
sub calculate_demand_trend { return 1.0; }
sub get_product_cost { return 50.0; }
sub calculate_days_since { return 15; }
sub get_product_category { return 'GENERAL'; }
sub get_order_item_price { return 100.0; }

print "Retail Management System - Business Rules Engine Initialized\n";
print "System ready for customer discount calculations, inventory management,\n";
print "dynamic pricing, customer segmentation, and return processing.\n";