"""
Quick Test Script - Test the workflow without Databricks connection
====================================================================
Use this to test the framework structure locally.
"""

import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def load_patterns():
    """Load patterns from JSON."""
    patterns_path = Path(__file__).parent / "patterns.json"
    with open(patterns_path, 'r') as f:
        return json.load(f)


def simulate_workflow():
    """Simulate the workflow without actual Databricks connection."""
    console.print(Panel.fit(
        "[bold blue]Agentic Fraud Detection - Simulation Mode[/bold blue]\n\n"
        "This simulates the workflow without connecting to Databricks.",
        title="Quick Test",
        border_style="blue"
    ))
    
    # Load patterns
    patterns_data = load_patterns()
    pattern = patterns_data['patterns'][0]
    
    # Display pattern
    console.print("\n[bold]Pattern Information:[/bold]")
    console.print(f"  ID: {pattern['pattern_id']}")
    console.print(f"  Name: {pattern['pattern_name']}")
    console.print(f"  Severity: {pattern['severity']}")
    
    # Display detection logic
    detection_logic = pattern.get('detection_logic', {})
    console.print(f"\n[bold]Detection Steps ({len(detection_logic)}):[/bold]")
    
    for key, value in detection_logic.items():
        console.print(f"  - {key}: {value}")
    
    # Simulate step processing
    console.print("\n[bold yellow]Simulating Workflow Steps:[/bold yellow]")
    
    simulated_sql = {
        "step1": """SELECT claim_id, patient_id, provider_npi, service_date, procedure_code, global_days_value
FROM fraud_detection.test_data.claims
WHERE global_days_value IN ('010', '090')
AND procedure_code IS NOT NULL
LIMIT 50""",
        
        "step2": """SELECT 
    claim_id,
    patient_id,
    service_date AS global_period_start,
    DATE_ADD(service_date, CAST(global_days_value AS INT)) AS global_period_end,
    global_days_value
FROM fraud_detection.test_data.claims
WHERE global_days_value IN ('010', '090')
LIMIT 50""",
        
        "step3": """SELECT 
    c1.claim_id AS em_claim_id,
    c1.patient_id,
    c1.service_date AS em_date,
    c1.em_code,
    c2.claim_id AS surgical_claim_id,
    c2.service_date AS surgical_date,
    c2.global_days_value
FROM fraud_detection.test_data.claims c1
INNER JOIN fraud_detection.test_data.claims c2
    ON c1.patient_id = c2.patient_id
WHERE c1.em_code IS NOT NULL
    AND c2.global_days_value IN ('010', '090')
    AND c1.service_date > c2.service_date
    AND c1.service_date <= DATE_ADD(c2.service_date, CAST(c2.global_days_value AS INT))
LIMIT 50""",
        
        "step4": """SELECT 
    c1.claim_id AS em_claim_id,
    c1.patient_id,
    c1.provider_npi,
    c1.service_date AS em_date,
    c1.em_code,
    c2.claim_id AS surgical_claim_id,
    c2.service_date AS surgical_date,
    c2.procedure_code,
    c2.global_days_value
FROM fraud_detection.test_data.claims c1
INNER JOIN fraud_detection.test_data.claims c2
    ON c1.patient_id = c2.patient_id
WHERE c1.em_code IS NOT NULL
    AND c2.global_days_value IN ('010', '090')
    AND c1.service_date > c2.service_date
    AND c1.service_date <= DATE_ADD(c2.service_date, CAST(c2.global_days_value AS INT))
    AND (c1.provider_npi = c2.provider_npi OR c1.provider_tin = c2.provider_tin)
LIMIT 50""",
        
        "step5": """SELECT 
    c1.claim_id AS em_claim_id,
    c1.patient_id,
    c1.provider_npi,
    c1.service_date AS em_date,
    c1.em_code,
    c1.modifier_24,
    c2.claim_id AS surgical_claim_id,
    c2.service_date AS surgical_date,
    c2.procedure_code,
    c2.global_days_value,
    DATEDIFF(c1.service_date, c2.service_date) AS days_after_surgery
FROM fraud_detection.test_data.claims c1
INNER JOIN fraud_detection.test_data.claims c2
    ON c1.patient_id = c2.patient_id
WHERE c1.em_code IS NOT NULL
    AND c2.global_days_value IN ('010', '090')
    AND c1.service_date > c2.service_date
    AND c1.service_date <= DATE_ADD(c2.service_date, CAST(c2.global_days_value AS INT))
    AND (c1.provider_npi = c2.provider_npi OR c1.provider_tin = c2.provider_tin)
    AND c1.modifier_24 IS NULL
LIMIT 50""",
    }
    
    for i, (step_key, step_desc) in enumerate(detection_logic.items(), 1):
        console.print(f"\n[bold cyan]Step {i}: {step_desc[:60]}...[/bold cyan]")
        
        sql = simulated_sql.get(step_key, "SELECT * FROM claims LIMIT 10")
        console.print(f"\n[dim]Generated SQL:[/dim]")
        console.print(f"```sql\n{sql[:200]}...\n```")
        
        console.print("[green][OK] Would ask for approval (yes/no/edit)[/green]")
        console.print("[green][OK] Would execute SQL[/green]")
        console.print("[green][OK] Would ask for feedback[/green]")
        console.print("[green][OK] Would store in sqlcode.md[/green]")
    
    # Final combined SQL
    final_sql = """WITH surgical_procedures AS (
    SELECT 
        claim_id,
        patient_id,
        provider_npi,
        provider_tin,
        provider_specialty,
        service_date AS surgical_date,
        procedure_code,
        global_days_value,
        DATE_ADD(service_date, CAST(global_days_value AS INT)) AS global_period_end
    FROM fraud_detection.test_data.claims
    WHERE global_days_value IN ('010', '090')
    AND procedure_code IS NOT NULL
),
em_services AS (
    SELECT 
        claim_id,
        patient_id,
        provider_npi,
        provider_tin,
        provider_specialty,
        service_date AS em_date,
        em_code,
        modifier_24
    FROM fraud_detection.test_data.claims
    WHERE em_code IS NOT NULL
)
SELECT 
    e.claim_id AS em_claim_id,
    e.patient_id,
    e.provider_npi,
    e.em_date,
    e.em_code,
    e.modifier_24,
    s.claim_id AS surgical_claim_id,
    s.surgical_date,
    s.procedure_code,
    s.global_days_value,
    DATEDIFF(e.em_date, s.surgical_date) AS days_after_surgery
FROM em_services e
INNER JOIN surgical_procedures s
    ON e.patient_id = s.patient_id
WHERE e.em_date > s.surgical_date
    AND e.em_date <= s.global_period_end
    AND (e.provider_npi = s.provider_npi 
         OR (e.provider_tin = s.provider_tin AND e.provider_specialty = s.provider_specialty))
    AND e.modifier_24 IS NULL
LIMIT 50"""
    
    console.print("\n[bold magenta]Combined Final Function:[/bold magenta]")
    console.print(f"```sql\n{final_sql}\n```")
    
    console.print("\n[bold green]Workflow Simulation Complete![/bold green]")
    console.print("\nIn real execution:")
    console.print("  1. Each step would wait for your approval")
    console.print("  2. SQL would be executed against Databricks")
    console.print("  3. Results would be shown for validation")
    console.print("  4. Final function would be inserted into tools table")
    
    # Save simulated SQL to file
    output_path = Path(__file__).parent / "output" / "simulated_sqlcode.md"
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write("# Simulated SQL Code\n\n")
        f.write("## Step Queries\n\n")
        for step_key, sql in simulated_sql.items():
            f.write(f"### {step_key}\n\n```sql\n{sql}\n```\n\n")
        f.write("## Final Function\n\n```sql\n")
        f.write(final_sql)
        f.write("\n```\n")
    
    console.print(f"\n[dim]Simulated SQL saved to: {output_path}[/dim]")


if __name__ == "__main__":
    simulate_workflow()

