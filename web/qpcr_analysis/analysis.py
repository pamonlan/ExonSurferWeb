"""
ΔΔCt analysis logic — no R dependency.
Replicates the core of the `pcr` R package: efficiency-corrected ΔΔCt
with t-test p-values and standard error for bar-plot error bars.
"""

import pandas as pd
import numpy as np
from scipy import stats

def _stars(pvalue: float) -> str:
    """Helper function to assign significance stars."""
    if pvalue < 0.001: return '***'
    elif pvalue < 0.01: return '**'
    elif pvalue < 0.05: return '*'
    else: return 'ns'

def average_technical_replicates(
    df: pd.DataFrame,
    rep_col: str,
    group_col: str,
    ct_cols: list[str],
    extra_groupby: list[str] = None,   # e.g. ["Day"] if present
) -> pd.DataFrame:
    """
    Collapse technical replicates → one row per biological replicate.
    Groups by [rep_col, group_col] + extra_groupby, averages all ct_cols.
    """
    groupby_cols = [rep_col, group_col] + (extra_groupby or [])
    # Keep only relevant columns
    cols_to_keep = groupby_cols + ct_cols
    df_sub = df[cols_to_keep].copy()
    return df_sub.groupby(groupby_cols, as_index=False)[ct_cols].mean()

    
def delta_delta_ct(
    df: pd.DataFrame,
    genes: list[str],
    ref_gene: str,
    ref_group: str,
    group_col: str,
    efficiency: float = 1.0,  # 1.0 = 100% efficiency
) -> pd.DataFrame:
    """
    Calculates relative gene expression using the ΔΔCt method.
    Statistics and errors are calculated on the log2 (Ct) scale as per Livak & Schmittgen (2001).
    """
    results = []
    
    ref_mask = df[group_col] == ref_group

    for gene in genes:
        # 1. Calculate ΔCt per sample (assumes paired measurements in same row)
        dct = df[gene] - df[ref_gene]
        
        # 2. Get reference group ΔCt values and mean
        ref_dct = dct[ref_mask]
        ref_mean_dct = ref_dct.mean()
        
        for group, grp_df in df.groupby(group_col):
            # ΔCt values for the current group
            grp_dct = dct[grp_df.index]
            
            # 3. Calculate mean ΔΔCt
            grp_mean_dct = grp_dct.mean()
            mean_ddct = grp_mean_dct - ref_mean_dct
            
            # 4. Calculate error on the ΔCt level (Standard Deviation)
            # You can change to SEM by dividing by np.sqrt(len(grp_dct)) if preferred
            error = grp_dct.std() if len(grp_dct) > 1 else 0.0
            
            # 5. Transform to Relative Expression (Fold Change)
            base = (1 + efficiency)
            expr = base ** (-mean_ddct)
            
            # 6. Calculate Asymmetric Error Bounds
            # Note: Adding error to ΔΔCt makes the value smaller, subtracting makes it larger
            lower = base ** -(mean_ddct + error)
            upper = base ** -(mean_ddct - error)
            
            # 7. Perform t-test on ΔCt values, NOT on the fold changes
            if group == ref_group or len(grp_dct) < 2 or len(ref_dct) < 2:
                pvalue = 1.0
            else:
                _, pvalue = stats.ttest_ind(grp_dct, ref_dct, equal_var=False)
                if pd.isna(pvalue):
                    pvalue = 1.0

            results.append(
                 {
                    "gene": gene,
                    "group": group,
                    "mean_expr": float(expr),
                    "se_expr": float(error),        # SD on ΔCt (log2) scale
                    "lower": float(lower),          # 2^-(ΔΔCt + SD)
                    "upper": float(upper),          # 2^-(ΔΔCt - SD)
                    "pvalue": float(pvalue),
                    "stars": _stars(pvalue),
                    "n": int(len(grp_dct)),
                }
            )

    return pd.DataFrame(results)
 
 
def build_plotly_figure(
    results: pd.DataFrame,
    gene_order: list[str],
    group_order: list[str],
    color_map: dict[str, str],
) -> dict:
    """
    Returns a Plotly figure as a JSON-serialisable dict.
    One subplot per gene, grouped bars with error bars.
    Uses plotly.graph_objects for fine control.
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
 
    n_genes = len(gene_order)
    fig = make_subplots(
        rows=1,
        cols=n_genes,
        shared_yaxes=False,
        subplot_titles=gene_order,
    )
 
    shown_in_legend = set()
 
    for col_idx, gene in enumerate(gene_order, start=1):
        gene_df = results[results["gene"] == gene]
        # respect group_order
        gene_df = (
            gene_df.set_index("group")
            .reindex(group_order)
            .reset_index()
        )
 
        for _, row in gene_df.iterrows():
            group = row["group"]
            show_legend = group not in shown_in_legend
            shown_in_legend.add(group)
 
            err_plus = max(0.0, float(row["upper"]) - float(row["mean_expr"]))
            err_minus = max(0.0, float(row["mean_expr"]) - float(row["lower"]))

            fig.add_trace(
                go.Bar(
                    name=group,
                    x=[group],
                    y=[row["mean_expr"]],
                    error_y=dict(
                        type="data",
                        symmetric=False,
                        array=[err_plus],
                        arrayminus=[err_minus],
                        visible=True,
                    ),
                    marker_color=color_map.get(group, "#999999"),
                    showlegend=show_legend,
                    legendgroup=group,
                    text=row["stars"],
                    textposition="outside",
                    hovertemplate=(
                        f"<b>{gene}</b> — {group}<br>"
                        f"Fold change: %{{y:.3f}}<br>"
                        f"Range (±SD ΔCt): [{row['lower']:.3f}, {row['upper']:.3f}]<br>"
                        f"SD (ΔCt): {row['se_expr']:.3f}<br>"
                        f"p: {row['pvalue']:.4f} {row['stars']}"
                        "<extra></extra>"
                    ),
                ),
                row=1,
                col=col_idx,
            )
 
        fig.update_xaxes(showticklabels=False, row=1, col=col_idx)
 
    fig.update_layout(
        barmode="group",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Arial, sans-serif", size=13),
        legend=dict(title="Group"),
        yaxis_title="Relative Expression (2^-ΔΔCt)",
        margin=dict(t=60, b=40, l=60, r=20),
        height=420,
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="#e0e0e0",
        zeroline=True,
        zerolinecolor="#aaa",
    )
 
    return fig.to_dict()