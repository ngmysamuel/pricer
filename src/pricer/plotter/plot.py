# --- plot.py ---
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import griddata

def create_volatility_surface(calls_data):
    # 1. Extract scattered data points directly
    # We do NOT use pivot_table here to avoid dropping sparse data
    x = calls_data["days_to_expiry"]
    y = calls_data["strike_price"]
    z = calls_data["calculated_iv"]

    # 2. Define a regular grid to interpolate onto
    # Adjust '100' to change resolution (higher = smoother but slower)
    xi = np.linspace(x.min(), x.max(), 50)
    yi = np.linspace(y.min(), y.max(), 50)
    X, Y = np.meshgrid(xi, yi)

    # 3. Interpolate the scattered data onto the grid
    # 'cubic' looks smoother, 'linear' is more robust to outliers
    Z = griddata((x, y), z, (X, Y), method='cubic')

    return X, Y, Z

def plot_volatility_surface(X, Y, Z):
    # Create interactive 3D plot with Plotly
    fig = go.Figure(data=[go.Surface(
        x=X, 
        y=Y, 
        z=Z,
        colorscale='Viridis',
        colorbar_title='Implied Volatility'
    )])

    fig.update_layout(
        title='Implied Volatility Surface',
        scene=dict(
            xaxis_title='Days to Expiration',
            yaxis_title='Strike Price',
            zaxis_title='Implied Volatility',
            xaxis=dict(backgroundcolor="rgb(230, 230,230)"),
            yaxis=dict(backgroundcolor="rgb(230, 230,230)"),
            zaxis=dict(backgroundcolor="rgb(230, 230,230)")
        ),
        autosize=False,
        width=800,
        height=800,
        margin=dict(l=65, r=50, b=65, t=90)
    )

    return fig