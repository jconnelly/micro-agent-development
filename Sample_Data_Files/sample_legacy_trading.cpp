/*
 * LEGACY TRADING SYSTEM - RISK MANAGEMENT MODULE
 * Financial Trading Platform - C++ Implementation
 * Contains embedded business rules for trade validation and risk assessment
 * Legacy Code Base - Circa 1995-2000
 */

#include <iostream>
#include <string>
#include <vector>
#include <map>

// Business Rule Constants
const double MAX_POSITION_SIZE = 10000000.0;     // $10M max position
const double MAX_DAILY_LOSS = 500000.0;         // $500K daily loss limit
const double MIN_ACCOUNT_BALANCE = 50000.0;     // $50K minimum balance
const double MAX_LEVERAGE_RATIO = 10.0;         // 10:1 max leverage
const double HIGH_RISK_THRESHOLD = 0.75;        // 75% risk threshold
const int MAX_TRADES_PER_DAY = 100;             // Daily trade limit
const double MARGIN_CALL_THRESHOLD = 0.25;     // 25% margin call level
const double FORCED_LIQUIDATION = 0.10;        // 10% forced liquidation
const int MIN_TRADING_EXPERIENCE = 2;          // 2 years minimum experience
const double MAX_SECTOR_CONCENTRATION = 0.30;  // 30% max sector exposure
const double VIX_HALT_THRESHOLD = 40.0;        // VIX threshold for trading halt
const double MAX_ORDER_SIZE = 1000000.0;       // $1M max single order
const int PATTERN_DAY_TRADER_LIMIT = 25000;    // PDT rule minimum

struct TraderProfile {
    int trader_id;
    std::string trader_name;
    int experience_years;
    std::string risk_level;  // LOW, MEDIUM, HIGH
    double account_balance;
    double available_margin;
    std::string trader_type; // RETAIL, INSTITUTIONAL, PROPRIETARY
    bool is_accredited;
    std::string jurisdiction;
};

struct TradeOrder {
    int order_id;
    std::string symbol;
    std::string order_type; // BUY, SELL, SHORT
    double quantity;
    double price;
    std::string time_in_force; // DAY, GTC, IOC
    bool is_margin_trade;
    std::string sector;
    double volatility_score;
};

struct PortfolioPosition {
    std::string symbol;
    double current_value;
    double unrealized_pnl;
    double sector_exposure;
    std::string risk_category;
};

class TradingRiskManager {
private:
    std::map<int, int> daily_trade_counts;
    std::map<int, double> daily_losses;
    
public:
    
    // Business Rule: Validate trader eligibility
    bool validateTraderEligibility(const TraderProfile& trader) {
        // Business Rule: Minimum experience requirement
        if (trader.experience_years < MIN_TRADING_EXPERIENCE) {
            std::cout << "REJECTED: Trader lacks minimum experience" << std::endl;
            return false;
        }
        
        // Business Rule: Account balance requirement
        if (trader.account_balance < MIN_ACCOUNT_BALANCE) {
            std::cout << "REJECTED: Insufficient account balance" << std::endl;
            return false;
        }
        
        // Business Rule: Jurisdiction restrictions
        if (trader.jurisdiction == "RESTRICTED" || trader.jurisdiction == "SANCTIONED") {
            std::cout << "REJECTED: Trader from restricted jurisdiction" << std::endl;
            return false;
        }
        
        // Business Rule: Accreditation requirement for high-risk trading
        if (trader.risk_level == "HIGH" && !trader.is_accredited) {
            std::cout << "REJECTED: High-risk trading requires accreditation" << std::endl;
            return false;
        }
        
        // Business Rule: Pattern Day Trader rule compliance
        if (trader.trader_type == "RETAIL" && trader.account_balance < PATTERN_DAY_TRADER_LIMIT) {
            std::cout << "WARNING: Pattern Day Trader restrictions apply" << std::endl;
        }
        
        return true;
    }
    
