from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Lead, Company
from .forms import LeadForm, CompanyForm


def lead_list(request):
    """View to list all leads"""
    leads = Lead.objects.select_related('company').all()
    return render(request, 'leads/lead_list.html', {'leads': leads})


def lead_detail(request, pk):
    """View to see lead details (read-only)"""
    lead = get_object_or_404(Lead, pk=pk)
    return render(request, 'leads/lead_detail.html', {'lead': lead})


def lead_create(request):
    """View to create a new lead"""
    if request.method == 'POST':
        form = LeadForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lead created successfully.')
            return redirect('leads:lead_list')
    else:
        form = LeadForm()
    return render(request, 'leads/lead_form.html', {'form': form, 'title': 'Create Lead'})


def lead_update(request, pk):
    """View to update an existing lead"""
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == 'POST':
        form = LeadForm(request.POST, instance=lead)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lead updated successfully.')
            return redirect('leads:lead_list')
    else:
        form = LeadForm(instance=lead)
    return render(request, 'leads/lead_form.html', {'form': form, 'title': 'Edit Lead'})


def lead_delete(request, pk):
    """View to delete a lead"""
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == 'POST':
        lead.delete()
        messages.success(request, 'Lead deleted successfully.')
        return redirect('leads:lead_list')
    return render(request, 'leads/lead_confirm_delete.html', {'lead': lead})


def company_create(request):
    """View to create a new company"""
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Company created successfully.')
            return redirect('leads:lead_create')
    else:
        form = CompanyForm()
    return render(request, 'leads/company_form.html', {'form': form, 'title': 'Create Company'})


def clear_leads(request):
    """View to clear all leads and companies"""
    if request.method == 'POST':
        leads_count = Lead.objects.count()
        companies_count = Company.objects.count()
        
        Lead.objects.all().delete()
        Company.objects.all().delete()
        
        messages.success(request, f'Successfully deleted {leads_count} leads and {companies_count} companies.')
        return redirect('leads:lead_list')
    
    return redirect('leads:lead_list')
