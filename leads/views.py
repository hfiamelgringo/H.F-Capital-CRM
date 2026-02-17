from .mailchimp_utils import add_lead_to_mailchimp
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Avg
from .models import Lead, Company, LeadTag
from .forms import LeadForm, CompanyForm
from .enrichment import enrich_lead
import os


def lead_list(request):
    """View to list all leads"""
    leads = Lead.objects.select_related('company').prefetch_related('tags').all()
    search_query = request.GET.get('search', '').strip()
    company_domain = request.GET.get('company', '').strip()
    
    # Filter by company domain if provided
    if company_domain:
        leads = leads.filter(company__domain=company_domain)
    
    # Filter by search query if provided
    if search_query:
        leads = leads.filter(
            Q(pdl_first_name__icontains=search_query)
            | Q(pdl_last_name__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(company__company_name__icontains=search_query)
            | Q(company__domain__icontains=search_query)
            | Q(tags__name__icontains=search_query)
        ).distinct()
    
    avg_score = leads.aggregate(avg=Avg('lead_score'))['avg']
    if avg_score is not None:
        avg_score = round(avg_score, 1)
    else:
        avg_score = '--'
    
    all_tags = LeadTag.objects.all().order_by('name')
    filter_company = None
    if company_domain:
        filter_company = Company.objects.filter(domain=company_domain).first()

    return render(request, 'leads/lead_list.html', {
        'leads': leads,
        'all_tags': all_tags,
        'search_query': search_query,
        'avg_score': avg_score,
        'filter_company': filter_company,
    })


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


from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect
def send_to_mailchimp(request):
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_leads')
        if not selected_ids:
            messages.error(request, 'No leads selected.')
            return redirect('leads:lead_list')
        from .models import Lead
        leads = Lead.objects.filter(pk__in=selected_ids)
        success, failed = 0, 0
        for lead in leads:
            # Push any existing CRM tags as Mailchimp audience tags too
            tag_names = list(lead.tags.values_list('name', flat=True))
            result = add_lead_to_mailchimp(
                lead.email,
                getattr(lead, 'pdl_first_name', ''),
                getattr(lead, 'pdl_last_name', ''),
                tag_names=tag_names,
            )
            if 'error' in result:
                failed += 1
            else:
                success += 1
        if success:
            messages.success(request, f'{success} leads sent to Mailchimp.')
        if failed:
            messages.error(request, f'{failed} leads failed to send.')
        return redirect('leads:lead_list')
    return redirect('leads:lead_list')


def bulk_apply_tag(request):
    if request.method != 'POST':
        return redirect('leads:lead_list')

    selected_ids = request.POST.getlist('selected_leads')
    tag_name = (request.POST.get('tag_name') or '').strip()

    if not selected_ids:
        messages.error(request, 'No leads selected.')
        return redirect('leads:lead_list')

    if not tag_name:
        messages.error(request, 'Tag name is required.')
        return redirect('leads:lead_list')

    tag, _ = LeadTag.objects.get_or_create(name=tag_name.strip().lower())
    leads = Lead.objects.filter(pk__in=selected_ids)

    updated = 0
    for lead in leads:
        lead.tags.add(tag)
        updated += 1

    messages.success(request, f'Applied tag "{tag.name}" to {updated} lead(s).')
    return redirect('leads:lead_list')


def send_tag_to_mailchimp(request):
    if request.method != 'POST':
        return redirect('leads:lead_list')

    tag_id = request.POST.get('tag_id')
    if not tag_id:
        messages.error(request, 'Please choose a tag.')
        return redirect('leads:lead_list')

    tag = get_object_or_404(LeadTag, pk=tag_id)
    leads = Lead.objects.filter(tags=tag)

    if not leads.exists():
        messages.info(request, f'No leads found with tag "{tag.name}".')
        return redirect('leads:lead_list')

    success, failed = 0, 0
    for lead in leads:
        result = add_lead_to_mailchimp(
            lead.email,
            getattr(lead, 'pdl_first_name', ''),
            getattr(lead, 'pdl_last_name', ''),
            tag_names=[tag.name],
        )
        if 'error' in result:
            failed += 1
        else:
            success += 1

    if success:
        messages.success(request, f'{success} tagged lead(s) sent to Mailchimp (tag: {tag.name}).')
    if failed:
        messages.error(request, f'{failed} tagged lead(s) failed to send to Mailchimp.')

    return redirect('leads:lead_list')


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


def lead_enrich(request):
    """Enrich leads using AI with optional re-enrichment."""
    enable_enrichment = os.getenv("GENAI_API_KEY") and os.getenv("OPENAI_API_KEY")
    if not enable_enrichment:
        messages.error(request, 'AI enrichment is disabled. Add GENAI_API_KEY and OPENAI_API_KEY to keys.env to enable.')
        return redirect('leads:lead_list')

    mode = request.GET.get('mode', 'empty')
    overwrite = mode == 'all'

    leads = Lead.objects.select_related('company').all()
    if not overwrite:
        leads = leads.filter(
            Q(pdl_first_name__isnull=True) | Q(pdl_first_name='') |
            Q(pdl_last_name__isnull=True) | Q(pdl_last_name='') |
            Q(pdl_job_title__isnull=True) | Q(pdl_job_title='') |
            Q(pdl_linkedin_url__isnull=True) | Q(pdl_linkedin_url='')
        )

    total = leads.count()
    if total == 0:
        messages.info(request, 'No leads need enrichment.')
        return redirect('leads:lead_list')

    enriched = 0
    skipped = 0
    errors = 0

    for lead in leads:
        try:
            result = enrich_lead(lead, verbose=False, overwrite=overwrite)
            if result and result.get('skipped'):
                skipped += 1
            elif result:
                enriched += 1
            else:
                errors += 1
        except Exception:
            errors += 1
            continue

    msg = f'Lead enrichment completed. Enriched {enriched} lead(s).'
    if skipped:
        msg += f' Skipped {skipped}.'
    if errors:
        msg += f' {errors} error(s) occurred.'
    messages.success(request, msg)

    return redirect('leads:lead_list')
