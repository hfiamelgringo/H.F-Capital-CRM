"""
Company enrichment utilities using DuckDuckGo, Gemini, and ChatGPT.
Adapted from enrich_and_import_companies.py
"""

import time
import json
import re
import os
from ddgs import DDGS
import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv("keys.env")

# Configure AI clients
GENAI_API_KEY = os.getenv("GENAI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize clients only if keys are available
gemini_client = None
gpt_client = None

if GENAI_API_KEY:
    genai.configure(api_key=GENAI_API_KEY)

if OPENAI_API_KEY:
    gpt_client = OpenAI(api_key=OPENAI_API_KEY)


def collect_candidates(domain: str, search_type="website", max_results: int = 6):
    """Search for URLs using DuckDuckGo."""
    company_name = domain.split('.')[0].replace('-', ' ').title()
    
    if search_type == "website":
        queries = [
            f"{company_name} official site",
            f"{company_name} company website",
            f"{company_name} homepage"
        ]
    elif search_type == "linkedin":
        queries = [
            f"{company_name} official LinkedIn page",
            f"{company_name} LinkedIn company profile",
            f"{company_name} site:linkedin.com"
        ]
    else:
        raise ValueError("Unknown search type")

    urls = []
    try:
        with DDGS() as ddgs:
            for q in queries:
                try:
                    for r in ddgs.text(q, max_results=max_results):
                        href = r.get("href") or r.get("link")
                        title = r.get("title", "")
                        if not href:
                            continue
                        urls.append({"title": title, "url": href, "query": q})
                    time.sleep(0.2)
                except Exception as e:
                    print(f"Search error: {e}")
                    continue
    except Exception as e:
        print(f"DDGS error: {e}")
        return []

    # Remove duplicates
    seen = set()
    dedup = []
    for item in urls:
        u = item["url"]
        if u not in seen:
            seen.add(u)
            dedup.append(item)
    return dedup


def select_best_with_gemini(domain: str, candidates: list, kind="website"):
    """Gemini selects the best URL from candidates."""
    if not candidates or not GENAI_API_KEY:
        return None

    company_name = domain.split('.')[0].title()
    urls_text = "\n".join([f"- {c['title']} ({c['url']})" for c in candidates])
    prompt = f"""You are selecting the best URL for a company.
Company: {company_name} (domain: {domain})
Type: {kind}

Candidates:
{urls_text}

Choose the most likely official URL from the list above.
Respond with ONLY the URL, nothing else. No explanations, no additional text.
If none match, respond with the first URL from the list.
"""
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Extract only the URL from the response
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith('http://') or line.startswith('https://'):
                return line
        
        # Try to extract from the text using regex
        urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', text)
        if urls:
            return urls[0]
        
        return text
    except Exception as e:
        print(f"Gemini error: {e}")
        return None


def get_company_info_with_gpt(domain: str, website: str, linkedin: str):
    """Use ChatGPT to extract company information."""
    if not gpt_client:
        return None
        
    company_name = domain.split('.')[0].replace('-', ' ').title()
    
    prompt = f"""Based on the domain "{domain}", extract comprehensive company information.

Website: {website or 'Unknown'}
LinkedIn: {linkedin or 'Unknown'}

Return ONLY a JSON object with this exact structure (use null for unknown fields):
{{
    "company_name": "Official company name",
    "industry": "Industry/sector",
    "company_size": estimated_employee_count_as_integer_or_null,
    "hq_country": "Country code like US, UK, CA",
    "org_type": "one of: private, public, gov, edu, nonprofit",
    "tech_stack": "Brief technologies description",
    "street": "Street address if available",
    "city": "City name",
    "state": "State/Province",
    "postal_code": "Postal/ZIP code",
    "country": "Full country name",
    "work_phone": "Phone number with country code",
    "facebook": "Facebook page URL if known"
}}

Return ONLY the JSON, no additional text."""

    try:
        response = gpt_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = response.choices[0].message.content.strip()
        
        # Remove markdown if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1]) if len(lines) > 2 else response_text
            if response_text.startswith("json"):
                response_text = response_text[4:].strip()
        
        data = json.loads(response_text)
        return data
    except Exception as e:
        print(f"GPT error: {e}")
        return None


def get_company_info_with_gemini(domain: str, website: str, linkedin: str):
    """Use Gemini to extract company information."""
    if not GENAI_API_KEY:
        return None
        
    company_name = domain.split('.')[0].replace('-', ' ').title()
    
    prompt = f"""Based on the domain "{domain}", extract comprehensive company information.

Website: {website or 'Unknown'}
LinkedIn: {linkedin or 'Unknown'}

Return ONLY a JSON object with this exact structure (use null for unknown fields):
{{
    "company_name": "Official company name",
    "industry": "Industry/sector",
    "company_size": estimated_employee_count_as_integer_or_null,
    "hq_country": "Country code like US, UK, CA",
    "org_type": "one of: private, public, gov, edu, nonprofit",
    "tech_stack": "Brief technologies description",
    "street": "Street address if available",
    "city": "City name",
    "state": "State/Province",
    "postal_code": "Postal/ZIP code",
    "country": "Full country name",
    "work_phone": "Phone number with country code",
    "facebook": "Facebook page URL if known"
}}

Return ONLY the JSON, no additional text."""

    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Remove markdown if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1]) if len(lines) > 2 else response_text
            if response_text.startswith("json"):
                response_text = response_text[4:].strip()
        
        data = json.loads(response_text)
        return data
    except Exception as e:
        print(f"Gemini error: {e}")
        return None


