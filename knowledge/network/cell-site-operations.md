# Cell Site Operations Guide

## Site Types

### Macro Sites

Full-size cell towers providing wide area coverage. Typically mounted on dedicated towers or building rooftops. Equipment includes baseband units, remote radio heads, antennas, and backhaul equipment. Macro sites serve the highest number of users and carry the most traffic.

### Small Cells

Low-power base stations for capacity injection in high-density areas. Mounted on street furniture, utility poles, or building facades. Used to fill coverage gaps and boost capacity in urban cores. Typically connect via fiber or microwave backhaul.

### Distributed Antenna Systems (DAS)

Network of antennas distributed throughout a building or venue. Used for indoor coverage in large facilities such as airports, stadiums, and convention centers. Connected to a central base station via fiber or coaxial cable.

## Site Status Codes

### Operational

Site is fully functional and serving customers. All equipment is powered and connected. No active alarms above informational level.

### Degraded

Site is operational but experiencing issues. May have reduced capacity, single-carrier operation, or minor equipment faults. Customers may experience degraded service quality.

### Maintenance

Site is undergoing planned work. May be partially or fully out of service during maintenance window. Customers should be notified before scheduled maintenance.

### Offline

Site is not operational. No service is being provided. Customers in the coverage area are affected. Immediate investigation is required.

## Capacity Management

### Normal Utilization (0-60%)

Site is operating well within capacity. No action required. Continue monitoring.

### Elevated Utilization (60-80%)

Site is approaching capacity limits. Schedule capacity upgrade assessment. Consider adding carriers or upgrading hardware. Monitor for further increases.

### High Utilization (80-95%)

Site is near maximum capacity. Initiate capacity expansion project. Implement traffic management policies. Consider temporary solutions such as COW (Cell on Wheels).

### Critical Utilization (95%+)

Site is at or beyond capacity. Immediate capacity injection required. Implement emergency traffic management. Prioritize voice over data if necessary.

## Backhaul Requirements

### Fiber Backhaul

Preferred for high-capacity sites. Minimum 1 Gbps for macro sites, 100 Mbps for small cells. Redundant paths required for Tier 1 sites. Latency must be below 5ms.

### Microwave Backhaul

Used where fiber is not available. Minimum 200 Mbps for macro sites. Dual diversity required for reliable operation. Frequency coordination needed to avoid interference.

### Satellite Backhaul

Used for remote sites only. Minimum 50 Mbps. High latency (600ms+) is expected. Used as temporary solution while fiber or microwave is deployed.

## Maintenance Procedures

### Preventive Maintenance

Quarterly inspection of all sites. Includes physical inspection, equipment testing, firmware updates, and cleaning. Battery backup testing monthly. Generator testing quarterly for sites with backup power.

### Corrective Maintenance

Response based on site tier. Tier 1 sites: 4-hour response, 8-hour repair. Tier 2 sites: 8-hour response, 24-hour repair. Tier 3 sites: 24-hour response, 48-hour repair.

## Troubleshooting Checklist

### No Service from Site

Verify power supply is active. Check backhaul connectivity. Verify base station software is running. Check for alarms on management system. Verify antenna connections. Test with portable equipment if available.

### Intermittent Service

Check for interference sources near the site. Verify antenna alignment and physical condition. Check for loose connections. Review error logs for patterns. Monitor during different times of day.

### Capacity Issues

Review traffic patterns and growth trends. Identify peak usage hours. Check for failed or degraded carriers. Consider adding carriers or upgrading to higher capacity hardware.