    // Business Rule: Validate individual trade order
    bool validateTradeOrder(const TradeOrder& order, const TraderProfile& trader) {
        // Business Rule: Maximum order size limit
        double order_value = order.quantity * order.price;
        if (order_value > MAX_ORDER_SIZE) {
            std::cout << "REJECTED: Order size exceeds maximum allowed" << std::endl;
            return false;
        }
        
        // Business Rule: Volatility-based restrictions
        if (order.volatility_score > 0.8 && trader.risk_level == "LOW") {
            std::cout << "REJECTED: High volatility instrument not allowed for low-risk trader" << std::endl;
            return false;
        }
        
        // Business Rule: Short selling restrictions
        if (order.order_type == "SHORT") {
            if (trader.trader_type == "RETAIL" && order_value > 100000.0) {
                std::cout << "REJECTED: Large short positions restricted for retail traders" << std::endl;
                return false;
            }
        }
        
        // Business Rule: Margin trading eligibility
        if (order.is_margin_trade) {
            if (trader.available_margin < order_value * 0.5) {
                std::cout << "REJECTED: Insufficient margin for trade" << std::endl;
                return false;
            }
        }
        
        // Business Rule: Daily trade limit
        if (daily_trade_counts[trader.trader_id] >= MAX_TRADES_PER_DAY) {
            std::cout << "REJECTED: Daily trade limit exceeded" << std::endl;
            return false;
        }
        
        // Business Rule: Sector concentration limits
        if (order.sector != "DIVERSIFIED") {
            // This would check against portfolio positions in real implementation
            std::cout << "INFO: Checking sector concentration limits" << std::endl;
        }
        
        // Business Rule: After-hours trading restrictions
        if (order.time_in_force == "EXTENDED_HOURS" && trader.experience_years < 5) {
            std::cout << "REJECTED: Insufficient experience for after-hours trading" << std::endl;
            return false;
        }
        
        return true;
    }
    
    // Business Rule: Portfolio risk assessment
    bool validatePortfolioRisk(const std::vector<PortfolioPosition>& positions, 
                              const TraderProfile& trader) {
        double total_portfolio_value = 0.0;
        double total_unrealized_loss = 0.0;
        double high_risk_exposure = 0.0;
        
        // Business Rule: Calculate portfolio metrics
        for (const auto& position : positions) {
            total_portfolio_value += position.current_value;
            
            if (position.unrealized_pnl < 0) {
                total_unrealized_loss += abs(position.unrealized_pnl);
            }
            
            if (position.risk_category == "HIGH_RISK") {
                high_risk_exposure += position.current_value;
            }
        }
        
        // Business Rule: Maximum portfolio loss limit
        if (total_unrealized_loss > trader.account_balance * 0.20) {
            std::cout << "WARNING: Portfolio losses exceed 20% of account balance" << std::endl;
        }
        
        // Business Rule: Position size limits
        for (const auto& position : positions) {
            if (position.current_value > MAX_POSITION_SIZE) {
                std::cout << "VIOLATION: Position size exceeds maximum allowed" << std::endl;
                return false;
            }
            
            // Business Rule: Single position concentration limit
            if (position.current_value > total_portfolio_value * 0.20) {
                std::cout << "WARNING: Single position exceeds 20% of portfolio" << std::endl;
            }
        }
        
        // Business Rule: High-risk exposure limits
        if (high_risk_exposure > total_portfolio_value * HIGH_RISK_THRESHOLD) {
            std::cout << "VIOLATION: High-risk exposure exceeds threshold" << std::endl;
            return false;
        }
        
        // Business Rule: Leverage ratio check
        double leverage_ratio = total_portfolio_value / trader.account_balance;
        if (leverage_ratio > MAX_LEVERAGE_RATIO) {
            std::cout << "VIOLATION: Leverage ratio exceeds maximum allowed" << std::endl;
            return false;
        }
        
        // Business Rule: Margin call assessment
        double margin_equity_ratio = trader.account_balance / total_portfolio_value;
        if (margin_equity_ratio < MARGIN_CALL_THRESHOLD) {
            std::cout << "MARGIN CALL: Account below margin maintenance requirement" << std::endl;
        }
        
        // Business Rule: Forced liquidation trigger
        if (margin_equity_ratio < FORCED_LIQUIDATION) {
            std::cout << "FORCED LIQUIDATION: Account below liquidation threshold" << std::endl;
            return false;
        }
        
        return true;
    }
    
    // Business Rule: Market condition restrictions
    bool checkMarketConditions(double current_vix, const std::string& market_status) {
        // Business Rule: VIX-based trading halts
        if (current_vix > VIX_HALT_THRESHOLD) {
            std::cout << "TRADING HALT: Market volatility too high (VIX > 40)" << std::endl;
            return false;
        }
        
        // Business Rule: Market hours validation
        if (market_status == "CLOSED") {
            std::cout << "REJECTED: Market is closed for regular trading" << std::endl;
            return false;
        }
        
        // Business Rule: Pre-market restrictions
        if (market_status == "PRE_MARKET") {
            std::cout << "RESTRICTED: Limited pre-market trading allowed" << std::endl;
        }
        
        return true;
    }
    
