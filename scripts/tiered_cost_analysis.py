#!/usr/bin/env python3
"""
Analyze profitability of tiered rate limiting strategy
"""

class TieredCostAnalysis:
    """Calculate costs and profitability for tiered subscription plans"""

    # API Costs (per 1K tokens)
    PRICING = {
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-4.1-mini": {"input": 0.00015, "output": 0.0006},
        "claude-3.5-sonnet": {"input": 0.003, "output": 0.015}
    }

    # Base feature costs (from previous analysis)
    FEATURE_COSTS = {
        "ask_question": 0.00025,
        "practice_session": 0.00101,
        "powergrid": 0.03360,
        "lesson_plan": 0.05550
    }

    # Subscription pricing
    SUBSCRIPTION_PRICES = {
        "free": 0,
        "basic": 7.99,
        "premium": 12.99,
        "complete": 29.99,
        "enterprise": 99.99
    }

    # Rate limits per tier (calls per month at max hourly usage)
    TIER_LIMITS = {
        "free": {
            "ask_question": 10 * 30,  # 10/hour × 30 days = 300/month max
            "practice_session": 30 * 30,
            "powergrid": 5 * 30,
            "lesson_plan": 3 * 30
        },
        "basic": {
            "ask_question": 30 * 30,
            "practice_session": 100 * 30,
            "powergrid": 20 * 30,
            "lesson_plan": 10 * 30
        },
        "premium": {
            "ask_question": 100 * 30,
            "practice_session": 300 * 30,
            "powergrid": 50 * 30,
            "lesson_plan": 30 * 30
        },
        "complete": {
            "ask_question": 300 * 30,
            "practice_session": 1000 * 30,
            "powergrid": 200 * 30,
            "lesson_plan": 100 * 30
        },
        "enterprise": {
            "ask_question": 1000 * 30,  # Effectively unlimited
            "practice_session": 3000 * 30,
            "powergrid": 500 * 30,
            "lesson_plan": 300 * 30
        }
    }

    def calculate_max_cost(self, tier: str) -> dict:
        """Calculate maximum possible API cost if user hits all limits"""
        limits = self.TIER_LIMITS[tier]

        costs = {}
        total = 0

        for feature, max_calls in limits.items():
            cost = self.FEATURE_COSTS[feature] * max_calls
            costs[feature] = cost
            total += cost

        return {
            "tier": tier,
            "breakdown": costs,
            "total_max_cost": total,
            "price": self.SUBSCRIPTION_PRICES[tier],
            "max_profit": self.SUBSCRIPTION_PRICES[tier] - total,
            "profit_margin": ((self.SUBSCRIPTION_PRICES[tier] - total) / self.SUBSCRIPTION_PRICES[tier] * 100) if self.SUBSCRIPTION_PRICES[tier] > 0 else 0
        }

    def realistic_usage(self, tier: str) -> dict:
        """Calculate realistic usage (users typically use 20-30% of limits)"""
        max_analysis = self.calculate_max_cost(tier)

        # Realistic usage: 25% of max limits
        realistic_cost = max_analysis["total_max_cost"] * 0.25

        return {
            "tier": tier,
            "max_cost": max_analysis["total_max_cost"],
            "realistic_cost": realistic_cost,
            "price": self.SUBSCRIPTION_PRICES[tier],
            "realistic_profit": self.SUBSCRIPTION_PRICES[tier] - realistic_cost,
            "realistic_margin": ((self.SUBSCRIPTION_PRICES[tier] - realistic_cost) / self.SUBSCRIPTION_PRICES[tier] * 100) if self.SUBSCRIPTION_PRICES[tier] > 0 else 0
        }

    def print_analysis(self):
        """Print comprehensive profitability analysis"""
        print("="*80)
        print("💰 TIERED RATE LIMITING PROFITABILITY ANALYSIS")
        print("="*80)

        print("\n📊 WORST CASE SCENARIO (User Maxes Out ALL Limits)")
        print("-"*80)
        print(f"{'Tier':<12} {'Price':<10} {'Max Cost':<12} {'Profit':<12} {'Margin':<10}")
        print("-"*80)

        for tier in ["free", "basic", "premium", "complete", "enterprise"]:
            analysis = self.calculate_max_cost(tier)
            print(f"{tier.upper():<12} ${analysis['price']:<9.2f} ${analysis['total_max_cost']:<11.2f} "
                  f"${analysis['max_profit']:<11.2f} {analysis['profit_margin']:<9.1f}%")

        print("\n\n✅ REALISTIC SCENARIO (Users Use ~25% of Limits)")
        print("-"*80)
        print(f"{'Tier':<12} {'Price':<10} {'Real Cost':<12} {'Profit':<12} {'Margin':<10}")
        print("-"*80)

        for tier in ["free", "basic", "premium", "complete", "enterprise"]:
            analysis = self.realistic_usage(tier)
            if tier != "free":
                print(f"{tier.upper():<12} ${analysis['price']:<9.2f} ${analysis['realistic_cost']:<11.2f} "
                      f"${analysis['realistic_profit']:<11.2f} {analysis['realistic_margin']:<9.1f}%")

        print("\n\n🎯 DETAILED BREAKDOWN BY FEATURE (Max Usage)")
        print("="*80)

        for tier in ["basic", "premium", "complete", "enterprise"]:
            analysis = self.calculate_max_cost(tier)
            print(f"\n{tier.upper()} - ${analysis['price']}/month")
            print("-"*80)

            for feature, cost in analysis['breakdown'].items():
                calls = self.TIER_LIMITS[tier][feature]
                print(f"  {feature.replace('_', ' ').title():<20} {calls:>6} calls × "
                      f"${self.FEATURE_COSTS[feature]:.5f} = ${cost:>8.2f}")

            print(f"\n  {'TOTAL MAX COST':<20} ${analysis['total_max_cost']:>8.2f}")
            print(f"  {'SUBSCRIPTION PRICE':<20} ${analysis['price']:>8.2f}")
            print(f"  {'MAX PROFIT':<20} ${analysis['max_profit']:>8.2f} ({analysis['profit_margin']:.1f}%)")

        print("\n\n💡 RECOMMENDATIONS")
        print("="*80)

        # Analyze profitability thresholds
        for tier in ["basic", "premium", "complete", "enterprise"]:
            max_analysis = self.calculate_max_cost(tier)
            real_analysis = self.realistic_usage(tier)

            if max_analysis['profit_margin'] < 50:
                print(f"\n⚠️  {tier.upper()}: Risk of unprofitability if users max out limits")
                print(f"   Recommendation: Consider reducing limits or increasing price")
            elif max_analysis['profit_margin'] >= 70:
                print(f"\n✅ {tier.upper()}: Highly profitable even at max usage ({max_analysis['profit_margin']:.1f}% margin)")
                print(f"   Realistic margin: {real_analysis['realistic_margin']:.1f}%")
            else:
                print(f"\n✔️  {tier.upper()}: Acceptable margins ({max_analysis['profit_margin']:.1f}% worst case)")
                print(f"   Realistic margin: {real_analysis['realistic_margin']:.1f}%")


