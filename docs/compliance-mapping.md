# AI Trust OS - Compliance Mapping

## Overview

This document maps AI Trust OS controls to major compliance frameworks:
- NIST AI Risk Management Framework (AI RMF)
- ISO/IEC 42001 - Artificial Intelligence Management System
- SOC 2 Trust Services Criteria

## Framework Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     AI Trust OS Compliance Architecture              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   NIST AI RMF          ISO 42001          SOC 2                      │
│   ┌─────────┐          ┌─────────┐        ┌─────────┐              │
│   │ Govern  │          │ Context │        │ Security│              │
│   │ Map     │          │ Policy  │        │ Availability│          │
│   │ Measure │          │ Support │        │ Processing  │          │
│   │ Manage  │          │ Ops     │        │ Integrity   │          │
│   └────┬────┘          │ Eval    │        │ Privacy     │          │
│        │               └────┬────┘        │ Confidentiality│       │
│        │                    │               └─────┬─────┘            │
│        └────────────────────┼─────────────────────┘                   │
│                             │                                        │
│                             ▼                                        │
│              ┌─────────────────────────────┐                       │
│              │      AI Trust OS Controls    │                       │
│              │                              │                       │
│              │ • Bedrock Guardrails         │                       │
│              │ • Neptune Asset Discovery    │                       │
│              │ • OpenSearch Telemetry       │                       │
│              │ • Step Functions Review      │                       │
│              │ • PrivateLink Security       │                       │
│              └─────────────────────────────┘                       │
└─────────────────────────────────────────────────────────────────────┘
```

## NIST AI Risk Management Framework (AI RMF)

### Govern (GO)

| AI RMF Function | Subcategory | AI Trust OS Control | Implementation |
|-----------------|-------------|---------------------|----------------|
| GOVERN 1 | Establish governance | CodeGuru Reviewer | Automated code scanning for AI SDK usage |
| GOVERN 2 | Define roles | IAM Integration | Role-based access to Bedrock models |
| GOVERN 3 | Policies defined | Bedrock Guardrails | Content policies enforced at API level |
| GOVERN 4 | Risk management | Config Rules | Automated compliance monitoring |
| GOVERN 5 | Legal compliance | Audit Manager | Continuous compliance assessment |

### Map (MAP)

| AI RMF Function | Subcategory | AI Trust OS Control | Implementation |
|-----------------|-------------|---------------------|----------------|
| MAP 1 | Context established | Neptune Graph | AI asset inventory and relationships |
| MAP 2 | Categorize AI systems | Config Rules | Automated classification |
| MAP 3 | Impacts identified | CloudTrail + Neptune | Usage pattern analysis |
| MAP 4 | Risks identified | Guardrail Metrics | Intervention tracking |

### Measure (MEA)

| AI RMF Function | Subcategory | AI Trust OS Control | Implementation |
|-----------------|-------------|---------------------|----------------|
| MEA 1 | Metrics identified | CloudWatch Dashboards | Latency, token usage, error rates |
| MEA 2 | Evaluate AI system | Bedrock Evaluations | Automated model assessments |
| MEA 3 | Track metrics | OpenSearch | Long-term telemetry storage |
| MEA 4 | Feedback loops | Step Functions | Human review workflows |

### Manage (MNG)

| AI RMF Function | Subcategory | AI Trust OS Control | Implementation |
|-----------------|-------------|---------------------|----------------|
| MNG 1 | Risk prioritized | Guardrail Alerts | High-intervention alerting |
| MNG 2 | Risk strategies | IAM Policies | Least-privilege access |
| MNG 3 | Response planned | SNS Notifications | Incident response triggers |
| MNG 4 | Incidents managed | CloudWatch Alarms | Automated detection |
| MNG 5 | Errors identified | Error Logging | Root cause analysis |

## ISO/IEC 42001 Mapping

### Clause 4: Context of the Organization

| ISO 42001 Clause | AI Trust OS Implementation | Evidence |
|------------------|------------------------------|----------|
| 4.1 | Neptune asset discovery | Asset inventory graph |
| 4.2 | Stakeholder mapping | IAM user/role tracking |
| 4.3 | AI system scope | Config Rules for scope definition |
| 4.4 | Management system | CloudFormation templates |

### Clause 5: Leadership

| ISO 42001 Clause | AI Trust OS Implementation | Evidence |
|------------------|------------------------------|----------|
| 5.1 | Bedrock Guardrails | Policy configuration |
| 5.2 | IAM policies | Role definitions |
| 5.3 | CloudTrail logging | Leadership audit trail |

### Clause 6: Planning

| ISO 42001 Clause | AI Trust OS Implementation | Evidence |
|------------------|------------------------------|----------|
| 6.1 | Risk assessment | Guardrail intervention metrics |
| 6.2 | Objectives | CloudWatch metrics and alarms |
| 6.3 | Planning changes | Change tracking in Neptune |

### Clause 7: Support

| ISO 42001 Clause | AI Trust OS Implementation | Evidence |
|------------------|------------------------------|----------|
| 7.1 | Resources | Cost Explorer tagging |
| 7.2 | Competence | Training records (external) |
| 7.3 | Awareness | Documentation in Confluence |
| 7.4 | Communication | SNS notification logs |
| 7.5 | Documentation | CloudFormation templates |

### Clause 8: Operation

| ISO 42001 Clause | AI Trust OS Implementation | Evidence |
|------------------|------------------------------|----------|
| 8.1 | Operational planning | Bedrock deployment guides |
| 8.2 | AI risk assessment | Guardrail effectiveness |
| 8.3 | AI system changes | Neptune change tracking |
| 8.4 | Third-party management | Vendor IAM roles |

### Clause 9: Performance Evaluation

| ISO 42001 Clause | AI Trust OS Implementation | Evidence |
|------------------|------------------------------|----------|
| 9.1 | Monitoring | CloudWatch Dashboards |
| 9.2 | Internal audit | Audit Manager assessments |
| 9.3 | Management review | Quarterly reports from OpenSearch |

### Clause 10: Improvement

| ISO 42001 Clause | AI Trust OS Implementation | Evidence |
|------------------|------------------------------|----------|
| 10.1 | Nonconformity | Guardrail block tracking |
| 10.2 | Corrective action | Step Functions remediation |
| 10.3 | Continual improvement | Model evaluation pipeline |

## SOC 2 Trust Services Criteria

### Security (CC1-CC7)

| TSC | Control Point | AI Trust OS Implementation | Test Approach |
|-----|---------------|---------------------------|---------------|
| CC1.1 | Governance | CloudFormation IAM roles | Review role policies |
| CC1.2 | Communication | SNS notification logs | Inspect SNS history |
| CC1.3 | Roles | IAM identity integration | Validate user permissions |
| CC2.1 | Risk assessment | Guardrail metrics | Review intervention rates |
| CC2.2 | Vendor management | Bedrock service-linked roles | Validate SLR permissions |
| CC3.1 | Risk mitigation | Config compliance packs | Run compliance report |
| CC4.1 | Monitoring | CloudWatch dashboards | Verify metric collection |
| CC5.1 | Control design | Guardrail configurations | Review policy settings |
| CC6.1 | Logical access | Cognito + IAM policies | Test authentication flows |
| CC6.2 | Access removal | IAM access analyzer | Review findings |
| CC6.3 | Access changes | CloudTrail IAM events | Query for changes |
| CC6.4 | Segregation | VPC endpoints with policies | Validate endpoint policies |
| CC6.5 | Credentials | Cognito MFA + rotation | Test MFA enforcement |
| CC6.6 | Authentication | Private API Gateway | Test unauthenticated access |
| CC6.7 | Encryption | KMS key policies | Verify encryption settings |
| CC6.8 | Malware | Guardrails content filtering | Test blocked content |
| CC7.1 | Detection | CloudWatch anomaly detection | Review alarm history |
| CC7.2 | Vulnerability | CodeGuru security scans | Review findings |
| CC7.3 | Incident response | Step Functions workflows | Test escalation paths |

### Availability (A1)

| TSC | Control Point | AI Trust OS Implementation | Test Approach |
|-----|---------------|---------------------------|---------------|
| A1.1 | Availability policy | Neptune backup policies | Review backup schedules |
| A1.2 | System monitoring | CloudWatch health checks | Validate alarms |
| A1.3 | Recovery | Neptune snapshots | Test point-in-time restore |

### Processing Integrity (PI1)

| TSC | Control Point | AI Trust OS Implementation | Test Approach |
|-----|---------------|---------------------------|---------------|
| PI1.1 | Input validation | Bedrock Guardrails | Test content filtering |
| PI1.2 | Processing | CloudTrail logging | Verify all invocations logged |
| PI1.3 | Output | Guardrail response handling | Test output validation |

### Confidentiality (C1)

| TSC | Control Point | AI Trust OS Implementation | Test Approach |
|-----|---------------|---------------------------|---------------|
| C1.1 | Classification | Neptune asset tagging | Review classification labels |
| C1.2 | Access | IAM policies with encryption | Test encrypted access |
| C1.3 | Transmission | PrivateLink endpoints | Verify no public exposure |
| C1.4 | Storage | KMS encrypted S3 + Neptune | Validate encryption at rest |
| C1.5 | Disposal | S3 lifecycle policies | Review retention settings |

## Control Implementation Matrix

### Preventive Controls

| Control | Technology | Frequency | Evidence |
|---------|------------|-----------|----------|
| Content filtering | Bedrock Guardrails | Real-time | CloudWatch metrics |
| Access control | IAM + Cognito | Continuous | CloudTrail logs |
| Network isolation | VPC + PrivateLink | Continuous | VPC Flow Logs |
| Encryption | KMS | Continuous | Key usage logs |
| Code review | CodeGuru | On commit | Review findings |

### Detective Controls

| Control | Technology | Frequency | Evidence |
|---------|------------|-----------|----------|
| Audit logging | CloudTrail | Continuous | S3 log archive |
| Anomaly detection | CloudWatch | 5-minute intervals | Alarm history |
| Compliance monitoring | AWS Config | Hourly | Config timeline |
| Usage analysis | OpenSearch | Real-time | Dashboard data |
| Asset discovery | Neptune | 5-minute sync | Graph queries |

### Corrective Controls

| Control | Technology | Trigger | Evidence |
|---------|------------|---------|----------|
| Human review | Step Functions | Guardrail intervention | DynamoDB records |
| Access revocation | IAM | Config non-compliance | CloudTrail events |
| Data backup | Neptune | Scheduled | Snapshot list |
| Incident response | SNS + Lambda | Alarm threshold | Notification logs |

## Evidence Collection Guide

### For Auditors

```bash
# 1. Export CloudTrail events for AI services
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventSource,AttributeValue=bedrock.amazonaws.com \
  --max-items 1000 \
  --region us-east-1

