import numpy as np
import scipy.interpolate as interpolate
import seaborn as sns
import matplotlib.pyplot as plt

def create_volatility_surface(calls_data):
    surface = (
        calls_data[["days_to_expiry", "strike_price", "calculated_iv"]]
        .pivot_table(
            values="calculated_iv", index="strike_price", columns="days_to_expiry"
        )
        .dropna()
    )

    # Prepare interpolation data
    x = surface.columns.values
    y = surface.index.values
    X, Y = np.meshgrid(x, y)
    Z = surface.values

    # Create interpolation points
    x_new = np.linspace(x.min(), x.max(), 100)
    y_new = np.linspace(y.min(), y.max(), 100)
    X_new, Y_new = np.meshgrid(x_new, y_new)

    # Perform interpolation
    spline = interpolate.SmoothBivariateSpline(
        X.flatten(), Y.flatten(), Z.flatten(), s=0.1
    )
    Z_smooth = spline(x_new, y_new)

    return X_new, Y_new, Z_smooth


def plot_volatility_surface(X, Y, Z):
    plt.style.use("default")
    sns.set_style("whitegrid", {"axes.grid": False})

    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection="3d")

    ax.plot_surface(
        X, Y, Z, cmap="viridis", alpha=0.9, linewidth=0, antialiased=True
    )

    ax.set_xlabel("Days to Expiration")
    ax.set_ylabel("Strike Price")
    ax.set_zlabel("Implied Volatility")
    ax.set_title("AAPL Volatility Surface")
    ax.view_init(elev=20, azim=45)

    plt.tight_layout()
    # plt.show()
    return plt