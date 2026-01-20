"""
Old script for lead management - Temp file used in older beta versions.
"""

import sys
import subprocess
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from browserling_leads.db import get_session
from browserling_leads.models import Lead


def clear_screen():
    """Clear the console screen."""
    subprocess.run("cls", shell=True)


def show_menu():
    """Display the main menu."""
    print("=" * 60)
    print("           BROWSERLING LEAD ENRICHMENT - LEADS")
    print("=" * 60)
    print()
    print("1. 📥 Import Leads from CSV")
    print("2. � Enrich Leads with People Data Labs")
    print("3. 🔧 Upload Leads to Copper CRM")
    print("4. 📊 Open Streamlit Dashboard")
    print("5. 📋 Upload Leads to Airtable")
    print("6. 📤 Export Enriched Leads to CSV")
    print("7. ✅ Check Leads Database")
    print("8. 🗑️  Clear Leads Database")
    print("0. 🚪 Exit")
    print()
    print("=" * 60)


def import_leads():
    """Import leads from CSV."""
    print("\n📥 IMPORT LEADS FROM CSV")
    print("-" * 60)
    
    csv_file = input("Enter CSV file path (or press Enter for default): ").strip()
    
    if not csv_file:
        # Use default file
        csv_file = "browserling_leads_final-500 .csv"
    
    confirm = input(f"Import leads from '{csv_file}'? (y/n): ").strip().lower()
    if confirm == "y":
        subprocess.run(f'python scripts/import_csv_batch.py "{csv_file}"', shell=True)
    
    input("\nPress Enter to continue...")


def enrich_with_pdl():
    """Enrich leads with People Data Labs API."""
    print("\n🔍 ENRICH LEADS WITH PEOPLE DATA LABS")
    print("-" * 60)
    print("Options:")
    print("1. Dry run - View data for first 5 leads (no database update)")
    print("2. Enrich specific number of leads")
    print("3. Enrich specific lead by email")
    print("4. Enrich ALL leads (⚠️  costs API credits)")
    print("5. Configure AI classification (Gemini/ChatGPT)")
    print("0. Back to main menu")
    
    choice = input("\nSelect option: ").strip()
    
    if choice == "1":
        subprocess.run("python scripts/leadsPDL.py --limit 5 --dry-run", shell=True)
    elif choice == "2":
        limit = input("Enter number of leads to enrich: ").strip()
        if limit.isdigit():
            use_ai = input("Use AI for hierarchical classification? (y/n): ").strip().lower()
            ai_flag = ""
            if use_ai == "y":
                ai_model = input("Select AI model (1=Gemini, 2=ChatGPT) [default: 1]: ").strip()
                model = "chatgpt" if ai_model == "2" else "gemini"
                ai_flag = f" --use-ai --ai-model {model}"
            
            dry_run = input("Dry run first? (y/n): ").strip().lower()
            if dry_run == "y":
                subprocess.run(f"python scripts/leadsPDL.py --limit {limit} --dry-run{ai_flag}", shell=True)
            else:
                confirm = input(f"⚠️  This will use API credits for {limit} lead(s). Continue? (y/n): ").strip().lower()
                if confirm == "y":
                    subprocess.run(f"python scripts/leadsPDL.py --limit {limit}{ai_flag}", shell=True)
        else:
            print("❌ Invalid number.")
    elif choice == "3":
        email = input("Enter lead email: ").strip()
        if email:
            use_ai = input("Use AI for hierarchical classification? (y/n): ").strip().lower()
            ai_flag = ""
            if use_ai == "y":
                ai_model = input("Select AI model (1=Gemini, 2=ChatGPT) [default: 1]: ").strip()
                model = "chatgpt" if ai_model == "2" else "gemini"
                ai_flag = f" --use-ai --ai-model {model}"
            
            dry_run = input("Dry run first? (y/n): ").strip().lower()
            if dry_run == "y":
                subprocess.run(f'python scripts/leadsPDL.py --email "{email}" --dry-run{ai_flag}', shell=True)
            else:
                subprocess.run(f'python scripts/leadsPDL.py --email "{email}"{ai_flag}', shell=True)
        else:
            print("❌ Email required.")
    elif choice == "4":
        confirm = input("⚠️  This will enrich ALL leads and use significant API credits. Continue? (y/n): ").strip().lower()
        if confirm == "y":
            use_ai = input("Use AI for hierarchical classification? (y/n): ").strip().lower()
            ai_flag = ""
            if use_ai == "y":
                ai_model = input("Select AI model (1=Gemini, 2=ChatGPT) [default: 1]: ").strip()
                model = "chatgpt" if ai_model == "2" else "gemini"
                ai_flag = f" --use-ai --ai-model {model}"
            
            double_confirm = input("Type 'ENRICH' to confirm: ").strip()
            if double_confirm == "ENRICH":
                subprocess.run(f"python scripts/leadsPDL.py --limit 999999{ai_flag}", shell=True)
            else:
                print("Cancelled.")
        else:
            print("Cancelled.")
    elif choice == "5":
        print("\n🤖 AI HIERARCHICAL CLASSIFICATION")
        print("-" * 60)
        print("\nAI classification uses Gemini or ChatGPT to determine hierarchical levels")
        print("based on full PDL context (job title, company size, industry, etc.)")
        print("\nBenefits:")
        print("  ✅ More contextual and accurate classification")
        print("  ✅ Better handling of ambiguous titles")
        print("  ✅ Considers company size and industry")
        print("\nCosts:")
        print("  💰 Additional API calls (Gemini or OpenAI)")
        print("  ⏱️  Slightly slower than rule-based")
        print("\nUsage: Select options 2-4 and choose 'y' for AI classification")
        input("\nPress Enter to continue...")
    
    input("\nPress Enter to continue...")