# 2. Generate Config compliance report
aws config get-compliance-details-by-config-rule \
  --config-rule-name ai-trust-os-bedrock-guardrail-${ENVIRONMENT}

# 3. Export OpenSearch telemetry
curl -X GET "https://${OPENSEARCH_DOMAIN}/bedrock-invocations/_search" \
  -H "Content-Type: application/json" \
  -d '{"size": 10000, "query": {"range": {"@timestamp": {"gte": "now-30d"}}}}'

# 4. Neptune asset inventory
gremlin> g.V().hasLabel('asset').valueMap().toList()

# 5. Guardrail effectiveness
curl -X GET "https://${OPENSEARCH_DOMAIN}/guardrail-interventions/_search" \
  -d '{"aggs": {"by_type": {"terms": {"field": "intervention_type"}}}}'
```

### For Continuous Compliance

```python
# Automated compliance evidence collection
import boto3
import json
from datetime import datetime, timedelta

def collect_evidence():
    """Collect compliance evidence from AI Trust OS."""
    
    evidence = {
        'timestamp': datetime.utcnow().isoformat(),
        'controls': {}
    }
    
    # 1. IAM policy compliance
    iam = boto3.client('iam')
    roles = iam.list_roles(PathPrefix='/ai-trust-os/')
    evidence['controls']['iam'] = {
        'role_count': len(roles['Roles']),
        'roles_with_external_id': sum(1 for r in roles['Roles'] if r.get('AssumeRolePolicyDocument', {}).get('ExternalId'))
    }
    
    # 2. Encryption status
    kms = boto3.client('kms')
    keys = kms.list_keys()
    evidence['controls']['encryption'] = {
        'cmk_count': len(keys['Keys']),
        'key_rotation_enabled': []
    }
    for key in keys['Keys']:
        try:
            rotation = kms.get_key_rotation_status(KeyId=key['KeyId'])
            if rotation['KeyRotationEnabled']:
                evidence['controls']['encryption']['key_rotation_enabled'].append(key['KeyId'])
        except:
            pass
    
    # 3. Guardrail interventions (last 24h)
    cloudwatch = boto3.client('cloudwatch')
    response = cloudwatch.get_metric_statistics(
        Namespace='AWS/Bedrock',
        MetricName='GuardrailInterventions',
        StartTime=datetime.utcnow() - timedelta(days=1),
        EndTime=datetime.utcnow(),
        Period=86400,
        Statistics=['Sum']
    )
    evidence['controls']['guardrails'] = {
        'interventions_24h': sum(dp['Sum'] for dp in response['Datapoints'])
    }
    
    # 4. Neptune backup compliance
    neptune = boto3.client('neptune')
    clusters = neptune.describe_db_clusters(
        Filters=[{'Name': 'db-cluster-id', 'Values': ['ai-trust-os-neptune-cluster-*']}]
    )
    evidence['controls']['backup'] = {
        'cluster_count': len(clusters['DBClusters']),
        'deletion_protection': [c['DBClusterIdentifier'] for c in clusters['DBClusters'] if c.get('DeletionProtection')]
    }
    
    return evidence

