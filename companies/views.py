from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from leads.models import Company
from leads.forms import CompanyForm


def company_list(request):
    """View to list all companies"""
    companies = Company.objects.all().order_by('-company_name')
    
    # Estadísticas
    total_companies = companies.count()
    with_linkedin = companies.exclude(linkedin__isnull=True).exclude(linkedin='').count()
    
    context = {
        'companies': companies,
        'total_companies': total_companies,
        'with_linkedin': with_linkedin,
    }
    return render(request, 'companies/company_list.html', context)


def company_detail(request, pk):
    """View to see company details (read-only)"""
    company = get_object_or_404(Company, domain=pk)
    return render(request, 'companies/company_detail.html', {'company': company})


def company_create(request):
    """View to create a new company"""
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Company created successfully.')
            return redirect('companies:company_list')
    else:
        form = CompanyForm()
    return render(request, 'companies/company_form.html', {'form': form, 'title': 'Create Company'})


def company_update(request, pk):
    """View to edit a company"""
    company = get_object_or_404(Company, domain=pk)
    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, 'Company updated successfully.')
            return redirect('companies:company_list')
    else:
        form = CompanyForm(instance=company)
    return render(request, 'companies/company_form.html', {'form': form, 'title': 'Edit Company'})


def company_delete(request, pk):
    """View to delete a company"""
    company = get_object_or_404(Company, domain=pk)
    if request.method == 'POST':
        company_name = company.company_name
        company.delete()
        messages.success(request, f'Company "{company_name}" deleted successfully.')
        return redirect('companies:company_list')
    return render(request, 'companies/company_confirm_delete.html', {'company': company})