def upload_to_copper():
    """Upload leads to Copper CRM."""
    print("\n🔧 UPLOAD TO COPPER CRM")
    print("-" * 60)
    print("Options:")
    print("1. Dry run (test without uploading)")
    print("2. Upload first 10 leads")
    print("3. Upload specific number of leads")
    print("4. Upload with company linking")
    print("5. Upload ALL enriched leads")
    print("0. Back to main menu")
    
    choice = input("\nSelect option: ").strip()
    
    if choice == "1":
        limit = input("Enter limit for dry run: ").strip() or "10"
        subprocess.run(f"python scripts/upload_leads_to_copper.py --limit {limit} --dry-run", shell=True)
    elif choice == "2":
        subprocess.run("python scripts/upload_leads_to_copper.py --limit 10", shell=True)
    elif choice == "3":
        limit = input("Enter number of leads to upload: ").strip()
        subprocess.run(f"python scripts/upload_leads_to_copper.py --limit {limit}", shell=True)
    elif choice == "4":
        limit = input("Enter number of leads: ").strip() or "10"
        link = input("⚠️  This will link leads to companies in Copper. Continue? (y/n): ").strip().lower()
        if link == "y":
            subprocess.run(f"python scripts/upload_leads_to_copper.py --limit {limit} --link-companies", shell=True)
    elif choice == "5":
        confirm = input("⚠️  This will upload ALL leads. Continue? (y/n): ").strip().lower()
        if confirm == "y":
            subprocess.run("python scripts/upload_leads_to_copper.py --limit 999999", shell=True)
    
    input("\nPress Enter to continue...")


def open_dashboard():
    """Open Streamlit dashboard."""
    print("\n📊 OPENING STREAMLIT DASHBOARD")
    print("-" * 60)
    print("Starting Streamlit server...")
    print("Press Ctrl+C in the new window to stop the server")
    print("The dashboard will open in your browser automatically...")
    # Run streamlit in a new terminal window with conda activated
    subprocess.run('start cmd /k "conda activate browserling-leads && streamlit run scripts/dashboard.py"', shell=True)
    input("\nPress Enter to continue...")


