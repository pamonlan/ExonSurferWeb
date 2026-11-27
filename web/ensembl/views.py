from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from .models import Gene, Transcript, HousekeepingGene
from ensembl.management.species_config import CANONICAL_CHR, SPECIES

def get_genes_for_species(request, species_key):
    if request.GET.get("hk") in ("1", "true", "True"):
        hk_genes = list(
            HousekeepingGene.objects.filter(species=species_key)
            .order_by("rank", "gene_name")
            .values_list(
                "gene_id",
                "gene_name",
                "rank",
                "evidence_tier",
                "sources",
                "citation",
            )
        )
        return JsonResponse(hk_genes, safe=False)

    cfg = SPECIES[species_key]
    filters = {
        "species": species_key,
        "gene_biotype": "protein_coding",
    }
    if not cfg["scaffold_only"]:
        filters["seqname__in"] = CANONICAL_CHR[species_key]

    unique_gene_ids = Transcript.objects.filter(
        species=species_key
    ).values_list('gene_id', flat=True).distinct()

    lGenes = Gene.objects.filter(
        gene_id__in=unique_gene_ids, **filters
    ).values_list("gene_id", "gene_name")

    lGenes = sorted([x for x in lGenes if x[1] != ''], key=lambda x: x[1])
    return JsonResponse(lGenes, safe=False)