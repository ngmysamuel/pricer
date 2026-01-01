import plotly.graph_objects as go
import numpy as np


def plot_traces(
    paths: np.array,
    mc_price: float,
    mc_strike: float,
    mc_iter: int,
    selected_ticker: str,
):
    fig_mc = go.Figure()
    days_axis = list(range(paths.shape[1]))

    # Limit paths for performance
    display_limit = 200
    subset_paths = paths[:display_limit]

    for i in range(len(subset_paths)):
        fig_mc.add_trace(
            go.Scatter(
                x=days_axis,
                y=np.concatenate((np.array([mc_price]), subset_paths[i])),
                mode="lines",
                line=dict(width=1, color="rgba(0, 200, 255, 0.1)"),
                showlegend=False,
                hoverinfo="skip",
            )
        )

    # Average Path
    avg_path = np.mean(paths, axis=0)
    fig_mc.add_trace(
        go.Scatter(
            x=days_axis,
            y=avg_path,
            mode="lines",
            line=dict(width=3, color="#FF4B4B"),
            name="Average Path",
        )
    )

    # Strike Line
    fig_mc.add_hline(
        y=mc_strike, line_dash="dash", line_color="orange", annotation_text="Strike"
    )

    fig_mc.update_layout(
        title=f"Monte Carlo Simulation - {selected_ticker} - {mc_iter} Paths (showing 200)",
        xaxis_title="Days",
        yaxis_title="Price",
        template="plotly_dark",
        height=600,
    )

    return fig_mc
