from django.shortcuts import render, get_object_or_404
from .models import Material

def material_list(request):
    materials = Material.objects.all().order_by('-created_at')
    return render(request, 'materials/material_list.html', {'materials': materials})

def material_detail(request, slug):
    material = get_object_or_404(Material, slug=slug)
    return render(request, 'materials/material_detail.html', {'material': material})

