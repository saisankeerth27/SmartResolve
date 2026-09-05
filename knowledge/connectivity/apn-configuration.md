# APN Configuration Guide

## What is an APN

Access Point Name (APN) is the gateway between the mobile network and the internet. It determines the network path for all data traffic. Correct APN configuration is essential for mobile data to function.

## Default APN Settings

### SmartConnect Internet APN

Name: SmartConnect Internet  
APN: smartconnect.internet  
Proxy: Not set  
Port: Not set  
Username: Not set  
Password: Not set  
Server: Not set  
MMSC: Not set  
MMS Proxy: Not set  
MMS Port: Not set  
MCC: 310  
MNC: 260  
Authentication type: None  
APN type: default,supl  
APN protocol: IPv4/IPv6  
APN roaming protocol: IPv4

### SmartConnect MMS APN

Name: SmartConnect MMS  
APN: smartconnect.mms  
Proxy: Not set  
Port: Not set  
Username: Not set  
Password: Not set  
Server: Not set  
MMSC: http://mmsc.smartconnect.com  
MMS Proxy: mmsproxy.smartconnect.com  
MMS Port: 8080  
MCC: 310  
MNC: 260  
Authentication type: None  
APN type: mms  
APN protocol: IPv4/IPv6  
APN roaming protocol: IPv4

## Configuration Procedures

### Android Configuration

1. Open Settings.
2. Navigate to Mobile Networks > Access Point Names.
3. Tap the menu icon and select New APN.
4. Enter the APN settings as listed above.
5. Save the new APN.
6. Select the new APN as the active APN.
7. Restart the device.

### iOS Configuration

iOS devices typically configure APN automatically through the carrier settings update. If manual configuration is needed:

1. Open Settings.
2. Navigate to Cellular > Cellular Data Options > Cellular Network.
3. Enter the APN settings under the Cellular Data section.
4. For MMS, enter the MMS settings under the MMS section.
5. Restart the device.

### Automatic Configuration

Most devices will automatically configure APN settings when a SmartConnect SIM is inserted. If data does not work after inserting the SIM, try: removing and reinserting the SIM, toggling airplane mode, or restarting the device. If automatic configuration fails, use manual configuration above.

## Troubleshooting

### Data Not Working After APN Change

Verify the APN settings match the defaults exactly. Check for typos in the APN name or settings. Ensure the APN is selected as active. Restart the device after making changes. If issues persist, reset APN to defaults and reconfigure.

### MMS Not Working

Verify MMS APN is configured correctly. Check that mobile data is enabled. Verify the messaging app has necessary permissions. Check for sufficient storage space on the device. Test MMS by sending a picture message.

### Roaming Data Not Working

Verify roaming is enabled on the device. Check that roaming is enabled on the account. Verify the roaming APN settings. Some devices require manual APN configuration while roaming. Contact support if roaming data still does not work.
