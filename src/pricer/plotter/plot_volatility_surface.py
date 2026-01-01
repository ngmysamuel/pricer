# --- plot.py ---
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import griddata


def create_volatility_surface(calls_data):
    # 1. Extract scattered data points directly
    # not using pivot_table here to avoid dropping sparse data
    x = calls_data["days_to_expiry"]
    y = calls_data["strike_price"]
    z = calls_data["calculated_iv"]

    # 2. Define a regular grid to interpolate onto
    # Adjust '50' to change resolution (higher = smoother but slower)
    xi = np.linspace(x.min(), x.max(), 50)
    yi = np.linspace(y.min(), y.max(), 50)
    X, Y = np.meshgrid(xi, yi)

    # 3. Interpolate the scattered data onto the grid
    # 'cubic' looks smoother, 'linear' is more robust to outliers
    Z = griddata((x, y), z, (X, Y), method='cubic')

    np.savetxt('implied_vol.csv', Z, delimiter=',')

    return X, Y, Z

def find_vol_arbitrage(Z, threshold=0.05):
    """
    Finds points where the gradient magnitude exceeds the threshold.
    """
    # np.gradient returns a tuple: (gradient_along_y, gradient_along_x)
    grad_y, grad_x = np.gradient(Z)
    
    # Calculate magnitude of the gradient vector: sqrt(dx^2 + dy^2)
    grad_magnitude = np.sqrt(grad_x**2 + grad_y**2)
    
    # Create a boolean mask where anomalies exist
    # We use nan_to_num to treat NaNs (from interpolation edges) as 0 to avoid errors
    mask = np.nan_to_num(grad_magnitude) > threshold
    
    return mask

def plot_volatility_surface(X, Y, Z, anomaly_mask=None):
    # Create interactive 3D plot with Plotly
    fig = go.Figure(data=[go.Surface(
        x=X, 
        y=Y, 
        z=Z,
        colorscale='Viridis',
        colorbar_title='Implied Volatility',
        name="Vol Surface"
    )])

    if anomaly_mask is not None and np.any(anomaly_mask):
        # Extract the X, Y, Z coordinates where the mask is True
        anom_x = X[anomaly_mask]
        anom_y = Y[anomaly_mask]
        anom_z = Z[anomaly_mask]

        fig.add_trace(go.Scatter3d(
            x=anom_x,
            y=anom_y,
            z=anom_z,
            mode='markers',
            marker=dict(
                size=10,
                color='red',    # Make anomalies bright red
                symbol='cross', # Distinct shape
                line=dict(width=5, color='black') # Outline for visibility
            ),
            name='High Gradient (Anomaly)'
        ))

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