from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import StreamingHttpResponse
from leads.models import Lead, Company
from leads.enrichment import enrich_company
import csv
import io
import os
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


def home(request):
    """Vista para la página de inicio"""
    return render(request, 'crm/home.html')


def ai_enrichment(request):
    """Vista para enriquecer empresas con IA"""
    if request.method == 'POST':
        # Check if AI enrichment is enabled
        enable_enrichment = os.getenv("GENAI_API_KEY") and os.getenv("OPENAI_API_KEY")
        
        if not enable_enrichment:
            messages.error(request, 'AI enrichment is disabled. Add GENAI_API_KEY and OPENAI_API_KEY to keys.env to enable.')
            return redirect('crm:ai_enrichment')
        
        # Get all companies without enrichment
        companies_to_enrich = Company.objects.filter(
            work_website__isnull=True
        ).exclude(
            domain__in=['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com']
        )
        
        total_to_enrich = companies_to_enrich.count()
        
        if total_to_enrich == 0:
            messages.info(request, 'No companies need enrichment. All companies are already enriched!')
            return redirect('companies:company_list')
        
        # Use streaming response to show progress in real-time
        def enrich_generator():
            yield '''<!DOCTYPE html>
<html>
<head>
    <title>AI Enrichment Progress</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            margin: 0;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .progress-bar {
            width: 100%;
            height: 35px;
            background: #e9ecef;
            border-radius: 17px;
            overflow: hidden;
            margin-bottom: 15px;
            border: 1px solid #dee2e6;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 14px;
        }
        .status-current {
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            font-weight: 600;
            color: #856404;
        }
        .status {
            padding: 10px 15px;
            margin: 8px 0;
            border-radius: 5px;
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            font-size: 14px;
        }
        .success {
            border-left-color: #28a745;
            background: #d4edda;
            color: #155724;
        }
        .error {
            border-left-color: #dc3545;
            background: #f8d7da;
            color: #721c24;
        }
        .complete {
            text-align: center;
            margin-top: 30px;
        }
        .btn {
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 5px;
            display: inline-block;
            margin: 10px 5px;
            font-weight: 600;
        }
        .btn:hover {
            opacity: 0.9;
            color: white;
        }
        .btn-secondary {
            background: #6c757d;
        }
        .log-container {
            max-height: 400px;
            overflow-y: auto;
            margin-top: 20px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
        }
        .stats {
            display: flex;
            justify-content: space-around;
            margin: 20px 0;
        }
        .stat-box {
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            flex: 1;
            margin: 0 10px;
        }
        .stat-number {
            font-size: 28px;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            font-size: 12px;
            color: #6c757d;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AI Enrichment Progress</h1>
        <div class="progress-bar">
            <div class="progress-fill" id="progress" style="width: 0%">0/''' + str(total_to_enrich) + '''</div>
        </div>
        <div class="stats">
            <div class="stat-box">
                <div class="stat-number" id="total">''' + str(total_to_enrich) + '''</div>
                <div class="stat-label">TOTAL</div>
            </div>
            <div class="stat-box">
                <div class="stat-number" id="enriched" style="color: #28a745;">0</div>
                <div class="stat-label">ENRICHED</div>
            </div>
            <div class="stat-box">
                <div class="stat-number" id="errors" style="color: #dc3545;">0</div>
                <div class="stat-label">ERRORS</div>
            </div>
        </div>
        <div id="current-status"></div>
        <div class="log-container" id="log">
'''
            
            enriched_companies = 0
            errors = 0
            completed = 0
            lock = threading.Lock()
            
            # Function to enrich a single company
            def enrich_single_company(company):
                try:
                    enriched_data = enrich_company(company.domain, verbose=False)
                    
                    # Update company with enriched data
                    if enriched_data.get('work_website'):
                        company.work_website = enriched_data['work_website']
                    if enriched_data.get('linkedin'):
                        company.linkedin = enriched_data['linkedin']
                    if enriched_data.get('company_name'):
                        company.company_name = enriched_data['company_name']
                    if enriched_data.get('industry'):
                        company.industry = enriched_data['industry']
                    if enriched_data.get('company_size'):
                        company.company_size = enriched_data['company_size']
                    if enriched_data.get('hq_country'):
                        company.hq_country = enriched_data['hq_country']
                    if enriched_data.get('org_type'):
                        company.org_type = enriched_data['org_type']
                    if enriched_data.get('tech_stack'):
                        company.tech_stack = enriched_data['tech_stack']
                    if enriched_data.get('street'):
                        company.street = enriched_data['street']
                    if enriched_data.get('city'):
                        company.city = enriched_data['city']
                    if enriched_data.get('state'):
                        company.state = enriched_data['state']
                    if enriched_data.get('postal_code'):
                        company.postal_code = enriched_data['postal_code']
                    if enriched_data.get('country'):
                        company.country = enriched_data['country']
                    if enriched_data.get('work_phone'):
                        company.work_phone = enriched_data['work_phone']
                    if enriched_data.get('facebook'):
                        company.facebook = enriched_data['facebook']
                    
                    company.save()
                    return {'success': True, 'company': company, 'name': company.company_name or company.domain}
                except Exception as e:
                    return {'success': False, 'company': company, 'error': str(e)}
            
            # Process companies in parallel with 5 workers
            with ThreadPoolExecutor(max_workers=5) as executor:
                # Submit all tasks
                future_to_company = {executor.submit(enrich_single_company, company): company for company in companies_to_enrich}
                
                # Process results as they complete
                for future in as_completed(future_to_company):
                    with lock:
                        completed += 1
                        progress_percent = int((completed / total_to_enrich) * 100)
                    
                    result = future.result()
                    
                    # Update progress bar
                    yield f'''<script>
                        document.getElementById('progress').style.width = '{progress_percent}%';
                        document.getElementById('progress').textContent = '{completed}/{total_to_enrich}';
                        document.getElementById('current-status').innerHTML = '<div class="status-current">⚙️ Processing {completed}/{total_to_enrich} companies in parallel (5 threads)</div>';
                        window.scrollTo(0, document.body.scrollHeight);
                    </script>'''
                    
                    if result['success']:
                        with lock:
                            enriched_companies += 1
                        
                        yield f'''<div class="status success">✅ [{completed}/{total_to_enrich}] Successfully enriched: {result['name']}</div>
<script>
    document.getElementById('enriched').textContent = '{enriched_companies}';
    window.scrollTo(0, document.body.scrollHeight);
</script>'''
                    else:
                        with lock:
                            errors += 1
                        
                        error_msg = result['error'].replace("'", "\\'")
                        yield f'''<div class="status error">❌ [{completed}/{total_to_enrich}] Error enriching {result['company'].domain}: {error_msg}</div>
<script>
    document.getElementById('errors').textContent = '{errors}';
    window.scrollTo(0, document.body.scrollHeight);
</script>'''
            
            # Final update
            yield f'''<script>
                document.getElementById('progress').style.width = '100%';
                document.getElementById('progress').textContent = '{total_to_enrich}/{total_to_enrich}';
                document.getElementById('current-status').innerHTML = '';
            </script>'''
            
            yield f'''</div>
        <div class="complete">
            <h2>🎉 Enrichment Complete!</h2>
            <p style="font-size: 18px; color: #333;">Successfully enriched <strong>{enriched_companies}</strong> out of <strong>{total_to_enrich}</strong> companies.</p>
            {f'<p style="color: #dc3545; font-size: 16px;">{errors} errors occurred during enrichment.</p>' if errors > 0 else ''}
            <a href="/companies/" class="btn">View Companies</a>
            <a href="/" class="btn btn-secondary">Back to Home</a>
        </div>
    </div>
</body>
</html>'''
        
        return StreamingHttpResponse(enrich_generator(), content_type='text/html; charset=utf-8')
    
    # GET request - show enrichment page
    enrichment_enabled = bool(os.getenv("GENAI_API_KEY") and os.getenv("OPENAI_API_KEY"))
    
    # Count companies that need enrichment
    companies_needing_enrichment = Company.objects.filter(
        work_website__isnull=True
    ).exclude(
        domain__in=['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com']
    ).count()
    
    context = {
        'enrichment_enabled': enrichment_enabled,
        'companies_count': companies_needing_enrichment
    }
    
    return render(request, 'crm/ai_enrichment.html', context)