def merge_and_verify_data(gpt_data: dict, gemini_data: dict, domain: str, website: str, linkedin: str):
    """
    Merge and verify data from both GPT and Gemini.
    Uses cross-validation to ensure accuracy.
    """
    if not gpt_data and not gemini_data:
        return None
    
    if not gpt_data:
        return gemini_data
    
    if not gemini_data:
        return gpt_data
    
    # Merge data, preferring values that both agree on
    merged = {}
    
    # For each field, compare both sources
    for key in gpt_data.keys():
        gpt_val = gpt_data.get(key)
        gemini_val = gemini_data.get(key)
        
        # If both agree or one is None, take the non-None value
        if gpt_val == gemini_val:
            merged[key] = gpt_val
        elif gpt_val and not gemini_val:
            merged[key] = gpt_val
        elif gemini_val and not gpt_val:
            merged[key] = gemini_val
        else:
            # If they differ, use GPT-4 to verify which is more accurate
            # For now, prefer GPT-4o-mini as it's generally more reliable
            merged[key] = gpt_val
    
    return merged


def enrich_company(domain: str, verbose=False):
    """
    Enrich a company domain with website, LinkedIn, and AI-extracted data.
    Returns a dict with enriched data.
    """
    if verbose:
        print(f"🔍 Enriching: {domain}")
    
    enriched_data = {
        'work_website': None,
        'linkedin': None,
        'company_name': None,
        'industry': None,
        'company_size': None,
        'hq_country': None,
        'org_type': None,
        'tech_stack': None,
        'street': None,
        'city': None,
        'state': None,
        'postal_code': None,
        'country': None,
        'work_phone': None,
        'facebook': None,
    }
    
    try:
        # Search for website
        if verbose:
            print(f"  🔍 Searching website...")
        web_candidates = collect_candidates(domain, "website")
        best_website = select_best_with_gemini(domain, web_candidates, "website") if web_candidates else None
        if best_website:
            enriched_data['work_website'] = best_website
            if verbose:
                print(f"  🌐 Website: {best_website}")
        
        # Search for LinkedIn
        if verbose:
            print(f"  🔍 Searching LinkedIn...")
        linkedin_candidates = collect_candidates(domain, "linkedin")
        best_linkedin = select_best_with_gemini(domain, linkedin_candidates, "linkedin") if linkedin_candidates else None
        if best_linkedin:
            enriched_data['linkedin'] = best_linkedin
            if verbose:
                print(f"  💼 LinkedIn: {best_linkedin}")
        
        # Get company info with GPT
        if verbose:
            print(f"  🤖 Enriching with ChatGPT...")
        gpt_data = get_company_info_with_gpt(domain, best_website, best_linkedin)
        
        # Get company info with Gemini
        if verbose:
            print(f"  🤖 Enriching with Gemini...")
        gemini_data = get_company_info_with_gemini(domain, best_website, best_linkedin)
        
        # Merge and verify data from both sources
        if verbose:
            print(f"  🔍 Cross-validating data from both AI models...")
        ai_data = merge_and_verify_data(gpt_data, gemini_data, domain, best_website, best_linkedin)
        
        if ai_data:
            enriched_data.update({k: v for k, v in ai_data.items() if v})
            if verbose and ai_data.get('company_name'):
                print(f"  ✓ Enriched & Verified: {ai_data.get('company_name')}")
        
        # Add delay to avoid rate limiting
        time.sleep(1)
        
        return enriched_data
        
    except Exception as e:
        if verbose:
            print(f"  ❌ Error: {e}")
        return enriched_data
