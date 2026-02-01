# Neo4j Cypher Query Reference

A comprehensive collection of Cypher queries for exploring and analyzing the Healthcare Policy Knowledge Graph.

## Table of Contents
1. [Basic Exploration](#basic-exploration)
2. [Policy Queries](#policy-queries)
3. [Denial Rules](#denial-rules)
4. [Fraud Tactics](#fraud-tactics)
5. [Code Analysis](#code-analysis)
6. [Relationship Queries](#relationship-queries)
7. [Analytics & Reporting](#analytics--reporting)
8. [Advanced Queries](#advanced-queries)

---

## Basic Exploration

### View All Node Types and Counts
```cypher
// Count all node types in the database
CALL db.labels() YIELD label
CALL apoc.cypher.run('MATCH (n:`' + label + '`) RETURN count(n) as count', {}) YIELD value
RETURN label, value.count as count
ORDER BY value.count DESC
```

### Simple Node Count (without APOC)
```cypher
// Count each node type
MATCH (p:Policy) RETURN 'Policy' as type, count(p) as count
UNION ALL
MATCH (d:DenialRule) RETURN 'DenialRule' as type, count(d) as count
UNION ALL
MATCH (f:FraudTactic) RETURN 'FraudTactic' as type, count(f) as count
UNION ALL
MATCH (c:CPTCode) RETURN 'CPTCode' as type, count(c) as count
UNION ALL
MATCH (m:Modifier) RETURN 'Modifier' as type, count(m) as count
UNION ALL
MATCH (a:Attachment) RETURN 'Attachment' as type, count(a) as count
```

### View All Relationship Types
```cypher
// List all relationship types and their counts
CALL db.relationshipTypes() YIELD relationshipType
RETURN relationshipType
ORDER BY relationshipType
```

### Database Schema Overview
```cypher
// Visualize the schema
CALL db.schema.visualization()
```

---

## Policy Queries

### List All Policies
```cypher
// Get all policies with basic info
MATCH (p:Policy)
RETURN p.policy_id as PolicyID, 
       p.title as Title, 
       p.status as Status,
       p.effective_date as EffectiveDate,
       p.line_of_business as LOB
ORDER BY p.policy_id
```

### Policy with Rule and Tactic Counts
```cypher
// Policies with their denial rules and fraud tactics counts
MATCH (p:Policy)
OPTIONAL MATCH (p)-[:CONTAINS_RULE]->(d:DenialRule)
OPTIONAL MATCH (p)-[:CONTAINS_TACTIC]->(f:FraudTactic)
RETURN p.policy_id as PolicyID,
       p.title as Title,
       count(DISTINCT d) as DenialRules,
       count(DISTINCT f) as FraudTactics
ORDER BY DenialRules DESC
```

### Policy Full Details
```cypher
// Get complete policy with all related entities
MATCH (p:Policy {policy_id: '2026R0009A'})
OPTIONAL MATCH (p)-[:CONTAINS_RULE]->(d:DenialRule)
OPTIONAL MATCH (p)-[:CONTAINS_TACTIC]->(f:FraudTactic)
OPTIONAL MATCH (p)-[:REFERENCES_ATTACHMENT]->(a:Attachment)
RETURN p, 
       collect(DISTINCT d.rule_key) as DenialRules,
       collect(DISTINCT f.tactic_key) as FraudTactics,
       collect(DISTINCT a.filename) as Attachments
```

---

## Denial Rules

### List All Denial Rules
```cypher
// Get all denial rules with severity
MATCH (d:DenialRule)
RETURN d.rule_key as RuleID,
       d.rule_name as RuleName,
       d.severity as Severity,
       d.description as Description
ORDER BY 
  CASE d.severity 
    WHEN 'critical' THEN 1 
    WHEN 'high' THEN 2 
    WHEN 'medium' THEN 3 
    WHEN 'low' THEN 4 
  END
```

### Denial Rules by Severity
```cypher
// Count rules by severity level
MATCH (d:DenialRule)
RETURN d.severity as Severity, count(d) as Count
ORDER BY 
  CASE d.severity 
    WHEN 'critical' THEN 1 
    WHEN 'high' THEN 2 
    WHEN 'medium' THEN 3 
    WHEN 'low' THEN 4 
  END
```

### Critical Denial Rules
```cypher
// Get all critical severity rules
MATCH (d:DenialRule {severity: 'critical'})
RETURN d.rule_key as RuleID,
       d.rule_name as RuleName,
       d.description as Description,
       d.source_text as PolicyText
```

### Denial Rules with CPT Codes
```cypher
// Find rules that affect specific CPT codes
MATCH (d:DenialRule)-[:AFFECTS_CODE]->(c:CPTCode)
RETURN d.rule_key as RuleID,
       d.rule_name as RuleName,
       collect(c.code) as CPTCodes
ORDER BY d.rule_key
```

### Denial Rules Requiring Specific Modifier
```cypher
// Find all rules that require modifier 25
MATCH (d:DenialRule)-[:REQUIRES_MODIFIER]->(m:Modifier {code: '25'})
RETURN d.rule_key as RuleID,
       d.rule_name as RuleName,
       d.severity as Severity
```

### Search Denial Rules by Keyword
```cypher
// Search rules by name or description
MATCH (d:DenialRule)
WHERE d.rule_name CONTAINS 'modifier' 
   OR d.description CONTAINS 'modifier'
RETURN d.rule_key as RuleID,
       d.rule_name as RuleName,
       d.description as Description
```

### Denial Rule with Detection Logic
```cypher
// Get rule with full detection logic
MATCH (d:DenialRule {rule_key: 'DENY_001'})
RETURN d.rule_key as RuleID,
       d.rule_name as RuleName,
       d.detection_logic as DetectionLogic,
       d.detection_sql as SQL,
       d.codification_steps as Steps
```

---

## Fraud Tactics

### List All Fraud Tactics
```cypher
// Get all fraud tactics with risk level
MATCH (f:FraudTactic)
RETURN f.tactic_key as TacticID,
       f.tactic_name as TacticName,
       f.risk_level as RiskLevel,
       f.exploits_rule as ExploitsRule,
       f.estimated_overpayment_per_claim as EstimatedLoss
ORDER BY 
  CASE f.risk_level 
    WHEN 'critical' THEN 1 
    WHEN 'high' THEN 2 
    WHEN 'medium' THEN 3 
    WHEN 'low' THEN 4 
  END
```

### High-Risk Fraud Tactics
```cypher
// Get critical and high risk fraud tactics
MATCH (f:FraudTactic)
WHERE f.risk_level IN ['critical', 'high']
RETURN f.tactic_key as TacticID,
       f.tactic_name as TacticName,
       f.fraud_pattern as FraudPattern,
       f.red_flags as RedFlags,
       f.estimated_overpayment_per_claim as EstimatedLoss
ORDER BY f.estimated_overpayment_per_claim DESC
```

### Fraud Tactics Exploiting Denial Rules
```cypher
// Find tactics that exploit specific denial rules
MATCH (f:FraudTactic)-[:EXPLOITS_RULE]->(d:DenialRule)
RETURN f.tactic_key as TacticID,
       f.tactic_name as TacticName,
       d.rule_key as ExploitedRule,
       d.rule_name as RuleName
ORDER BY d.rule_key
```

### Fraud Tactics with Red Flags
```cypher
// Get tactics with their warning signs
MATCH (f:FraudTactic)
WHERE f.red_flags IS NOT NULL
RETURN f.tactic_key as TacticID,
       f.tactic_name as TacticName,
       f.red_flags as RedFlags
```

### Fraud Tactic Detection Queries
```cypher
// Get SQL detection queries for fraud tactics
MATCH (f:FraudTactic)
WHERE f.detection_sql IS NOT NULL
RETURN f.tactic_key as TacticID,
       f.tactic_name as TacticName,
       f.detection_sql as DetectionSQL
```

---

## Code Analysis

### All CPT Codes in Graph
```cypher
// List all CPT codes
MATCH (c:CPTCode)
RETURN c.code as Code, c.description as Description
ORDER BY c.code
```

### CPT Codes with Most Rules
```cypher
// Find CPT codes affected by most denial rules
MATCH (c:CPTCode)<-[:AFFECTS_CODE]-(d:DenialRule)
RETURN c.code as CPTCode,
       c.description as Description,
       count(d) as RuleCount,
       collect(d.rule_key) as Rules
ORDER BY RuleCount DESC
LIMIT 20
```

### All Modifiers in Graph
```cypher
// List all modifiers
MATCH (m:Modifier)
RETURN m.code as Code, m.description as Description
ORDER BY m.code
```

### Modifier Usage Analysis
```cypher
// Find which modifiers are required by most rules
MATCH (m:Modifier)<-[:REQUIRES_MODIFIER]-(d:DenialRule)
RETURN m.code as Modifier,
       m.description as Description,
       count(d) as RuleCount,
       collect(d.rule_key) as Rules
ORDER BY RuleCount DESC
```

### Place of Service Codes
```cypher
// List all POS codes
MATCH (pos:POSCode)
RETURN pos.code as Code, 
       pos.description as Description,
       pos.category as Category
ORDER BY pos.code
```

---

## Relationship Queries

### Policy to Rules Path
```cypher
// Visualize policy to denial rules relationship
MATCH path = (p:Policy)-[:CONTAINS_RULE]->(d:DenialRule)
WHERE p.policy_id = '2026R0009A'
RETURN path
LIMIT 50
```

### Rule to Code Relationships
```cypher
// Find all codes affected by a specific rule
MATCH (d:DenialRule {rule_key: 'DENY_001'})-[r]->(code)
WHERE code:CPTCode OR code:HCPCSCode OR code:Modifier
RETURN type(r) as Relationship,
       labels(code)[0] as CodeType,
       code.code as Code,
       code.description as Description
```

### Fraud Tactic to Rule Chain
```cypher
// Show fraud tactics and the rules they exploit
MATCH path = (f:FraudTactic)-[:EXPLOITS_RULE]->(d:DenialRule)<-[:CONTAINS_RULE]-(p:Policy)
RETURN path
LIMIT 50
```

### Full Policy Graph
```cypher
// Get entire graph for a policy (limit for visualization)
MATCH (p:Policy {policy_id: '2026R0009A'})
OPTIONAL MATCH path1 = (p)-[:CONTAINS_RULE]->(d:DenialRule)-[]->(code)
OPTIONAL MATCH path2 = (p)-[:CONTAINS_TACTIC]->(f:FraudTactic)
OPTIONAL MATCH path3 = (p)-[:REFERENCES_ATTACHMENT]->(a:Attachment)
RETURN p, path1, path2, path3
LIMIT 100
```

### Attachment to Rule Connections
```cypher
// Find which attachments support which rules
MATCH (a:Attachment)-[:SUPPORTS_RULE]->(d:DenialRule)
RETURN a.filename as Attachment,
       a.attachment_name as Name,
       collect(d.rule_key) as SupportedRules
```

---

## Analytics & Reporting

### Policy Coverage Summary
```cypher
// Summary of all policies with metrics
MATCH (p:Policy)
OPTIONAL MATCH (p)-[:CONTAINS_RULE]->(d:DenialRule)
OPTIONAL MATCH (p)-[:CONTAINS_TACTIC]->(f:FraudTactic)
OPTIONAL MATCH (p)-[:REFERENCES_ATTACHMENT]->(a:Attachment)
WITH p, 
     count(DISTINCT d) as rules,
     count(DISTINCT f) as tactics,
     count(DISTINCT a) as attachments
RETURN p.policy_id as PolicyID,
       p.title as Title,
       rules as DenialRules,
       tactics as FraudTactics,
       attachments as Attachments,
       rules + tactics as TotalRulesAndTactics
ORDER BY TotalRulesAndTactics DESC
```

### Severity Distribution
```cypher
// Distribution of denial rules by severity
MATCH (d:DenialRule)
WITH d.severity as severity, count(*) as count
RETURN severity, count,
       round(100.0 * count / sum(count) OVER (), 2) as percentage
ORDER BY 
  CASE severity 
    WHEN 'critical' THEN 1 
    WHEN 'high' THEN 2 
    WHEN 'medium' THEN 3 
    WHEN 'low' THEN 4 
  END
```

### Estimated Fraud Impact
```cypher
// Total estimated overpayment by fraud tactic
MATCH (f:FraudTactic)
WHERE f.estimated_overpayment_per_claim IS NOT NULL
RETURN sum(f.estimated_overpayment_per_claim) as TotalEstimatedLossPerClaim,
       avg(f.estimated_overpayment_per_claim) as AvgLossPerClaim,
       max(f.estimated_overpayment_per_claim) as MaxLossPerClaim,
       count(f) as TotalTactics
```

### Most Exploited Rules
```cypher
// Find denial rules that are most exploited by fraud tactics
MATCH (d:DenialRule)<-[:EXPLOITS_RULE]-(f:FraudTactic)
RETURN d.rule_key as RuleID,
       d.rule_name as RuleName,
       d.severity as Severity,
       count(f) as ExploitCount,
       collect(f.tactic_key) as ExploitingTactics
ORDER BY ExploitCount DESC
```

### Code Vulnerability Analysis
```cypher
// Find codes that are both in denial rules and fraud tactics
MATCH (c:CPTCode)<-[:AFFECTS_CODE]-(d:DenialRule)
OPTIONAL MATCH (c)<-[:EXPLOITS_CODE]-(f:FraudTactic)
WITH c, count(DISTINCT d) as ruleCount, count(DISTINCT f) as tacticCount
WHERE tacticCount > 0
RETURN c.code as CPTCode,
       c.description as Description,
       ruleCount as DenialRules,
       tacticCount as FraudTactics,
       ruleCount + tacticCount as TotalExposure
ORDER BY TotalExposure DESC
```

---

## Advanced Queries

### Find Unprotected Rules
```cypher
// Find denial rules without fraud tactic coverage
MATCH (d:DenialRule)
WHERE NOT EXISTS {
  MATCH (d)<-[:EXPLOITS_RULE]-(f:FraudTactic)
}
RETURN d.rule_key as RuleID,
       d.rule_name as RuleName,
       d.severity as Severity
ORDER BY 
  CASE d.severity 
    WHEN 'critical' THEN 1 
    WHEN 'high' THEN 2 
    WHEN 'medium' THEN 3 
    WHEN 'low' THEN 4 
  END
```

### Modifier 25 Analysis
```cypher
// Complete analysis of Modifier 25 usage
MATCH (m:Modifier {code: '25'})
OPTIONAL MATCH (m)<-[:REQUIRES_MODIFIER]-(d:DenialRule)
OPTIONAL MATCH (m)<-[:EXPLOITS_CODE]-(f:FraudTactic)
RETURN m.code as Modifier,
       m.description as Description,
       collect(DISTINCT d.rule_key) as DenialRules,
       collect(DISTINCT f.tactic_key) as FraudTactics
```

### Same-Day Service Rules
```cypher
// Find rules that apply to same-day services
MATCH (d:DenialRule)
WHERE d.detection_logic.same_date_of_service = true
RETURN d.rule_key as RuleID,
       d.rule_name as RuleName,
       d.detection_logic as Logic
```

### Global Period Rules
```cypher
// Find rules related to global periods
MATCH (d:DenialRule)
WHERE d.detection_logic.time_window CONTAINS 'global'
   OR d.rule_name CONTAINS 'Global'
   OR d.description CONTAINS 'global'
RETURN d.rule_key as RuleID,
       d.rule_name as RuleName,
       d.detection_logic.time_window as TimeWindow
```

### Cross-Policy Code Analysis
```cypher
// Find CPT codes that appear in multiple policies
MATCH (c:CPTCode)<-[:AFFECTS_CODE]-(d:DenialRule)<-[:CONTAINS_RULE]-(p:Policy)
WITH c, collect(DISTINCT p.policy_id) as policies
WHERE size(policies) > 1
RETURN c.code as CPTCode,
       c.description as Description,
       size(policies) as PolicyCount,
       policies as Policies
ORDER BY PolicyCount DESC
```

### Rule Dependency Chain
```cypher
// Find rules that share common codes (potential conflicts)
MATCH (d1:DenialRule)-[:AFFECTS_CODE]->(c:CPTCode)<-[:AFFECTS_CODE]-(d2:DenialRule)
WHERE d1.rule_key < d2.rule_key
RETURN d1.rule_key as Rule1,
       d2.rule_key as Rule2,
       collect(c.code) as SharedCodes
ORDER BY size(SharedCodes) DESC
LIMIT 20
```

### Full Text Search (requires index)
```cypher
// Create full-text index first (run once)
// CREATE FULLTEXT INDEX ruleSearch FOR (d:DenialRule) ON EACH [d.rule_name, d.description, d.source_text]

// Then search
// CALL db.index.fulltext.queryNodes('ruleSearch', 'modifier injection') YIELD node, score
// RETURN node.rule_key, node.rule_name, score
// ORDER BY score DESC
```

---

## Data Maintenance Queries

### Find Orphan Nodes
```cypher
// Find codes not connected to any rule
MATCH (c:CPTCode)
WHERE NOT EXISTS {
  MATCH (c)<-[:AFFECTS_CODE]-(:DenialRule)
}
RETURN c.code as OrphanCode, c.description as Description
```

### Validate Rule Completeness
```cypher
// Find rules missing required fields
MATCH (d:DenialRule)
WHERE d.source_text IS NULL 
   OR d.detection_sql IS NULL
   OR d.severity IS NULL
RETURN d.rule_key as RuleID,
       d.rule_name as RuleName,
       CASE WHEN d.source_text IS NULL THEN 'source_text' ELSE '' END +
       CASE WHEN d.detection_sql IS NULL THEN ', detection_sql' ELSE '' END +
       CASE WHEN d.severity IS NULL THEN ', severity' ELSE '' END as MissingFields
```

### Update Analytics Counters
```cypher
// Reset all analytics counters (use with caution)
// MATCH (d:DenialRule)
// SET d.total_times_fired = 0,
//     d.total_denials = 0,
//     d.total_financial_impact = 0.0
// RETURN count(d) as UpdatedRules
```

---

## Quick Reference

### Common Filters
```cypher
// By severity
WHERE d.severity = 'critical'
WHERE d.severity IN ['critical', 'high']

// By date
WHERE d.effective_date >= '2026-01-01'

// By status
WHERE d.status = 'active'

// Text contains
WHERE d.rule_name CONTAINS 'modifier'
WHERE toLower(d.description) CONTAINS 'injection'
```

### Aggregation Functions
```cypher
// count, sum, avg, min, max, collect
count(d) as total
sum(f.estimated_overpayment_per_claim) as totalLoss
collect(d.rule_key) as ruleList
collect(DISTINCT d.severity) as severities
```

### Path Patterns
```cypher
// Direct relationship
(a)-[:RELATIONSHIP]->(b)

// Any relationship
(a)-[r]->(b)

// Variable length (1-3 hops)
(a)-[*1..3]->(b)

// Named path
path = (a)-[:REL]->(b)
```

---

## Notes

1. **Performance**: For large graphs, always use `LIMIT` when exploring
2. **Indexes**: Create indexes on frequently queried properties:
   ```cypher
   CREATE INDEX policy_id_index FOR (p:Policy) ON (p.policy_id)
   CREATE INDEX rule_key_index FOR (d:DenialRule) ON (d.rule_key)
   CREATE INDEX tactic_key_index FOR (f:FraudTactic) ON (f.tactic_key)
   CREATE INDEX cpt_code_index FOR (c:CPTCode) ON (c.code)
   ```
3. **Visualization**: Use Neo4j Browser for graph visualization
4. **APOC**: Some queries require APOC library - install if needed
