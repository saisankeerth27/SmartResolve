# Spectrum Management and Allocation

## Overview

This document describes how SmartConnect manages and allocates wireless spectrum across its network. Spectrum is a finite resource that must be carefully managed to ensure optimal network performance.

## Licensed Spectrum Holdings

### Low-Band Spectrum (600-900 MHz)

Provides wide area coverage and excellent building penetration. Used primarily for rural coverage and indoor penetration in urban areas. Includes 600 MHz (n71/71), 700 MHz (B12), and 850 MHz bands. These bands carry voice and low-bandwidth data services.

### Mid-Band Spectrum (1.7-3.7 GHz)

Provides balanced coverage and capacity. Primary bands for urban and suburban capacity. Includes 1700/2100 MHz (B4/B66), 1900 MHz (B2), and 2500 MHz (B41/n41) bands. These bands carry the majority of mobile broadband traffic.

### High-Band Spectrum (24-39 GHz)

Provides ultra-high capacity in dense areas. Limited range and building penetration. Used for hotspots, venues, and dense urban cores. Includes 28 GHz and 39 GHz (n260) bands. These bands support peak data rates.

## Spectrum Allocation Rules

### Voice Priority

Voice services always receive priority allocation during congestion. VoLTE and VoNR calls are allocated dedicated bearers with guaranteed bit rates. Voice traffic cannot be deprioritized or throttled.

### Data Traffic Management

Best-effort data traffic is managed using quality of service (QoS) classes. Streaming video is allocated medium priority. Web browsing is allocated standard priority. File downloads and backups are allocated low priority.

### IoT Allocation

IoT devices are allocated narrow bandwidth channels. NB-IoT uses 180 kHz channels. LTE-M uses 1.4 MHz channels. These allocations are isolated from consumer traffic.

## Interference Management

### External Interference

Caused by non-network sources such as illegal transmitters, faulty electronics, or adjacent systems. Detected through spectrum monitoring and customer reports. Resolution involves coordination with regulatory authorities.

### Internal Interference

Caused by network elements such as adjacent cells or overlapping frequencies. Managed through frequency planning and power control. Coordinated multipoint (CoMP) techniques reduce inter-cell interference.

## Carrier Aggregation

Combines multiple frequency carriers to increase bandwidth. Up to 5 carriers can be aggregated in LTE. Up to 16 carriers in 5G NR. Carrier aggregation is dynamically adjusted based on network load and device capabilities.

## Dynamic Spectrum Sharing

Allows simultaneous operation of LTE and 5G NR on the same frequency band. Resources are allocated based on demand. Enables smooth transition from 4G to 5G without requiring separate spectrum allocations.
