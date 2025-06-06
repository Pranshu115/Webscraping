# -*- coding: utf-8 -*-
"""webscraping_final.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1FbLX6dquqScck8O2ty4LmKKIQ04SLxK7
"""

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import pandas as pd
import re

# Base URL
base_url = "https://www.indcareer.com"

def clean_text(text):
    """Cleans and extracts readable text from HTML content."""
    soup = BeautifulSoup(text, 'html.parser')
    return soup.get_text(separator=" ").strip().replace('[email\xa0protected]', '')

def extract_email(text):
    """Extracts email addresses from text."""
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    emails = re.findall(email_pattern, text)
    return ", ".join(emails) if emails else ""

def extract_phone_numbers(text):
    """Extracts phone numbers from text."""
    phone_pattern = r"\+?\d{1,3}[-./\s]?\(?\d{2,5}\)?[-./\s]?\d{2,5}[-./\s]?\d{2,5}[-./\s]?\d{1,5}"
    phone_numbers = re.findall(phone_pattern, text)

    valid_numbers = []
    for phone in phone_numbers:
        phone = re.sub(r"[^\d+]", "", phone)
        if phone.startswith("0"):
            phone = phone[1:]
        if 10 <= len(phone) <= 12:
            valid_numbers.append(f"+91{phone}" if not phone.startswith("+") else phone)

    return ", ".join(valid_numbers) if valid_numbers else ""

# List of states and UTs formatted for URLs
states_ut = [
    "andhra-pradesh", "arunachal-pradesh", "assam", "bihar",
    "chhattisgarh", "goa", "gujarat", "haryana", "himachal-pradesh", "jharkhand", "karnataka",
    "kerala", "madhya-pradesh", "maharashtra", "manipur", "meghalaya", "mizoram", "nagaland",
    "odisha", "punjab", "rajasthan", "sikkim", "tamil-nadu", "telangana", "tripura",
    "uttar-pradesh", "uttarakhand", "west-bengal", "andaman-nicobar-islands", "chandigarh",
    "dadra-nagar-haveli-daman-diu", "delhi", "lakshadweep", "puducherry", "ladakh", "jammu-kashmir"
]

def get_college_links(state):
    """Fetches all college links for a given state."""
    print(f"Scraping colleges in {state.title()}...")

    links = []
    for x in tqdm(range(0, 120)):  # Adjust range if required
        response = requests.get(f"https://www.indcareer.com/find/all-colleges-in-{state}?page={x}")
        if response.status_code != 200:
            break  # Stop if the page does not exist

        soup = BeautifulSoup(response.content, 'html.parser')
        h4s = soup.find_all("h4")

        for h4 in h4s:
            a_tag = h4.find("a")
            if a_tag and 'href' in a_tag.attrs:
                links.append(base_url + a_tag['href'])

    return links

def get_college_details(college_url, state):
    """Extracts details from a college page."""
    try:
        response = requests.get(college_url)
        soup = BeautifulSoup(response.content, 'html.parser')

        college_info = {
            "College Name": soup.find("h1").get_text(strip=True) if soup.find("h1") else "",
            "State": state.replace("-", " ").title()
        }

        email, phone, website, city, affiliation = "", "", "", "", ""

        table = soup.find("table")
        if table:
            rows = table.find_all("tr")
            for row in rows:
                columns = row.find_all(["th", "td"])
                if len(columns) == 2:
                    key = columns[0].get_text(strip=True)
                    value = clean_text(columns[1].get_text(strip=True))

                    if "City" in key:
                        city = value
                    if "Affiliated to" in key:
                        affiliation = value
                    if "Email" in key and "@" in value:
                        email = extract_email(value)
                    if "Phone" in key or "Contact" in key:
                        phone = extract_phone_numbers(value)
                    if "Website" in key:
                        website_link = columns[1].find("a", href=True)
                        if website_link:
                            website = website_link["href"].strip()

        full_text = soup.get_text()
        if not email:
            email = extract_email(full_text)
        if not phone:
            phone = extract_phone_numbers(full_text)

        college_info["City"] = city
        college_info["Affiliated to"] = affiliation
        college_info["Email"] = email if email else ""
        college_info["Phone"] = phone if phone else ""
        college_info["Website"] = website

        return college_info

    except Exception as e:
        print(f"Error retrieving information for {college_url}: {e}")
        return None

def scrape_state_colleges(state):
    """Scrapes all colleges for a given state and returns a list of dictionaries."""
    college_info_list = []
    college_links = get_college_links(state)

    for college_url in tqdm(college_links):
        college_info = get_college_details(college_url, state)
        if college_info:
            college_info_list.append(college_info)

    return college_info_list

"""## As we have scraped the information of by taking two states at a time or five states at a time"""

state_to_scrape = "karnataka"  # Change this to scrape a different state

college_data = scrape_state_colleges(state_to_scrape)

# Convert to DataFrame
df = pd.DataFrame(college_data)

# Keep only required columns
columns_to_keep = ['College Name', 'City', 'State', 'Affiliated to', 'Phone', 'Email', 'Website']
df = df.reindex(columns=columns_to_keep, fill_value="")

# Save to Excel
df.to_excel(f"{state_to_scrape}_College_Information.xlsx", index=False)

print(f"Data for {state_to_scrape} saved successfully!")

all_college_info = []
for state in states_ut:
    all_college_info.extend(scrape_state_colleges(state))

df = pd.DataFrame(all_college_info)
df.to_excel("All_States_College_Information.xlsx", index=False)

print("Scraping for all states completed!")

import os
import pandas as pd

def combine_xlsx_to_xlsx(file_paths, output_xlsx):
    with pd.ExcelWriter(output_xlsx, engine='openpyxl') as writer:
        for file in file_paths:
            df = pd.read_excel(file, engine='openpyxl')
            sheet_name = os.path.splitext(os.path.basename(file))[0][:31]
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"Combined {len(file_paths)} files into {output_xlsx}")


file_paths = [
    "/content/Andaman...dadarnagar.xlsx",
    "/content/Andhrapradesh_Arunachalpradesh.xlsx",
    "/content/Assam_Bihar.xlsx",
    "/content/Chhattishgarh_goa.xlsx",
    "/content/Delhi....Jammu.xlsx",
    "/content/Gujarat.....Nagaland.xlsx",
    "/content/Odisha...WestBengal.xlsx"
]
output_xlsx = "combined_output.xlsx"
combine_xlsx_to_xlsx(file_paths, output_xlsx)

