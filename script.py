import requests, time
from bs4 import BeautifulSoup
import excel

import urllib3
urllib3.disable_warnings() # Disable ssl certificate warning

request_number = 0
		

def add_to_collection(organization_info, head_info, contacts):

	def get_table_data(tr):
		return tr.findChild("td", recursive=False).text.strip()
	
	def get_contacts():
		addresses = []
		for contact in contacts[1:]:
			address = contact.findChildren('td', recursive=False)[2].text.strip()
			addresses.append(address)
		return '; '.join(addresses)


	org_name = get_table_data(organization_info[7])
	org_bin = get_table_data(organization_info[4])
	head_name = get_table_data(head_info[2])
	head_iin = get_table_data(head_info[0])
	full_address = get_contacts()

	if org_bin not in organizations_set:
		organizations_set.add(org_bin)
		data_collection.append([org_name, org_bin, head_name, head_iin, full_address])


def parse_supplier_by_url(url):
	html = get_request(url)
	return get_soup(html)


def isNone(soup): # if request get error response will be none(may be)
	return (soup is None) or (soup.body is None) or (soup.body.main is None)

def parse_suppliers(suppliers_link):
	
	def get_panel(num):
		return panels[num].findChild('div', class_='panel-body').findChild('table', class_='table').findChildren("tr", recursive=False)
	
	for supplier_link in suppliers_link:
		soup = parse_supplier_by_url(supplier_link['href'])
		
		if isNone(soup):
			suppliers_link.append(supplier_link)
			continue

		content_block = soup.body.main.find('div', class_='content-block')
		panels_parent = content_block.findChildren('div', recursive=False)[-1]
		panels = panels_parent.findChildren('div', recursive=False, class_='panel')
		
		organization_info = get_panel(0)
		head_info = get_panel(2)
		contacts = get_panel(3)

		add_to_collection(organization_info, head_info, contacts)


def get_request(url):
	global request_number

	if request_number % 6 == 0: # avoid captcha
		time.sleep(3)

	try:
		response = requests.get(url, verify=False, timeout=10)
		request_number += 1
	except:
		time.sleep(3)
		request_number = 0
		return get_request(url)

	return response.text


def get_soup(html):
	return BeautifulSoup(html, "html.parser")


def parse_registry_at_page(page_num):
	html = get_request(f"https://www.goszakup.gov.kz/ru/registry/rqc?count_record={COUNT_RECORD}&page={page_num}")
	return get_soup(html)


def parse_page(page_num):
	soup = parse_registry_at_page(page_num)		
	content_block = soup.body.main.find('div', class_='content-block')
	table_of_suppliers = content_block.find('div', class_='table-responsive').findChild("tbody")
	suppliers_link = table_of_suppliers.findChildren("a")
	parse_suppliers(suppliers_link)

	if len(suppliers_link) == COUNT_RECORD:
		parse_page(page_num+1)


if __name__ == "__main__":
	COUNT_RECORD = 500
	
	organizations_set = set()
	data_collection = []

	parse_page(1)
	print(len(data_collection))
	print(len(organizations_set))
	excel.export_to_excel(data_collection)
