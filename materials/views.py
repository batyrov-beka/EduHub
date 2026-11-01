from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Material


def material_list(request):
    materials = Material.objects.all().order_by('-created_at')
    q = request.GET.get('q', '').strip()
    if q:
        materials = materials.filter(Q(title__icontains=q) | Q(short_description__icontains=q) | Q(content__icontains=q))
    return render(request, 'materials/material_list.html', {'materials': materials, 'q': q})


def material_detail(request, slug):
    material = get_object_or_404(Material, slug=slug)
    others = Material.objects.exclude(pk=material.pk).order_by('-created_at')[:3]
    return render(request, 'materials/material_detail.html', {'material': material, 'others': others})
