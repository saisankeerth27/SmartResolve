# Network Technology Overview

## LTE (4G)

Long Term Evolution provides high-speed wireless broadband. Supports peak speeds up to 150 Mbps downlink and 50 Mbps uplink. Used for mobile broadband, IoT, and voice over LTE (VoLTE). Coverage is provided by macro and small cell sites across all regions.

### LTE Coverage Bands

Band 2 (1900 MHz): Primary coverage band for urban and suburban areas. Good balance of coverage and capacity.

Band 4 (1700/2100 MHz): AWS band used for capacity in urban areas. Higher capacity but shorter range.

Band 12 (700 MHz): Low-band for rural coverage and building penetration. Longer range but lower capacity.

Band 66 (1700/2100 MHz): Extended AWS band for additional capacity.

## 5G NR

New Radio provides next-generation wireless connectivity. Supports peak speeds up to 10 Gbps downlink. Used for enhanced mobile broadband, ultra-reliable low-latency communications, and massive machine-type communications.

### 5G Deployment Modes

#### Non-Standalone (NSA)

5G NR deployed on top of existing LTE core. Provides increased capacity and speed without new core infrastructure. Uses EN-DC (EUTRA-NR Dual Connectivity) for device connection.

#### Standalone (SA)

Full 5G NR with 5G core. Enables all 5G features including network slicing and ultra-low latency. Deployed in select urban areas.

### 5G Frequency Bands

n71 (600 MHz): Low-band 5G for wide coverage. Good building penetration but limited capacity.

n41 (2500 MHz): Mid-band 5G for balanced coverage and capacity. Primary 5G band for urban areas.

n260 (39 GHz): mmWave 5G for ultra-high capacity in dense areas. Limited range and poor building penetration.

## 3G (Legacy)

UMTS/HSPA technology providing basic mobile broadband. Supports peak speeds up to 42 Mbps downlink. Being phased out in favor of 4G and 5G. Still operational in some rural areas for backward compatibility.

## Network Architecture

### Radio Access Network (RAN)

Base stations (eNodeB for LTE, gNodeB for 5G) provide wireless access. Connected to the core network via backhaul. Includes baseband processing, radio transmission, and antenna systems.

### Core Network

Centralized network functions including mobility management, session management, and subscriber management. Evolved Packet Core (EPC) for LTE. 5G Core (5GC) for 5G SA.

### Transport Network

Interconnects RAN and core network. Includes backhaul (site to aggregation), midhaul (aggregation to core), and fronthaul (baseband to radio). Fiber, microwave, and Ethernet are primary transport technologies.

## Voice Services

### VoLTE (Voice over LTE)

IP-based voice service on LTE. Provides HD voice quality. Supports simultaneous voice and data. Required for voice service as 3G is retired.

### VoNR (Voice over New Radio)

IP-based voice service on 5G SA. Provides even lower latency and higher quality. Used in 5G standalone deployments.

### VoWiFi (Voice over Wi-Fi)

Voice service over Wi-Fi networks. Used for indoor coverage and areas with poor cellular coverage. Seamless handoff between Wi-Fi and cellular.

## IoT Connectivity

### NB-IoT (Narrowband IoT)

Low-power wide-area technology for IoT devices. Supports deep indoor coverage. Used for smart metering, asset tracking, and environmental monitoring.

### LTE-M (Cat-M1)

Medium-power IoT technology. Supports mobility and handover. Used for connected vehicles, wearable devices, and industrial IoT.
