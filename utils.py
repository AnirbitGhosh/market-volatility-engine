import pandas as pd
from typing import List, Dict

def detect_spikes(vol: pd.Series, threshold: float=2.5) -> List[Dict]:
    if vol.empty:
        return []
    
    mean = vol.mean()
    std = vol.std()
    spikes = vol[vol > mean + threshold * std]

    if spikes.empty:
        return []
    
    top_spikes = spikes.sort_values(ascending=False).head(10)

    annotations = []
    y_positions = set()

    for idx, val  in top_spikes.items():
        y_pos = val
        while any(abs(y_pos - existing_y) < (0.1 * vol.max()) for existing_y in y_positions):
            y_pos *= 0.95

        y_positions.add(y_pos)

        annotations.append(dict(
            x=idx, 
            y=y_pos,
            text = f"Spike: {val:.1f}σ",
            showarrow=True,
            arrowhead=1,
            ax=0,
            ay=30,
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='rgba(0,0,0,0.5)',
            borderwidth=1,
            font=dict(size=12, color='black')
        ))

        return annotations