# Run and save
evidence = collect_evidence()
with open(f"evidence-{datetime.utcnow().strftime('%Y%m%d')}.json", 'w') as f:
    json.dump(evidence, f, indent=2)
```

## Compliance Reporting Dashboard

The AI Trust OS includes a CloudWatch Dashboard for compliance metrics:

```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "title": "Guardrail Effectiveness (SOC 2 CC5.1)",
        "metrics": [
          ["AWS/Bedrock", "GuardrailInterventions", {"stat": "Sum"}]
        ],
        "period": 86400,
        "yAxis": {"left": {"min": 0}}
      }
    },
    {
      "type": "log",
      "properties": {
        "title": "IAM Policy Changes (ISO 42001 6.2)",
        "query": "SOURCE 'cloudtrail' | fields @timestamp, eventName, userIdentity.arn | filter eventSource = 'iam.amazonaws.com' and eventName like /(Create|Delete|Attach|Detach)/ | sort @timestamp desc | limit 20",
        "region": "us-east-1"
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "Encryption Key Usage (SOC 2 CC6.7)",
        "metrics": [
          ["AWS/KMS", "Encrypt", {"stat": "Sum"}],
          [".", "Decrypt", {"stat": "Sum"}]
        ],
        "period": 3600
      }
    }
  ]
}
```

## Certification Paths

### ISO 42001 Preparation Checklist

- [x] AI system inventory (Neptune graph)
- [x] Risk assessment process (Guardrail metrics)
- [x] Policy documentation (Guardrail configs)
- [x] Competence records (External training)
- [x] Monitoring system (CloudWatch)
- [x] Internal audit (Audit Manager)
- [x] Management review (Quarterly reports)
- [x] Continuous improvement (Model evaluation pipeline)

### SOC 2 Type II Evidence

| Month | Evidence Type | Source |
|-------|--------------|--------|
| Month 1 | IAM access reviews | IAM Access Analyzer |
| Month 2 | Guardrail effectiveness | CloudWatch metrics |
| Month 3 | Vulnerability scan | CodeGuru findings |
| Month 4 | Backup testing | Neptune restore test |
| Month 5 | Incident response | Step Functions logs |
| Month 6 | Policy review | Config compliance |

## Regulatory Considerations

### GDPR (European Union)

| Requirement | AI Trust OS Implementation |
|-------------|---------------------------|
| Art. 5 - Data minimization | PII redaction in Guardrails |
| Art. 17 - Right to erasure | S3 lifecycle policies |
| Art. 25 - Privacy by design | Default encryption |
| Art. 32 - Security | KMS + TLS 1.2 |
| Art. 35 - DPIA | Neptune impact tracking |

### CCPA (California)

| Requirement | AI Trust OS Implementation |
|-------------|---------------------------|
| Data inventory | Neptune asset graph |
| Consumer rights | Self-service via Cognito |
| Third-party disclosure | IAM role tracking |
| Security safeguards | VPC isolation |

### AI Act (European Union - Proposed)

| Requirement | AI Trust OS Implementation |
|-------------|---------------------------|
| Risk classification | Config Rules |
| Documentation | CloudFormation templates |
| Human oversight | Step Functions review |
| Transparency | OpenSearch queryable logs |
| Accuracy | Bedrock evaluations |

## Continuous Compliance

The AI Trust OS architecture enables continuous compliance through:

1. **Automated evidence collection** - CloudTrail, Config, CloudWatch
2. **Real-time compliance monitoring** - Config Rules and Guardrails
3. **Self-documenting infrastructure** - CloudFormation templates
4. **Immutable audit logs** - S3 with Object Lock
5. **Queryable telemetry** - OpenSearch for investigations

This approach shifts compliance from periodic assessments to continuous assurance.