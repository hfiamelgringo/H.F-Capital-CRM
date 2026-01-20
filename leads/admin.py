from django.contrib import admin
from django.shortcuts import render
from django.utils.html import format_html
from .models import Lead, Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['domain', 'company_name', 'industry', 'company_size', 'hq_country', 'created_at']
    list_filter = ['industry', 'org_type', 'hq_country']
    search_fields = ['domain', 'company_name', 'industry']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['view_details']
    
    @admin.action(description='Ver detalles completos')
    def view_details(self, request, queryset):
        """Muestra los detalles completos de las empresas seleccionadas sin permitir edición."""
        if queryset.count() == 1:
            company = queryset.first()
            context = {
                'title': f'Detalles de {company.company_name or company.domain}',
                'object': company,
                'opts': self.model._meta,
                'fields': [
                    ('Información Básica', [
                        ('Domain', company.domain),
                        ('Nombre de la Empresa', company.company_name or '-'),
                        ('Industria', company.industry or '-'),
                        ('Tamaño de la Empresa', company.company_size or '-'),
                        ('País HQ', company.hq_country or '-'),
                        ('Tipo de Organización', company.org_type or '-'),
                        ('Tech Stack', company.tech_stack or '-'),
                        ('Confianza del Dominio', company.domain_confidence_score or '-'),
                    ]),
                    ('Dirección', [
                        ('Calle', company.street or '-'),
                        ('Ciudad', company.city or '-'),
                        ('Estado', company.state or '-'),
                        ('Código Postal', company.postal_code or '-'),
                        ('País', company.country or '-'),
                    ]),
                    ('Contacto y Redes', [
                        ('Teléfono', company.work_phone or '-'),
                        ('Sitio Web', company.work_website or '-'),
                        ('LinkedIn', company.linkedin or '-'),
                        ('Facebook', company.facebook or '-'),
                    ]),
                    ('CRM', [
                        ('Propiedad de', company.owned_by or '-'),
                        ('Tipo de Contacto', company.contact_type or '-'),
                        ('Tags', company.tags or '-'),
                        ('Último Contacto', company.last_contacted or '-'),
                    ]),
                    ('Financiamiento (PDL)', [
                        ('Total Financiamiento', f'${company.pdl_total_funding_raised:,.2f}' if company.pdl_total_funding_raised else '-'),
                        ('Última Etapa de Financiamiento', company.pdl_latest_funding_stage or '-'),
                        ('Última Fecha de Financiamiento', company.pdl_last_funding_date or '-'),
                        ('Número de Rondas', company.pdl_number_funding_rounds or '-'),
                    ]),
                    ('Fechas', [
                        ('Creado', company.created_at),
                        ('Actualizado', company.updated_at),
                    ]),
                ],
            }
            return render(request, 'admin/view_details.html', context)
        else:
            self.message_user(request, 'Por favor selecciona solo un elemento para ver sus detalles.', level='warning')
            return None


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['email', 'get_full_name', 'company', 'lead_score', 'lead_stage', 'email_status', 'created_at']
    list_filter = ['lead_stage', 'hierarchical_level', 'email_status', 'is_candidate_enterprise']
    search_fields = ['email', 'pdl_first_name', 'pdl_last_name', 'pdl_job_title', 'company__company_name']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['lead_score', 'lead_stage']
    actions = ['view_details']
    
    def get_full_name(self, obj):
        return f"{obj.pdl_first_name or ''} {obj.pdl_last_name or ''}".strip() or '-'
    get_full_name.short_description = 'Name'
    
    @admin.action(description='Ver detalles completos')
    def view_details(self, request, queryset):
        """Muestra los detalles completos del lead seleccionado sin permitir edición."""
        if queryset.count() == 1:
            lead = queryset.first()
            context = {
                'title': f'Detalles de {lead.get_full_name() or lead.email}',
                'object': lead,
                'opts': self.model._meta,
                'fields': [
                    ('Información Personal', [
                        ('Email', lead.email),
                        ('Nombre', lead.pdl_first_name or '-'),
                        ('Apellido', lead.pdl_last_name or '-'),
                        ('Puesto de Trabajo', lead.pdl_job_title or '-'),
                        ('LinkedIn', lead.pdl_linkedin_url or '-'),
                        ('Última Verificación del Trabajo', lead.pdl_job_last_verified or '-'),
                    ]),
                    ('Empresa', [
                        ('Empresa', str(lead.company)),
                        ('Email Gratuito', 'Sí' if lead.is_free_email else 'No'),
                    ]),
                    ('Lead Scoring y Segmentación', [
                        ('Puntaje del Lead', lead.lead_score),
                        ('Etapa del Lead', lead.get_lead_stage_display() if lead.lead_stage else '-'),
                        ('Nivel Jerárquico', lead.get_hierarchical_level_display() if lead.hierarchical_level else '-'),
                        ('Candidato Enterprise', 'Sí' if lead.is_candidate_enterprise else 'No'),
                        ('Segmento de Campaña', lead.campaign_segment or '-'),
                    ]),
                    ('Estado y Actividad', [
                        ('Estado del Email', lead.get_email_status_display()),
                        ('Fecha de Registro', lead.signup_date or '-'),
                        ('Conteo de Sesiones', lead.session_count or '-'),
                        ('Primera Vez Visto', lead.first_seen or '-'),
                        ('Última Actividad', lead.last_active or '-'),
                        ('Última Fecha de Contacto', lead.last_contacted_date or '-'),
                    ]),
                    ('CRM', [
                        ('Propietario CRM', lead.crm_owner or '-'),
                    ]),
                    ('Fechas', [
                        ('Creado', lead.created_at),
                        ('Actualizado', lead.updated_at),
                    ]),
                ],
            }
            return render(request, 'admin/view_details.html', context)
        else:
            self.message_user(request, 'Por favor selecciona solo un elemento para ver sus detalles.', level='warning')
            return None