def main():
    analyzer = TieredCostAnalysis()
    analyzer.print_analysis()

    print("\n\n📈 REVENUE PROJECTIONS (100 Users)")
    print("="*80)

    # Scenario: 100 users across tiers
    user_distribution = {
        "basic": 50,
        "premium": 30,
        "complete": 15,
        "enterprise": 5
    }

    total_revenue = 0
    total_cost = 0

    print(f"\n{'Tier':<12} {'Users':<8} {'Revenue':<12} {'API Cost':<12} {'Profit':<12}")
    print("-"*80)

    for tier, user_count in user_distribution.items():
        analysis = analyzer.realistic_usage(tier)
        tier_revenue = analysis['price'] * user_count
        tier_cost = analysis['realistic_cost'] * user_count
        tier_profit = tier_revenue - tier_cost

        total_revenue += tier_revenue
        total_cost += tier_cost

        print(f"{tier.upper():<12} {user_count:<8} ${tier_revenue:<11.2f} ${tier_cost:<11.2f} ${tier_profit:<11.2f}")

    print("-"*80)
    print(f"{'TOTAL':<12} {sum(user_distribution.values()):<8} ${total_revenue:<11.2f} "
          f"${total_cost:<11.2f} ${total_revenue - total_cost:<11.2f}")
    print(f"\nOverall Profit Margin: {((total_revenue - total_cost) / total_revenue * 100):.1f}%")


if __name__ == "__main__":
    main()
