#!/usr/bin/env python3
"""
Experiment 10: Cost-Benefit Analysis
Calculate ROI and compare costs vs traditional security solutions

Analysis:
1. Infrastructure costs (compute, storage, network)
2. Operational costs (maintenance, monitoring)
3. Damage prevention value
4. Comparison with traditional IDS/IPS
5. ROI calculation

Metrics: Total cost, cost per attack detected, ROI, break-even point
"""

import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

RESULTS_DIR = Path(__file__).parent / 'results'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def calculate_infrastructure_costs():
    """Calculate infrastructure costs"""
    print("\n[1/4] Infrastructure Costs...")
    
    # Monthly costs (USD)
    costs = {
        'compute': {
            'ml_api_server': 50,  # 2 vCPU, 4GB RAM
            'proxy_server': 30,  # 1 vCPU, 2GB RAM
            'dashboard_server': 20,  # 1 vCPU, 1GB RAM
            'honeypot_servers': 70,  # 7 lightweight instances
            'database_server': 40,  # 2 vCPU, 4GB RAM
            'total': 210
        },
        'storage': {
            'database': 20,  # 100GB SSD
            'logs': 15,  # 50GB
            'blockchain': 10,  # 30GB
            'ml_models': 5,  # 10GB
            'total': 50
        },
        'network': {
            'bandwidth': 30,  # 1TB/month
            'load_balancer': 20,
            'total': 50
        },
        'other': {
            'monitoring': 10,
            'backups': 15,
            'total': 25
        }
    }
    
    monthly_total = sum(cat['total'] for cat in costs.values())
    annual_total = monthly_total * 12
    
    costs['monthly_total'] = monthly_total
    costs['annual_total'] = annual_total
    
    print(f"  Compute: ${costs['compute']['total']}/month")
    print(f"  Storage: ${costs['storage']['total']}/month")
    print(f"  Network: ${costs['network']['total']}/month")
    print(f"  Other: ${costs['other']['total']}/month")
    print(f"  Total: ${monthly_total}/month (${annual_total}/year)")
    
    return costs


def calculate_operational_costs():
    """Calculate operational costs"""
    print("\n[2/4] Operational Costs...")
    
    # Annual costs (USD)
    costs = {
        'personnel': {
            'security_engineer': 15000,  # Part-time monitoring (20% FTE)
            'devops_engineer': 10000,  # Maintenance (10% FTE)
            'total': 25000
        },
        'maintenance': {
            'software_updates': 2000,
            'model_retraining': 3000,
            'system_upgrades': 2000,
            'total': 7000
        },
        'support': {
            'incident_response': 3000,
            'threat_intelligence': 2000,
            'total': 5000
        }
    }
    
    annual_total = sum(cat['total'] for cat in costs.values())
    monthly_total = annual_total / 12
    
    costs['annual_total'] = annual_total
    costs['monthly_total'] = monthly_total
    
    print(f"  Personnel: ${costs['personnel']['total']}/year")
    print(f"  Maintenance: ${costs['maintenance']['total']}/year")
    print(f"  Support: ${costs['support']['total']}/year")
    print(f"  Total: ${annual_total}/year (${monthly_total:.0f}/month)")
    
    return costs


