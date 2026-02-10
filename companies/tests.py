from django.test import TestCase
from django.urls import reverse

from leads.models import Company, CompanyNote


class CompanyNotesTests(TestCase):
	def setUp(self):
		self.company = Company.objects.create(domain='acme.com', company_name='Acme Inc')
		self.other_company = Company.objects.create(domain='other.com', company_name='Other Co')

	def test_notes_page_renders(self):
		url = reverse('companies:company_notes', kwargs={'pk': self.company.domain})
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, 'Company Notes')

	def test_create_note(self):
		url = reverse('companies:company_notes', kwargs={'pk': self.company.domain})
		resp = self.client.post(url, data={'body': 'Called them, waiting on reply.'})
		self.assertEqual(resp.status_code, 302)
		self.assertTrue(CompanyNote.objects.filter(company=self.company, body__icontains='waiting').exists())

	def test_edit_note(self):
		note = CompanyNote.objects.create(company=self.company, body='Initial')
		url = reverse('companies:company_note_update', kwargs={'pk': self.company.domain, 'note_id': note.id})
		resp = self.client.post(url, data={'body': 'Updated text'})
		self.assertEqual(resp.status_code, 302)
		note.refresh_from_db()
		self.assertEqual(note.body, 'Updated text')

	def test_delete_note(self):
		note = CompanyNote.objects.create(company=self.company, body='To be deleted')
		url = reverse('companies:company_note_delete', kwargs={'pk': self.company.domain, 'note_id': note.id})
		resp = self.client.post(url)
		self.assertEqual(resp.status_code, 302)
		self.assertFalse(CompanyNote.objects.filter(id=note.id).exists())

	def test_cross_company_note_access_is_404(self):
		note = CompanyNote.objects.create(company=self.company, body='Secret')
		url = reverse('companies:company_note_update', kwargs={'pk': self.other_company.domain, 'note_id': note.id})
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 404)