    // Business Rule: Daily loss monitoring
    bool checkDailyLossLimits(int trader_id, double trade_loss) {
        daily_losses[trader_id] += trade_loss;
        
        // Business Rule: Daily loss limit enforcement
        if (daily_losses[trader_id] > MAX_DAILY_LOSS) {
            std::cout << "TRADING SUSPENDED: Daily loss limit exceeded" << std::endl;
            return false;
        }
        
        // Business Rule: Warning at 75% of daily limit
        if (daily_losses[trader_id] > MAX_DAILY_LOSS * 0.75) {
            std::cout << "WARNING: Approaching daily loss limit" << std::endl;
        }
        
        return true;
    }
    
    // Business Rule: Client suitability assessment
    bool assessClientSuitability(const TraderProfile& trader, const std::string& product_type) {
        // Business Rule: Complex products require institutional status
        if (product_type == "DERIVATIVES" || product_type == "STRUCTURED_PRODUCTS") {
            if (trader.trader_type == "RETAIL" && !trader.is_accredited) {
                std::cout << "REJECTED: Complex products require accredited investor status" << std::endl;
                return false;
            }
        }
        
        // Business Rule: High-frequency trading restrictions
        if (product_type == "HFT_ALGORITHMS") {
            if (trader.trader_type != "PROPRIETARY") {
                std::cout << "REJECTED: HFT algorithms restricted to proprietary traders" << std::endl;
                return false;
            }
        }
        
        // Business Rule: International trading requirements
        if (product_type == "INTERNATIONAL_EQUITIES") {
            if (trader.experience_years < 5) {
                std::cout << "REJECTED: International trading requires 5+ years experience" << std::endl;
                return false;
            }
        }
        
        // Business Rule: Cryptocurrency trading restrictions
        if (product_type == "CRYPTOCURRENCY") {
            if (trader.jurisdiction == "NY" || trader.jurisdiction == "RESTRICTED_CRYPTO") {
                std::cout << "REJECTED: Cryptocurrency trading not allowed in jurisdiction" << std::endl;
                return false;
            }
        }
        
        return true;
    }
    
    // Business Rule: Order routing and execution rules
    bool validateOrderExecution(const TradeOrder& order, const std::string& venue) {
        // Business Rule: Large order routing requirements
        if (order.quantity * order.price > 500000.0) {
            if (venue != "DARK_POOL" && venue != "INSTITUTIONAL_NETWORK") {
                std::cout << "WARNING: Large orders should use dark pools" << std::endl;
            }
        }
        
        // Business Rule: Best execution requirements
        if (order.order_type == "MARKET" && order.quantity > 10000) {
            std::cout << "WARNING: Large market orders may have price impact" << std::endl;
        }
        
        // Business Rule: Venue-specific restrictions
        if (venue == "RETAIL_VENUE" && order.quantity > 100000) {
            std::cout << "REJECTED: Order too large for retail venue" << std::endl;
            return false;
        }
        
        return true;
    }
};

// Business Rule: Risk scoring algorithm
double calculateRiskScore(const TraderProfile& trader, const TradeOrder& order) {
    double risk_score = 0.0;
    
    // Business Rule: Experience factor
    if (trader.experience_years < 3) {
        risk_score += 0.3;
    }
    
    // Business Rule: Account size factor
    if (trader.account_balance < 100000.0) {
        risk_score += 0.2;
    }
    
    // Business Rule: Order size factor
    double order_value = order.quantity * order.price;
    if (order_value > trader.account_balance * 0.1) {
        risk_score += 0.4;
    }
    
    // Business Rule: Volatility factor
    risk_score += order.volatility_score * 0.5;
    
    // Business Rule: Sector risk factor
    if (order.sector == "BIOTECH" || order.sector == "CRYPTO") {
        risk_score += 0.3;
    }
    
    return risk_score;
}

int main() {
    TradingRiskManager risk_manager;
    
    // Sample trader profile
    TraderProfile trader = {
        123,
        "John Trader",
        5,
        "MEDIUM",
        250000.0,
        100000.0,
        "RETAIL",
        true,
        "US"
    };
    
    // Sample trade order
    TradeOrder order = {
        1001,
        "AAPL",
        "BUY",
        1000,
        150.0,
        "DAY",
        false,
        "TECHNOLOGY",
        0.3
    };
    
    // Validate trader and order
    if (risk_manager.validateTraderEligibility(trader)) {
        if (risk_manager.validateTradeOrder(order, trader)) {
            std::cout << "ORDER APPROVED" << std::endl;
        }
    }
    
    return 0;
}