# Network Health Monitoring Standards

## Overview

This document defines the monitoring standards used to assess network health across SmartConnect infrastructure. All monitoring follows the three-state model: Healthy, Degraded, and Critical.

## Health State Definitions

### Healthy

All network sites in the monitored group are operational with no active events. No alarms with severity higher than informational are present. Key performance indicators are within normal thresholds.

### Degraded

One or more sites are in maintenance mode or have active non-critical events. Performance metrics are elevated but service is available. Customer impact is limited or non-existent.

### Critical

One or more sites are offline. Active critical or high-severity events are present. Service is disrupted or significantly degraded. Customer-facing services are affected.

## Health Determination Logic

The network health status is calculated using the following deterministic rules:

1. If any sites in the monitored set have status "offline", the health is "critical".
2. If any sites have active events with event_type "maintenance" or "degradation", the health is "degraded".
3. Otherwise, the health is "healthy".

These rules are applied in priority order. Critical status overrides degraded, which overrides healthy.

## Monitoring Endpoints

### GET /api/network/health

Returns aggregated network health for all sites or filtered by region. Response includes total sites, operational count, degraded count, maintenance count, offline count, overall status, and active event count.

### GET /api/network/sites

Returns individual site status with health indicators. Each site includes its current operational state, capacity utilization, and last maintenance timestamp.

## Key Metrics

### Site Availability

Measured as percentage of time a site is operational in a 24-hour window. Target is 99.9% for Tier 1 sites, 99.5% for Tier 2 sites, and 99.0% for Tier 3 sites.

### Capacity Utilization

Current utilization as percentage of total capacity. Thresholds: below 60% is normal, 60-80% is elevated, 80-95% is high, above 95% is critical.

### Event Rate

Number of active events per site. More than 3 active events per site triggers a review. More than 5 active events per site triggers automatic escalation.

### Response Time

Average round-trip time for synthetic probes. Baseline is established during the first 7 days of monitoring. Deviations greater than 50% from baseline trigger alerts.

## Alert Thresholds

### Immediate Alert (P1)

Site offline for more than 5 minutes. More than 500 customers affected. Backbone link failure. Core router interface down.

### Urgent Alert (P2)

Site degraded for more than 15 minutes. Capacity above 90%. Error rate above 0.1%. BNG session count above 80% capacity.

### Warning (P3)

Site in maintenance for more than 4 hours. Capacity above 75%. Error rate above 0.01%. Backhaul utilization above 70%.

### Informational (P4)

Scheduled maintenance starting. Capacity above 60%. Minor configuration change applied. Software update completed.

## Dashboard Integration

The monitoring data feeds into the Operations Overview dashboard. Key metrics displayed include network health status, site status counts, active events, and regional health breakdown. All metrics update in real-time through the API layer.

## SLA Thresholds

For enterprise customers, additional SLA-specific monitoring applies. Network availability must meet the terms specified in the customer's service level agreement. Breach of SLA thresholds triggers automatic escalation and customer notification.