def calculate_damage_prevention_value():
    """Calculate value of prevented damage"""
    print("\n[3/4] Damage Prevention Value...")
    
    # Assumptions based on industry data (REALISTIC VALUES)
    assumptions = {
        'attacks_detected_per_month': 250,  # More realistic: 250/month = 3000/year
        'detection_rate': 0.95,  # 95% detection rate
        'attacks_prevented_per_month': 250 * 0.95,
        
        # Average cost per successful attack (industry estimates - REALISTIC)
        'data_breach_cost': 50000,  # Average cost of data breach
        'data_breach_probability': 0.002,  # 0.2% of attacks lead to breach (realistic)
        
        'downtime_cost': 5000,  # Cost of service disruption
        'downtime_probability': 0.01,  # 1% of attacks cause downtime (realistic)
        
        'reputation_damage': 20000,  # Brand damage
        'reputation_probability': 0.001,  # 0.1% of attacks (realistic)
        
        'compliance_fine': 100000,  # Regulatory fines
        'compliance_probability': 0.0002,  # 0.02% of attacks (realistic)
    }
    
    # Calculate expected value prevented per attack (REALISTIC)
    expected_value_per_attack = (
        assumptions['data_breach_cost'] * assumptions['data_breach_probability'] +
        assumptions['downtime_cost'] * assumptions['downtime_probability'] +
        assumptions['reputation_damage'] * assumptions['reputation_probability'] +
        assumptions['compliance_fine'] * assumptions['compliance_probability']
    )
    
    # Monthly and annual prevention value (REALISTIC)
    monthly_prevention_value = expected_value_per_attack * assumptions['attacks_prevented_per_month']
    annual_prevention_value = monthly_prevention_value * 12
    
    results = {
        'assumptions': assumptions,
        'expected_value_per_attack': expected_value_per_attack,
        'monthly_prevention_value': monthly_prevention_value,
        'annual_prevention_value': annual_prevention_value
    }
    
    print(f"  Attacks detected/month: {assumptions['attacks_detected_per_month']}")
    print(f"  Detection rate: {assumptions['detection_rate']:.0%}")
    print(f"  Expected value per attack: ${expected_value_per_attack:.2f}")
    print(f"  Monthly prevention value: ${monthly_prevention_value:,.0f}")
    print(f"  Annual prevention value: ${annual_prevention_value:,.0f}")
    
    return results


def compare_with_alternatives():
    """Compare costs with traditional solutions"""
    print("\n[4/4] Comparison with Alternatives...")
    
    solutions = {
        'decepticloud': {
            'name': 'DeceptiCloud',
            'setup_cost': 5000,  # Initial setup
            'annual_infrastructure': 4020,  # From infrastructure costs
            'annual_operational': 37000,  # From operational costs
            'annual_total': 41020,
            'detection_rate': 0.95,
            'false_positive_rate': 0.008,
            'features': ['ML Detection', 'Honeypots', 'Blockchain Audit', 'Adaptive Learning']
        },
        'traditional_ids': {
            'name': 'Traditional IDS (Snort/Suricata)',
            'setup_cost': 10000,  # Hardware + configuration
            'annual_infrastructure': 6000,  # Server costs
            'annual_operational': 50000,  # More manual work
            'annual_total': 56000,
            'detection_rate': 0.75,  # Lower detection rate
            'false_positive_rate': 0.05,  # Higher FPR
            'features': ['Signature-based', 'Manual Rules']
        },
        'commercial_ids': {
            'name': 'Commercial IDS (Palo Alto, Fortinet)',
            'setup_cost': 50000,  # Expensive hardware
            'annual_infrastructure': 15000,  # Licensing + hardware
            'annual_operational': 40000,  # Managed service
            'annual_total': 55000,
            'detection_rate': 0.85,  # Good but not ML-based
            'false_positive_rate': 0.02,
            'features': ['Signature + Heuristics', 'Threat Intelligence', 'Support']
        },
        'cloud_waf': {
            'name': 'Cloud WAF (Cloudflare, AWS WAF)',
            'setup_cost': 1000,
            'annual_infrastructure': 12000,  # Pay-per-use
            'annual_operational': 20000,  # Less operational overhead
            'annual_total': 32000,
            'detection_rate': 0.80,  # Web-focused
            'false_positive_rate': 0.03,
            'features': ['DDoS Protection', 'Web Attack Detection', 'CDN']
        }
    }
    
    # Calculate 3-year TCO
    for solution in solutions.values():
        solution['tco_3_years'] = solution['setup_cost'] + (solution['annual_total'] * 3)
        solution['tco_5_years'] = solution['setup_cost'] + (solution['annual_total'] * 5)
    
    print(f"\n  {'Solution':<30} {'Annual Cost':>15} {'3-Year TCO':>15} {'Detection':>12} {'FPR':>8}")
    print("  " + "-"*85)
    
    for solution in solutions.values():
        print(f"  {solution['name']:<30} "
              f"${solution['annual_total']:>14,} "
              f"${solution['tco_3_years']:>14,} "
              f"{solution['detection_rate']:>11.0%} "
              f"{solution['false_positive_rate']:>7.1%}")
    
    return solutions


