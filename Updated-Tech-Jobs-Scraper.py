# -*- coding: utf-8 -*-
"""
Created on Sat Mar  1 13:54:03 2025

@author: njosp
"""

import csv
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Print first statement
print("Fetching available jobs today.....")
time.sleep(3)  # Delay before the next statement

# Print next statement
print("Extracting and saving the latest job listings...")

# Set up Selenium
options = Options()
options.add_argument("--headless")  # Run in background
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# Load page
url = "https://www.swejobpostings.com/job-listings.html"
driver.get(url)
time.sleep(10)  # Wait for JavaScript to load

# Get page source after JavaScript executes
html = driver.page_source
driver.quit()

# Parse with BeautifulSoup
soup = BeautifulSoup(html, "html.parser")

# Extract job listings
jobs = soup.find_all("div", class_="job-card")

job_list = []
for job in jobs:  # Loop through each job card
    title = job.find("h3", class_="job-card-title").text.strip()

    # Get all <p> elements and join them into a single string
    description = " | ".join([p.text.strip() for p in job.find_all("p")])

    # Extract the job link correctly
    link = job.find("a", class_="btn btn-primary")
    job_url = link["href"] if link else "N/A"  # Get only the href attribute

    job_list.append([title, description, job_url])



# Generate a timestamped filename
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
filename = f"job_list_{timestamp}.csv"

# Save to CSV
with open(filename, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["JOB TITLE", "DESCRIPTION", "URL"])  # Headers
    writer.writerows(job_list)

# Print completion message
print("Your job list is ready.")