def enrichment_progress(request):
    """API endpoint to get enrichment progress"""
    from django.http import JsonResponse
    
    progress = request.session.get('enrichment_progress', {
        'total': 0,
        'current': 0,
        'enriched': 0,
        'errors': 0,
        'current_company': '',
        'status': 'idle',
        'logs': []
    })
    
    # Only return last 20 logs to avoid too much data
    if len(progress.get('logs', [])) > 20:
        progress['logs'] = progress['logs'][-20:]
    
    return JsonResponse(progress)


def import_csv(request):
    """Vista para importar leads desde CSV con enriquecimiento AI"""
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        
        # Validate file type
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a valid CSV file.')
            return redirect('crm:import_csv')
        
        # Validate file size (10MB max)
        if csv_file.size > 10 * 1024 * 1024:
            messages.error(request, 'File size must be less than 10MB.')
            return redirect('crm:import_csv')
        
        # Check if AI enrichment is enabled
        enable_enrichment = os.getenv("GENAI_API_KEY") and os.getenv("OPENAI_API_KEY")
        
        try:
            # Read and decode CSV
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            # Convert to list to get total count
            rows = list(reader)
            total_rows = len(rows)
            
            print("\n" + "="*60)
            print(f"📥 STARTING CSV IMPORT: {total_rows} rows to process")
            print("="*60 + "\n")
            
            created_companies = 0
            enriched_companies = 0
            created_leads = 0
            skipped_leads = 0
            errors = []
            
            # Track unique domains to enrich
            domains_to_enrich = set()
            
            for row_num, row in enumerate(rows, start=1):
                try:
                    email = row.get('email', '').strip()
                    
                    if not email or '@' not in email:
                        skipped_leads += 1
                        print(f"  [{row_num}/{total_rows}] ⚠️  Skipped invalid email")
                        continue
                    
                    # Extract domain from email
                    domain = email.split('@')[1].lower()
                    domains_to_enrich.add(domain)
                    
                    # Get or create company (without enrichment yet)
                    company, company_created = Company.objects.get_or_create(
                        domain=domain,
                        defaults={
                            'company_name': row.get('company_name', '').strip() or None,
                            'domain_confidence_score': 1.0 if domain not in ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com'] else 0.5
                        }
                    )
                    
                    if company_created:
                        created_companies += 1
                        print(f"  [{row_num}/{total_rows}] 🏢 Created company: {domain}")
                    
                    # Check if lead already exists
                    if Lead.objects.filter(email=email).exists():
                        skipped_leads += 1
                        print(f"  [{row_num}/{total_rows}] ⏭️  Skipped duplicate: {email}")
                        continue
                    
                    # Create lead
                    lead = Lead(
                        email=email,
                        company=company,
                        pdl_first_name=row.get('first_name', '').strip() or None,
                        pdl_last_name=row.get('last_name', '').strip() or None,
                        pdl_job_title=row.get('job_title', '').strip() or None,
                        lead_score=int(row.get('lead_score', 0)) if row.get('lead_score') else 0,
                        is_free_email=domain in ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com'],
                    )
                    lead.save()
                    created_leads += 1
                    
                    lead_name = f"{lead.pdl_first_name or ''} {lead.pdl_last_name or ''}".strip() or email
                    print(f"  [{row_num}/{total_rows}] ✅ Created lead: {lead_name}")
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                    print(f"  [{row_num}/{total_rows}] ❌ Error: {str(e)}")
                    continue
            
            print("\n" + "="*60)
            print(f"📊 CSV IMPORT COMPLETED")
            print(f"  Created: {created_leads} leads, {created_companies} companies")
            print(f"  Skipped: {skipped_leads} duplicates")
            print("="*60 + "\n")
            
            # Enrich companies with AI if enabled
            if enable_enrichment and domains_to_enrich:
                # Filter out free email domains
                business_domains = [d for d in domains_to_enrich if d not in ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com']]
                total_to_enrich = len(business_domains)
                
                print("\n" + "="*60)
                print(f"🤖 STARTING AI ENRICHMENT: {total_to_enrich} companies")
                print("="*60 + "\n")
                
                for idx, domain in enumerate(business_domains, start=1):
                    try:
                        company = Company.objects.get(domain=domain)
                        
                        # Skip if already enriched
                        if company.work_website and company.company_name:
                            print(f"  [{idx}/{total_to_enrich}] ⏭️  Already enriched: {domain}")
                            continue
                        
                        # Enrich with AI
                        print(f"\n  [{idx}/{total_to_enrich}] 🔍 Enriching: {domain}")
                        enriched_data = enrich_company(domain, verbose=True)
                        
                        # Update company with enriched data
                        if enriched_data.get('work_website'):
                            company.work_website = enriched_data['work_website']
                        if enriched_data.get('linkedin'):
                            company.linkedin = enriched_data['linkedin']
                        if enriched_data.get('company_name'):
                            company.company_name = enriched_data['company_name']
                        if enriched_data.get('industry'):
                            company.industry = enriched_data['industry']
                        if enriched_data.get('company_size'):
                            company.company_size = enriched_data['company_size']
                        if enriched_data.get('hq_country'):
                            company.hq_country = enriched_data['hq_country']
                        if enriched_data.get('org_type'):
                            company.org_type = enriched_data['org_type']
                        if enriched_data.get('tech_stack'):
                            company.tech_stack = enriched_data['tech_stack']
                        if enriched_data.get('street'):
                            company.street = enriched_data['street']
                        if enriched_data.get('city'):
                            company.city = enriched_data['city']
                        if enriched_data.get('state'):
                            company.state = enriched_data['state']
                        if enriched_data.get('postal_code'):
                            company.postal_code = enriched_data['postal_code']
                        if enriched_data.get('country'):
                            company.country = enriched_data['country']
                        if enriched_data.get('work_phone'):
                            company.work_phone = enriched_data['work_phone']
                        if enriched_data.get('facebook'):
                            company.facebook = enriched_data['facebook']
                        
                        company.save()
                        enriched_companies += 1
                        print(f"  ✅ [{idx}/{total_to_enrich}] Saved: {company.company_name or domain}\n")
                        
                    except Exception as e:
                        print(f"  ❌ [{idx}/{total_to_enrich}] Error enriching {domain}: {e}\n")
                        continue
                
                print("="*60)
                print(f"🎉 AI ENRICHMENT COMPLETED: {enriched_companies}/{total_to_enrich} companies enriched")
                print("="*60 + "\n")
            
            # Show results
            success_msg = f'Import completed! Created {created_leads} leads and {created_companies} companies.'
            if enable_enrichment and enriched_companies > 0:
                success_msg += f' AI-enriched {enriched_companies} companies.'
            success_msg += f' Skipped {skipped_leads} duplicates.'
            
            messages.success(request, success_msg)
            
            if errors:
                messages.warning(request, f'{len(errors)} errors occurred during import.')
            
            if not enable_enrichment:
                messages.info(request, 'AI enrichment disabled. Add GENAI_API_KEY and OPENAI_API_KEY to .env to enable.')
            
            return redirect('leads:lead_list')
            
        except Exception as e:
            messages.error(request, f'Error processing CSV: {str(e)}')
            return redirect('crm:import_csv')
    
    # Check if enrichment is configured
    enrichment_enabled = bool(os.getenv("GENAI_API_KEY") and os.getenv("OPENAI_API_KEY"))
    
    return render(request, 'crm/import_csv.html', {'enrichment_enabled': enrichment_enabled})