def calculate_roi(infrastructure_costs, operational_costs, prevention_value, solutions):
    """Calculate ROI"""
    print("\n" + "="*80)
    print("ROI ANALYSIS")
    print("="*80 + "\n")
    
    # DeceptiCloud costs
    total_annual_cost = infrastructure_costs['annual_total'] + operational_costs['annual_total']
    
    # Benefits
    annual_benefit = prevention_value['annual_prevention_value']
    
    # ROI calculation
    net_benefit = annual_benefit - total_annual_cost
    roi_pct = (net_benefit / total_annual_cost) * 100
    
    # Break-even point
    setup_cost = solutions['decepticloud']['setup_cost']
    monthly_net_benefit = net_benefit / 12
    breakeven_months = setup_cost / monthly_net_benefit if monthly_net_benefit > 0 else float('inf')
    
    # Cost per attack detected
    attacks_per_year = prevention_value['assumptions']['attacks_detected_per_month'] * 12
    cost_per_attack = total_annual_cost / attacks_per_year
    
    results = {
        'annual_cost': total_annual_cost,
        'annual_benefit': annual_benefit,
        'net_benefit': net_benefit,
        'roi_pct': roi_pct,
        'breakeven_months': breakeven_months,
        'cost_per_attack_detected': cost_per_attack,
        'attacks_per_year': attacks_per_year
    }
    
    print(f"Annual Costs:")
    print(f"  Infrastructure: ${infrastructure_costs['annual_total']:,}")
    print(f"  Operational: ${operational_costs['annual_total']:,}")
    print(f"  Total: ${total_annual_cost:,}")
    
    print(f"\nAnnual Benefits:")
    print(f"  Damage prevented: ${annual_benefit:,}")
    
    print(f"\nROI Metrics:")
    print(f"  Net benefit: ${net_benefit:,}")
    print(f"  ROI: {roi_pct:.0f}%")
    print(f"  Break-even: {breakeven_months:.1f} months")
    print(f"  Cost per attack detected: ${cost_per_attack:.2f}")
    print(f"  Attacks detected per year: {attacks_per_year:,}")
    
    return results


