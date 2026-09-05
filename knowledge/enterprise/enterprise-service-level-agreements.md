# Enterprise Service Level Agreements

## Overview

This document defines the Service Level Agreements (SLAs) provided to SmartConnect enterprise customers. Enterprise SLAs include enhanced guarantees for network availability, performance, and support responsiveness.

## SLA Tiers

### Platinum SLA

Target: 99.99% network availability. Maximum 4.3 minutes of downtime per month. Response time: 15 minutes for critical issues, 1 hour for high issues. Resolution time: 4 hours for critical issues, 8 hours for high issues. Dedicated account manager available 24/7. Quarterly business reviews.

### Gold SLA

Target: 99.95% network availability. Maximum 21.9 minutes of downtime per month. Response time: 30 minutes for critical issues, 2 hours for high issues. Resolution time: 8 hours for critical issues, 24 hours for high issues. Dedicated account manager available during business hours. Monthly performance reports.

### Silver SLA

Target: 99.9% network availability. Maximum 43.8 minutes of downtime per month. Response time: 1 hour for critical issues, 4 hours for high issues. Resolution time: 24 hours for critical issues, 48 hours for high issues. Shared account manager. Quarterly performance reports.

## Availability Measurement

### Measurement Period

SLA availability is measured on a monthly basis. The measurement period is the calendar month. Availability is calculated at the end of each measurement period.

### Exclusions

Scheduled maintenance windows are excluded from availability calculations. Maintenance windows must be scheduled at least 72 hours in advance. Maximum maintenance window is 4 hours per month. Emergency maintenance is excluded but must be reported within 24 hours.

### Downtime Definition

Downtime is defined as any period where the customer's primary connection is completely unavailable. Degraded performance does not constitute downtime unless it falls below 50% of the guaranteed bandwidth for more than 15 consecutive minutes.

## Performance Guarantees

### Bandwidth

Enterprise SLAs guarantee minimum bandwidth levels. Guaranteed bandwidth is specified in the customer's service agreement. Actual bandwidth may exceed the guarantee during non-peak hours. Bandwidth is measured at the customer's demarcation point.

### Latency

Maximum latency from customer premises to SmartConnect network edge: Platinum: 10ms, Gold: 20ms, Silver: 30ms. Latency is measured using continuous synthetic probes. Latency measurements are averaged over 5-minute intervals.

### Packet Loss

Maximum packet loss: Platinum: 0.01%, Gold: 0.05%, Silver: 0.1%. Packet loss is measured using continuous synthetic probes. Packet loss measurements are averaged over 5-minute intervals.

## Credit Structure

### Availability Credits

Credits for availability SLA breaches are calculated as a percentage of the monthly service fee. Platinum: 5% credit per 0.01% below guarantee. Gold: 5% credit per 0.05% below guarantee. Silver: 5% credit per 0.1% below guarantee. Maximum credit is 100% of the monthly service fee.

### Performance Credits

Credits for performance SLA breaches: Latency exceeded: 10% credit per measurement period. Packet loss exceeded: 10% credit per measurement period. Bandwidth below guarantee: 20% credit per measurement period. Performance credits are in addition to availability credits.

### Claim Process

Enterprise customers must submit SLA credit claims within 30 days of the breach. Claims must include the date, time, and duration of the breach. SmartConnect will validate the claim against monitoring data. Credits are applied within 30 days of claim approval.

## Support SLAs

### Response Times

Platinum: 15 minutes for P1, 30 minutes for P2, 1 hour for P3, 4 hours for P4. Gold: 30 minutes for P1, 1 hour for P2, 2 hours for P3, 8 hours for P4. Silver: 1 hour for P1, 2 hours for P2, 4 hours for P3, 24 hours for P4.

### Resolution Times

Platinum: 4 hours for P1, 8 hours for P2, 24 hours for P3, 72 hours for P4. Gold: 8 hours for P1, 24 hours for P2, 48 hours for P3, 96 hours for P4. Silver: 24 hours for P1, 48 hours for P2, 96 hours for P3, 120 hours for P4.

### Escalation Paths

Enterprise customers have direct escalation paths to senior engineering and management. Escalation contacts are provided in the service agreement. Escalation response times are guaranteed in the SLA.

## Reporting and Review

### Monthly Reports

Enterprise customers receive monthly performance reports. Reports include availability measurements, performance metrics, incident summaries, and credit calculations. Reports are delivered within 5 business days of the measurement period end.

### Quarterly Business Reviews

Platinum and Gold customers receive quarterly business reviews. Reviews include SLA performance analysis, trend review, capacity planning, and optimization recommendations. Reviews are conducted by the account manager and technical team.

### Annual Reviews

All enterprise customers receive annual reviews. Reviews include comprehensive SLA performance, contract review, and planning for the upcoming year. Reviews are conducted by senior management and the account team.
