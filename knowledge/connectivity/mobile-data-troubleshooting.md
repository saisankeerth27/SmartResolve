# Mobile Data Connectivity Troubleshooting

## Common Symptoms

### No Data Connection

Device shows signal bars but cannot access internet. Web pages fail to load. Applications cannot connect. Speed test shows 0 Mbps or fails entirely.

### Slow Data

Pages load slowly. Video buffers frequently. Applications time out. Speed test shows significantly lower than expected speeds.

### Intermittent Data

Connection drops periodically. Applications disconnect and reconnect. Downloads fail partway through. Web pages partially load.

## Diagnostic Steps

### Step 1: Check Device Status

Verify mobile data is enabled in device settings. Check that airplane mode is off. Confirm SIM card is active and not locked. Verify APN settings are correct.

### Step 2: Check Network Coverage

Check coverage map for the user's location. Verify the site serving the user is operational. Check for active network events in the area. Confirm the user's subscription includes data service.

### Step 3: Run Speed Test

Use the network speed test tool. Record download and upload speeds. Note latency and jitter values. Compare against plan expectations.

### Step 4: Check for Congestion

Review site capacity utilization. Check time of day for peak usage. Look for recent traffic spikes. Verify no maintenance is in progress.

## Resolution Procedures

### APN Configuration Issues

If APN settings are incorrect, guide the user through resetting APN to default. For Android: Settings > Mobile Networks > Access Point Names > Reset to default. For iOS: Settings > Cellular > Cellular Data Options > Reset Settings. After reset, reboot the device.

### SIM Card Issues

If SIM shows as invalid, try reseating the SIM card. If SIM is locked, guide user through PUK code entry. If SIM is damaged, arrange replacement. If SIM is suspended, verify account status.

### Network Registration Issues

If device is not registered on the network, toggle airplane mode on and off. If persistent, manually select network operator. If still unresolved, check for SIM provisioning issues.

### Speed Issues

If speed is low despite good signal, check for background app data usage. Verify no VPN is active. Check for data throttling due to plan limits. Test at different times to rule out congestion.

## Advanced Diagnostics

### Signal Quality Analysis

Reference Signal Received Power (RSRP): Above -80 dBm is excellent, -80 to -90 dBm is good, -90 to -100 dBm is fair, below -100 dBm is poor.

Reference Signal Received Quality (RSRQ): Above -10 dB is excellent, -10 to -15 dB is good, -15 to -20 dB is fair, below -20 dB is poor.

Signal to Interference plus Noise Ratio (SINR): Above 20 dB is excellent, 13-20 dB is good, 0-13 dB is fair, below 0 dB is poor.

### Handover Issues

Check for frequent handovers between cells. Review handover failure rates. Check for ping-pong handovers between overlapping cells. Verify handover parameters are optimized.

## Escalation Criteria

Escalate to Tier 2 support if: issue persists after all standard troubleshooting, device is not compatible with network bands, multiple users in same area report similar issues, or issue requires network-side investigation.
