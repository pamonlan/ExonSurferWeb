import io
import json
 
import pandas as pd
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST, require_GET
 
from .analysis import average_technical_replicates, build_plotly_figure, delta_delta_ct 
 
@ensure_csrf_cookie
def index(request):
    """Main page — empty form, no file loaded yet."""
    return render(request, "qpcr_analysis/qpcr_result.html")


@require_GET
def download_example(request):
    """Download a ready-to-run example Excel file with realistic Ct values."""
    rows = [
        # Group, BioRep, GAPDH (housekeeping), IL6 (up), TNF (up), CD206 (down)
        ("Control",        1, 18.42, 28.10, 26.55, 23.10),
        ("Control",        1, 18.51, 28.25, 26.40, 23.22),
        ("Control",        2, 18.60, 28.45, 26.80, 23.35),
        ("Control",        2, 18.55, 28.32, 26.72, 23.28),
        ("Control",        3, 18.38, 28.05, 26.48, 23.02),
        ("Control",        3, 18.44, 28.18, 26.52, 23.15),
        ("Treatment_Low",  1, 18.50, 26.15, 25.40, 24.20),
        ("Treatment_Low",  1, 18.46, 26.08, 25.52, 24.12),
        ("Treatment_Low",  2, 18.58, 26.35, 25.65, 24.45),
        ("Treatment_Low",  2, 18.62, 26.42, 25.58, 24.38),
        ("Treatment_Low",  3, 18.40, 26.02, 25.32, 24.08),
        ("Treatment_Low",  3, 18.45, 26.12, 25.44, 24.18),
        ("Treatment_High", 1, 18.48, 24.10, 23.85, 25.30),
        ("Treatment_High", 1, 18.52, 24.22, 23.92, 25.22),
        ("Treatment_High", 2, 18.61, 24.38, 24.10, 25.55),
        ("Treatment_High", 2, 18.56, 24.28, 24.02, 25.48),
        ("Treatment_High", 3, 18.41, 23.98, 23.78, 25.18),
        ("Treatment_High", 3, 18.47, 24.08, 23.88, 25.28),
    ]
    df = pd.DataFrame(rows, columns=["Group", "BioRep", "GAPDH", "IL6", "TNF", "CD206"])
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Ct_Values")
    buf.seek(0)
    response = HttpResponse(
        buf.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="exonsurfer_qpcr_example.xlsx"'
    return response
 
 
@require_POST
def parse_excel(request):
    """
    Step 1 — called via AJAX after file upload.
    Returns sheet names, numeric columns, group columns, and group levels
    so the frontend can build the configuration form dynamically.
    """
    if "file" not in request.FILES:
        return JsonResponse({"error": "No file provided"}, status=400)
 
    xl_file = request.FILES["file"]
 
    try:
        xl = pd.ExcelFile(xl_file)
    except Exception as exc:
        return JsonResponse({"error": f"Cannot read file: {exc}"}, status=400)
 
    sheet = request.POST.get("sheet", xl.sheet_names[0])
 
    try:
        df = xl.parse(sheet)
    except Exception as exc:
        return JsonResponse({"error": f"Cannot parse sheet: {exc}"}, status=400)
 
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    group_cols = [
        c for c in df.columns
        if c not in numeric_cols and df[c].nunique() <= 30
    ]

    rep_col_candidates = [
        c for c in numeric_cols
        if df[c].nunique() <= 10 and df[c].dropna().apply(lambda x: float(x).is_integer()).all()
    ]

    ct_cols = [c for c in numeric_cols if c not in rep_col_candidates]

    default_group_col = group_cols[0] if group_cols else None
    groups = df[default_group_col].dropna().unique().tolist() if default_group_col else []

    return JsonResponse({
        "sheets": xl.sheet_names,
        "numeric_cols": ct_cols,
        "group_cols": group_cols,
        "rep_col_candidates": rep_col_candidates,
        "default_group_col": default_group_col,
        "groups": groups,
    })
 
 
@require_POST
def get_groups(request):
    """
    Step 1b — called when user changes sheet OR group column.
    Returns updated group levels for that column.
    """
    if "file" not in request.FILES:
        return JsonResponse({"error": "No file provided"}, status=400)
 
    xl_file = request.FILES["file"]
    sheet = request.POST.get("sheet")
    group_col = request.POST.get("group_col")
 
    try:
        df = pd.read_excel(xl_file, sheet_name=sheet)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=400)
 
    if group_col not in df.columns:
        return JsonResponse({"error": "Column not found"}, status=400)
 
    groups = df[group_col].dropna().unique().tolist()
    return JsonResponse({"groups": groups})
 
 
@require_POST
def run_analysis(request):
    """
    Step 2 — called on form submit.
    Runs ΔΔCt and returns a Plotly figure dict.
    """
    if "file" not in request.FILES:
        return JsonResponse({"error": "No file provided"}, status=400)
 
    xl_file = request.FILES["file"]
    sheet = request.POST.get("sheet")
    group_col = request.POST.get("group_col")
    ref_gene = request.POST.get("ref_gene")
    ref_group = request.POST.get("ref_group")
    genes = request.POST.getlist("genes")  # target genes (excludes ref_gene)
    group_order = request.POST.getlist("group_order")  # ordered list from drag UI
 
    # color_map comes as JSON string: {"VEH CTRL": "#808080", ...}
    try:
        color_map = json.loads(request.POST.get("color_map", "{}"))
    except json.JSONDecodeError:
        color_map = {}
 
    if not genes:
        return JsonResponse({"error": "No target genes selected"}, status=400)
    if not ref_gene:
        return JsonResponse({"error": "No housekeeping gene selected"}, status=400)
    if not ref_group:
        return JsonResponse({"error": "No reference group selected"}, status=400)
 
    try:
        df = pd.read_excel(xl_file, sheet_name=sheet)
    except Exception as exc:
        return JsonResponse({"error": f"Cannot read file: {exc}"}, status=400)
 
    # Validate columns exist
    missing = [c for c in genes + [ref_gene] if c not in df.columns]
    if missing:
        return JsonResponse(
            {"error": f"Columns not found in sheet: {missing}"}, status=400
        )
 
    if group_col not in df.columns:
        return JsonResponse({"error": f"Group column '{group_col}' not found"}, status=400)
 
    # Fallback group order
    if not group_order:
        group_order = df[group_col].dropna().unique().tolist()
 
    try:
        rep_col   = request.POST.get("rep_col", "")      # vacío si no hay bio reps
        extra_grp = request.POST.getlist("extra_groupby") # e.g. ["Day"]

        all_ct_cols = genes + [ref_gene]

        if rep_col and rep_col in df.columns:
            df = average_technical_replicates(
                df,
                rep_col=rep_col,
                group_col=group_col,
                ct_cols=all_ct_cols,
                extra_groupby=[c for c in extra_grp if c in df.columns],
            )
        results = delta_delta_ct(df, genes, ref_gene, ref_group, group_col)
        fig_dict = build_plotly_figure(results, genes, group_order, color_map)
    except Exception as exc:
        return JsonResponse({"error": f"Analysis failed: {exc}"}, status=500)
 
    # Also return a summary table for display
    table_data = results.to_dict(orient="records")
 
    return JsonResponse({"plot": fig_dict, "table": table_data})
 