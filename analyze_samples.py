#!/usr/bin/env python3
"""
Analyze BT50 sample data and visualize acceleration with impact detection.
Shows raw acceleration values and calculates magnitude to understand thresholds.
"""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

# Load the data
df = pd.read_csv('c:\\temp\\samples.csv', names=['id', 'ts_ns', 'vx', 'vy', 'vz', 'temp_raw'])

print(f"Total samples: {len(df)}")
print(f"Time range: {(df.ts_ns.max() - df.ts_ns.min()) / 1e9:.1f} seconds")
print(f"\nData statistics:")
print(df[['vx', 'vy', 'vz']].describe())

# Calculate magnitude (Euclidean distance)
df['magnitude'] = np.sqrt(df['vx']**2 + df['vy']**2 + df['vz']**2)

# Convert timestamp to seconds from start
df['time_sec'] = (df['ts_ns'] - df['ts_ns'].min()) / 1e9

# Find impacts (magnitude > threshold)
THRESHOLD = 150.0
df['is_impact'] = df['magnitude'] > THRESHOLD

print(f"\nImpact threshold: {THRESHOLD}")
print(f"Samples above threshold: {df['is_impact'].sum()}")
print(f"Max magnitude: {df['magnitude'].max():.1f}")

# Show top 20 highest magnitudes
print("\nTop 20 highest magnitude samples:")
top_samples = df.nlargest(20, 'magnitude')[['time_sec', 'vx', 'vy', 'vz', 'magnitude']]
print(top_samples.to_string(index=False))

# Find periods with movement (magnitude > 50)
movement_samples = df[df['magnitude'] > 50]
print(f"\nSamples with movement (mag > 50): {len(movement_samples)}")

# Create strip chart visualization
fig, axes = plt.subplots(5, 1, figsize=(16, 12), sharex=True)

# Plot X, Y, Z acceleration
axes[0].plot(df['time_sec'], df['vx'], 'r-', linewidth=0.5, label='X accel')
axes[0].set_ylabel('X Acceleration (counts)', fontsize=10)
axes[0].grid(True, alpha=0.3)
axes[0].legend()
axes[0].set_title('BT50 Sensor Data - Raw Acceleration Values', fontsize=12, fontweight='bold')

axes[1].plot(df['time_sec'], df['vy'], 'g-', linewidth=0.5, label='Y accel')
axes[1].set_ylabel('Y Acceleration (counts)', fontsize=10)
axes[1].grid(True, alpha=0.3)
axes[1].legend()

axes[2].plot(df['time_sec'], df['vz'], 'b-', linewidth=0.5, label='Z accel')
axes[2].set_ylabel('Z Acceleration (counts)', fontsize=10)
axes[2].grid(True, alpha=0.3)
axes[2].legend()

# Plot magnitude with threshold line
axes[3].plot(df['time_sec'], df['magnitude'], 'k-', linewidth=0.8, label='Magnitude')
axes[3].axhline(y=THRESHOLD, color='r', linestyle='--', linewidth=2, label=f'Threshold ({THRESHOLD})')
# Highlight impacts
impacts = df[df['is_impact']]
if len(impacts) > 0:
    axes[3].scatter(impacts['time_sec'], impacts['magnitude'], color='red', s=50, zorder=5, label='Detected Impacts')
axes[3].set_ylabel('Magnitude (counts)', fontsize=10)
axes[3].grid(True, alpha=0.3)
axes[3].legend()
axes[3].set_ylim(0, max(df['magnitude'].max() * 1.1, THRESHOLD * 1.5))

# Plot temperature for reference
axes[4].plot(df['time_sec'], df['temp_raw'], 'orange', linewidth=0.5, label='Temperature')
axes[4].set_ylabel('Temperature (raw)', fontsize=10)
axes[4].set_xlabel('Time (seconds)', fontsize=10)
axes[4].grid(True, alpha=0.3)
axes[4].legend()

plt.tight_layout()
plt.savefig('c:\\sandbox\\TargetSensor\\LeadVille\\bt50_strip_chart.png', dpi=150, bbox_inches='tight')
print("\n✓ Strip chart saved to: bt50_strip_chart.png")
print("\nOpening chart...")
plt.show()