def upload_to_airtable():
    """Upload leads to Airtable."""
    print("\n📋 UPLOAD TO AIRTABLE")
    print("-" * 60)
    print("Options:")
    print("1. Dry run (test connection)")
    print("2. Upload first 10 leads")
    print("3. Upload specific number of leads")
    print("4. Upload ALL enriched leads")
    print("5. Upload high-priority leads only (score >= 70)")
    print("0. Back to main menu")
    
    choice = input("\nSelect option: ").strip()
    
    if choice == "1":
        limit = input("Enter limit for dry run: ").strip() or "10"
        subprocess.run(f"python scripts/upload_leads_to_airtable.py --limit {limit} --dry-run", shell=True)
    elif choice == "2":
        subprocess.run("python scripts/upload_leads_to_airtable.py --limit 10", shell=True)
    elif choice == "3":
        limit = input("Enter number of leads to upload: ").strip()
        subprocess.run(f"python scripts/upload_leads_to_airtable.py --limit {limit}", shell=True)
    elif choice == "4":
        confirm = input("⚠️  This will upload ALL leads. Continue? (y/n): ").strip().lower()
        if confirm == "y":
            subprocess.run("python scripts/upload_leads_to_airtable.py --limit 999999", shell=True)
    elif choice == "5":
        limit = input("Enter number of high-priority leads to upload (default 100): ").strip() or "100"
        subprocess.run(f"python scripts/upload_leads_to_airtable.py --min-score 70 --limit {limit}", shell=True)
    
    input("\nPress Enter to continue...")


def export_leads():
    """Export enriched leads to CSV."""
    print("\n📤 EXPORT LEADS TO CSV")
    print("-" * 60)
    print("Options:")
    print("1. Export leads only")
    print("2. Export leads and companies")
    print("0. Back to main menu")
    
    choice = input("\nSelect option: ").strip()
    
    if choice == "1":
        subprocess.run("python scripts/export_enriched_data.py --leads-only", shell=True)
    elif choice == "2":
        subprocess.run("python scripts/export_enriched_data.py", shell=True)
    
    input("\nPress Enter to continue...")


def check_leads():
    """Check leads database statistics."""
    print("\n✅ DATABASE STATISTICS")
    print("-" * 60)
    
    with get_session() as session:
        total_leads = session.query(Lead).count()
        enriched_leads = session.query(Lead).filter(Lead.enriched == True).count()
        
        # Count by stage
        from sqlalchemy import func
        stages = session.query(
            Lead.lead_stage,
            func.count(Lead.id)
        ).group_by(Lead.lead_stage).all()
        
        print(f"\n📊 Lead Statistics:")
        print(f"  Total leads: {total_leads}")
        print(f"  Enriched leads: {enriched_leads}")
        print(f"  Not enriched: {total_leads - enriched_leads}")
        
        if stages:
            print(f"\n📈 Leads by Stage:")
            for stage, count in stages:
                stage_name = stage or "Unknown"
                print(f"  {stage_name}: {count}")
        
        # Count by score range
        score_ranges = [
            ("High Priority (80+)", 80, 100),
            ("Medium Priority (60-79)", 60, 79),
            ("Low Priority (40-59)", 40, 59),
            ("Very Low (<40)", 0, 39),
        ]
        
        print(f"\n⭐ Leads by Score Range:")
        for label, min_score, max_score in score_ranges:
            count = session.query(Lead).filter(
                Lead.lead_score >= min_score,
                Lead.lead_score <= max_score
            ).count()
            if count > 0:
                print(f"  {label}: {count}")
    
    input("\nPress Enter to continue...")


def clear_leads():
    """Clear leads database."""
    print("\n🗑️  CLEAR LEADS DATABASE")
    print("-" * 60)
    confirm = input("⚠️  This will DELETE ALL leads. Are you sure? (y/n): ").strip().lower()
    if confirm == "y":
        double_confirm = input("Type 'DELETE' to confirm: ").strip()
        if double_confirm == "DELETE":
            with get_session() as session:
                deleted_count = session.query(Lead).delete()
                session.commit()
                print(f"\n✅ Deleted {deleted_count} leads from database.")
        else:
            print("Cancelled.")
    else:
        print("Cancelled.")
    
    input("\nPress Enter to continue...")


def main():
    """Main entry point."""
    while True:
        clear_screen()
        show_menu()
        
        choice = input("Select an option: ").strip()
        
        if choice == "1":
            import_leads()
        elif choice == "2":
            enrich_with_pdl()
        elif choice == "3":
            upload_to_copper()
        elif choice == "4":
            open_dashboard()
        elif choice == "5":
            upload_to_airtable()
        elif choice == "6":
            export_leads()
        elif choice == "7":
            check_leads()
        elif choice == "8":
            clear_leads()
        elif choice == "0":
            print("\n👋 Goodbye!")
            break
        else:
            print("\n❌ Invalid option. Please try again.")
            input("Press Enter to continue...")


if __name__ == "__main__":
    main()