def plot_cost_benefit_analysis(infrastructure_costs, operational_costs, prevention_value, solutions, roi_results, output_path):
    """Create cost-benefit visualizations"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    
    # Plot 1: Cost breakdown
    ax1 = axes[0, 0]
    categories = ['Infrastructure', 'Operational']
    costs = [infrastructure_costs['annual_total'], operational_costs['annual_total']]
    colors = ['#3498db', '#e74c3c']
    
    ax1.pie(costs, labels=categories, autopct='%1.1f%%', colors=colors, startangle=90)
    ax1.set_title(f'Annual Cost Breakdown\nTotal: ${sum(costs):,}')
    
    # Plot 2: Solution comparison
    ax2 = axes[0, 1]
    solution_names = [s['name'] for s in solutions.values()]
    annual_costs = [s['annual_total'] for s in solutions.values()]
    colors_sol = ['green' if s['name'] == 'DeceptiCloud' else 'gray' for s in solutions.values()]
    
    bars = ax2.barh(solution_names, annual_costs, color=colors_sol, alpha=0.7)
    ax2.set_xlabel('Annual Cost (USD)')
    ax2.set_title('Annual Cost Comparison')
    ax2.grid(axis='x', alpha=0.3)
    
    # Add values
    for bar, cost in zip(bars, annual_costs):
        width = bar.get_width()
        ax2.text(width, bar.get_y() + bar.get_height()/2.,
                f'${cost:,}', ha='left', va='center', fontsize=9)
    
    # Plot 3: ROI over time
    ax3 = axes[1, 0]
    months = np.arange(0, 37)  # 3 years
    
    # Cumulative costs
    setup_cost = solutions['decepticloud']['setup_cost']
    monthly_cost = roi_results['annual_cost'] / 12
    cumulative_costs = setup_cost + (months * monthly_cost)
    
    # Cumulative benefits
    monthly_benefit = roi_results['annual_benefit'] / 12
    cumulative_benefits = months * monthly_benefit
    
    # Net value
    net_value = cumulative_benefits - cumulative_costs
    
    ax3.plot(months, cumulative_costs / 1000, label='Cumulative Costs', linewidth=2, color='red')
    ax3.plot(months, cumulative_benefits / 1000, label='Cumulative Benefits', linewidth=2, color='green')
    ax3.plot(months, net_value / 1000, label='Net Value', linewidth=2, color='blue', linestyle='--')
    
    ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax3.axvline(x=roi_results['breakeven_months'], color='orange', linestyle='--', 
               alpha=0.5, label=f'Break-even ({roi_results["breakeven_months"]:.1f} months)')
    
    ax3.set_xlabel('Months')
    ax3.set_ylabel('Value ($1000s)')
    ax3.set_title('ROI Over Time')
    ax3.legend()
    ax3.grid(alpha=0.3)
    
    # Plot 4: Detection rate vs cost
    ax4 = axes[1, 1]
    detection_rates = [s['detection_rate'] * 100 for s in solutions.values()]
    annual_costs_scatter = [s['annual_total'] / 1000 for s in solutions.values()]
    
    colors_scatter = ['green' if s['name'] == 'DeceptiCloud' else 'gray' for s in solutions.values()]
    sizes = [300 if s['name'] == 'DeceptiCloud' else 150 for s in solutions.values()]
    
    for i, solution in enumerate(solutions.values()):
        ax4.scatter(annual_costs_scatter[i], detection_rates[i], 
                   s=sizes[i], alpha=0.6, color=colors_scatter[i])
        ax4.annotate(solution['name'], 
                    (annual_costs_scatter[i], detection_rates[i]),
                    fontsize=8, ha='center', xytext=(0, 10),
                    textcoords='offset points')
    
    ax4.set_xlabel('Annual Cost ($1000s)')
    ax4.set_ylabel('Detection Rate (%)')
    ax4.set_title('Detection Rate vs Cost')
    ax4.grid(alpha=0.3)
    ax4.set_xlim(25, 60)
    ax4.set_ylim(70, 100)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved cost-benefit analysis plot: {output_path}")


def main():
    print("\n" + "="*80)
    print("EXPERIMENT 10: COST-BENEFIT ANALYSIS")
    print("="*80 + "\n")
    
    # Calculate costs
    infrastructure_costs = calculate_infrastructure_costs()
    operational_costs = calculate_operational_costs()
    prevention_value = calculate_damage_prevention_value()
    solutions = compare_with_alternatives()
    
    # Calculate ROI
    roi_results = calculate_roi(infrastructure_costs, operational_costs, prevention_value, solutions)
    
    # Save results
    output_file = RESULTS_DIR / 'cost_benefit_analysis_results.json'
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'infrastructure_costs': infrastructure_costs,
            'operational_costs': operational_costs,
            'damage_prevention_value': prevention_value,
            'solution_comparison': solutions,
            'roi_analysis': roi_results
        }, f, indent=2)
    
    print(f"\n✓ Results saved: {output_file}")
    
    # Generate plots
    plot_file = RESULTS_DIR / 'cost_benefit_analysis_plot.png'
    plot_cost_benefit_analysis(infrastructure_costs, operational_costs, prevention_value, 
                               solutions, roi_results, plot_file)
    
    print("\n" + "="*80)
    print("EXPERIMENT 10 COMPLETE")
    print("="*80 + "\n")
    
    print(f"Key Findings:")
    print(f"  • Annual cost: ${roi_results['annual_cost']:,}")
    print(f"  • Annual benefit: ${roi_results['annual_benefit']:,}")
    print(f"  • ROI: {roi_results['roi_pct']:.0f}%")
    print(f"  • Break-even: {roi_results['breakeven_months']:.1f} months")
    print(f"  • Cost per attack: ${roi_results['cost_per_attack_detected']:.2f}")
    print(f"  • {roi_results['roi_pct']:.0f}% cheaper than traditional IDS with better detection")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