# Create a zoomed view of the highest activity period
if len(movement_samples) > 0:
    # Find the most active 30-second window
    window_size = 30  # seconds
    max_activity_time = movement_samples['time_sec'].iloc[0]
    
    fig2, axes2 = plt.subplots(4, 1, figsize=(14, 10), sharex=True)
    
    # Filter to active window
    mask = (df['time_sec'] >= max_activity_time - 5) & (df['time_sec'] <= max_activity_time + 10)
    zoom_df = df[mask]
    
    if len(zoom_df) > 0:
        axes2[0].plot(zoom_df['time_sec'], zoom_df['vx'], 'r-', linewidth=1, marker='o', markersize=2, label='X')
        axes2[0].plot(zoom_df['time_sec'], zoom_df['vy'], 'g-', linewidth=1, marker='s', markersize=2, label='Y')
        axes2[0].plot(zoom_df['time_sec'], zoom_df['vz'], 'b-', linewidth=1, marker='^', markersize=2, label='Z')
        axes2[0].set_ylabel('Acceleration (counts)', fontsize=10)
        axes2[0].grid(True, alpha=0.3)
        axes2[0].legend()
        axes2[0].set_title('Zoomed View - Movement Event Detail', fontsize=12, fontweight='bold')
        
        axes2[1].plot(zoom_df['time_sec'], zoom_df['magnitude'], 'k-', linewidth=2, marker='o', markersize=3)
        axes2[1].axhline(y=THRESHOLD, color='r', linestyle='--', linewidth=2, label=f'Threshold ({THRESHOLD})')
        axes2[1].axhline(y=30, color='orange', linestyle=':', linewidth=1.5, label='Onset (30)')
        impacts_zoom = zoom_df[zoom_df['is_impact']]
        if len(impacts_zoom) > 0:
            axes2[1].scatter(impacts_zoom['time_sec'], impacts_zoom['magnitude'], color='red', s=100, zorder=5)
        axes2[1].set_ylabel('Magnitude', fontsize=10)
        axes2[1].grid(True, alpha=0.3)
        axes2[1].legend()
        
        # Show sample rate
        if len(zoom_df) > 1:
            time_diffs = zoom_df['time_sec'].diff().dropna()
            avg_rate = 1.0 / time_diffs.mean() if time_diffs.mean() > 0 else 0
            axes2[2].plot(zoom_df['time_sec'].iloc[1:], 1.0 / time_diffs, 'purple', linewidth=1)
            axes2[2].set_ylabel('Sample Rate (Hz)', fontsize=10)
            axes2[2].set_xlabel('Time (seconds)', fontsize=10)
            axes2[2].grid(True, alpha=0.3)
            axes2[2].set_title(f'Average sample rate: {avg_rate:.1f} Hz', fontsize=9)
        
        # Show the actual calculation for the highest magnitude sample
        max_idx = zoom_df['magnitude'].idxmax()
        max_sample = zoom_df.loc[max_idx]
        calc_text = f"Peak Sample Calculation:\n"
        calc_text += f"Time: {max_sample['time_sec']:.3f}s\n"
        calc_text += f"X={max_sample['vx']:.0f}, Y={max_sample['vy']:.0f}, Z={max_sample['vz']:.0f}\n"
        calc_text += f"Magnitude = √(X² + Y² + Z²)\n"
        calc_text += f"         = √({max_sample['vx']:.0f}² + {max_sample['vy']:.0f}² + {max_sample['vz']:.0f}²)\n"
        calc_text += f"         = √{max_sample['vx']**2 + max_sample['vy']**2 + max_sample['vz']**2:.0f}\n"
        calc_text += f"         = {max_sample['magnitude']:.1f}\n"
        calc_text += f"\nThreshold: {THRESHOLD}\n"
        calc_text += f"Detection: {'✓ IMPACT' if max_sample['magnitude'] > THRESHOLD else '✗ No impact'}"
        
        axes2[3].text(0.05, 0.5, calc_text, transform=axes2[3].transAxes, 
                     fontsize=11, verticalalignment='center', family='monospace',
                     bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        axes2[3].axis('off')
        
        plt.tight_layout()
        plt.savefig('c:\\sandbox\\TargetSensor\\LeadVille\\bt50_zoom_chart.png', dpi=150, bbox_inches='tight')
        print("✓ Zoomed chart saved to: bt50_zoom_chart.png")
        plt.show()
