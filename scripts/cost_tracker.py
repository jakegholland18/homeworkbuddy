#!/usr/bin/env python3
"""
CozmicLearning API Cost Tracker
Estimates API costs based on token usage across different features
"""

class CostTracker:
    """Track and estimate API costs for CozmicLearning features"""

    # Pricing per 1K tokens (Dec 2024)
    PRICING = {
        "gpt-4o-mini": {
            "input": 0.00015,   # $0.150 per 1M tokens
            "output": 0.0006,   # $0.600 per 1M tokens
        },
        "gpt-4.1-mini": {
            "input": 0.00015,
            "output": 0.0006,
        },
        "claude-3.5-sonnet": {
            "input": 0.003,     # $3.00 per 1M tokens
            "output": 0.015,    # $15.00 per 1M tokens
        }
    }

    # Average token usage per feature (from code analysis)
    FEATURES = {
        "ask_question": {
            "model": "gpt-4o-mini",
            "input_tokens": 500,
            "output_tokens": 300,
            "rate_limit": "30/hour"
        },
        "practice_session": {
            "model": "gpt-4.1-mini",
            "input_tokens": 700,
            "output_tokens": 1500,
            "rate_limit": "100/hour"
        },
        "powergrid": {
            "model": "claude-3.5-sonnet",
            "input_tokens": 1200,
            "output_tokens": 2000,
            "rate_limit": "20/hour"
        },
        "lesson_plan": {
            "model": "claude-3.5-sonnet",
            "input_tokens": 1000,
            "output_tokens": 3500,
            "rate_limit": "10/hour"
        },
        "teachers_pet": {
            "model": "gpt-4o-mini",
            "input_tokens": 400,
            "output_tokens": 200,
            "rate_limit": "unlimited"
        }
    }

    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for a single API call"""
        if model not in self.PRICING:
            raise ValueError(f"Unknown model: {model}")

        input_cost = (input_tokens / 1000) * self.PRICING[model]["input"]
        output_cost = (output_tokens / 1000) * self.PRICING[model]["output"]

        return input_cost + output_cost

    def feature_cost(self, feature: str, count: int = 1) -> dict:
        """Calculate cost for a specific feature"""
        if feature not in self.FEATURES:
            raise ValueError(f"Unknown feature: {feature}")

        feat = self.FEATURES[feature]
        cost_per_call = self.calculate_cost(
            feat["model"],
            feat["input_tokens"],
            feat["output_tokens"]
        )

        return {
            "feature": feature,
            "model": feat["model"],
            "calls": count,
            "cost_per_call": cost_per_call,
            "total_cost": cost_per_call * count,
            "rate_limit": feat["rate_limit"]
        }

    def user_scenario(self,
                     ask_questions: int = 0,
                     practice_sessions: int = 0,
                     powergrid_guides: int = 0,
                     lesson_plans: int = 0,
                     teachers_pet: int = 0) -> dict:
        """Calculate total cost for a user scenario"""

        costs = []
        total = 0

        if ask_questions > 0:
            result = self.feature_cost("ask_question", ask_questions)
            costs.append(result)
            total += result["total_cost"]

        if practice_sessions > 0:
            result = self.feature_cost("practice_session", practice_sessions)
            costs.append(result)
            total += result["total_cost"]

        if powergrid_guides > 0:
            result = self.feature_cost("powergrid", powergrid_guides)
            costs.append(result)
            total += result["total_cost"]

        if lesson_plans > 0:
            result = self.feature_cost("lesson_plan", lesson_plans)
            costs.append(result)
            total += result["total_cost"]

        if teachers_pet > 0:
            result = self.feature_cost("teachers_pet", teachers_pet)
            costs.append(result)
            total += result["total_cost"]

        return {
            "breakdown": costs,
            "total_cost": total
        }

    def print_scenario(self, name: str, **kwargs):
        """Print a formatted cost scenario"""
        print(f"\n{'='*60}")
        print(f"📊 {name}")
        print(f"{'='*60}")

        result = self.user_scenario(**kwargs)

        for item in result["breakdown"]:
            print(f"\n{item['feature'].replace('_', ' ').title()}:")
            print(f"  Calls: {item['calls']}")
            print(f"  Model: {item['model']}")
            print(f"  Cost per call: ${item['cost_per_call']:.5f}")
            print(f"  Total: ${item['total_cost']:.4f}")
            print(f"  Rate limit: {item['rate_limit']}")

        print(f"\n{'─'*60}")
        print(f"💰 TOTAL COST: ${result['total_cost']:.4f}")
        print(f"{'='*60}")


def main():
    """Run example cost calculations"""
    tracker = CostTracker()

    print("\n" + "="*60)
    print("🚀 CozmicLearning API Cost Calculator")
    print("="*60)

    # Scenario 1: Light Student
    tracker.print_scenario(
        "Light Student User (Monthly)",
        ask_questions=50,
        practice_sessions=20,
        powergrid_guides=5
    )

    # Scenario 2: Active Student
    tracker.print_scenario(
        "Active Student User (Monthly)",
        ask_questions=200,
        practice_sessions=50,
        powergrid_guides=15
    )

    # Scenario 3: Homeschool Parent
    tracker.print_scenario(
        "Homeschool Parent (Monthly)",
        ask_questions=100,
        practice_sessions=30,
        powergrid_guides=20,
        lesson_plans=20,
        teachers_pet=50
    )

    # Scenario 4: Teacher
    tracker.print_scenario(
        "Teacher (Monthly)",
        lesson_plans=50,
        practice_sessions=100,
        powergrid_guides=30,
        teachers_pet=100
    )

    # User base projections
    print("\n" + "="*60)
    print("📈 USER BASE PROJECTIONS")
    print("="*60)

    scenarios = {
        "10 Users (Alpha)": {
            "students": (5, 50, 20, 5, 0, 0),
            "parents": (3, 100, 30, 20, 20, 50),
            "teachers": (2, 0, 100, 30, 50, 100)
        },
        "100 Users (Beta)": {
            "students": (60, 50, 20, 5, 0, 0),
            "parents": (30, 100, 30, 20, 20, 50),
            "teachers": (10, 0, 100, 30, 50, 100)
        },
        "1,000 Users (Launch)": {
            "students": (600, 50, 20, 5, 0, 0),
            "parents": (300, 100, 30, 20, 20, 50),
            "teachers": (100, 0, 100, 30, 50, 100)
        }
    }

    for scenario_name, users in scenarios.items():
        total_cost = 0
        print(f"\n{scenario_name}:")

        for user_type, (count, *usage) in users.items():
            result = tracker.user_scenario(*usage)
            user_cost = result["total_cost"] * count
            total_cost += user_cost
            print(f"  {user_type.title()}: {count} × ${result['total_cost']:.2f} = ${user_cost:.2f}")

        print(f"  {'─'*50}")
        print(f"  💰 Monthly Total: ${total_cost:.2f}")
        print(f"  📅 Annual Total: ${total_cost * 12:.2f}")


if __name__ == "__main__":
    main()
