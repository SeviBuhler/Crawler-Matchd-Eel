from bs4 import BeautifulSoup
import requests
import json
import urllib.parse

def crawl_abacus(crawler_instance, url, keywords):
        """Crawl function for Abacus API"""
        print(f"Crawling Abacus API URL: {url}")

        try:
            ### Make the API request
            response = requests.get(url, headers=crawler_instance.api_headers, timeout=10)

            ### Parse the response as a dictionary
            response_data = response.json()

            ### Check if 'html' key exists in the response
            if 'html' not in response_data:
                print("No HTML content found in the response")
                return [], None

            ### Parse the HTML content
            soup = BeautifulSoup(response_data['html'], 'html.parser')

            ### Look for job advertisement table or elements
            job_elements = soup.find_all('job-advertisement-table')

            content = []
            for job_element in job_elements:
                try:
                    ### Try to extract job data from the element's attributes
                    job_value = job_element.get('value', '')

                    ### URL decode the value
                    decoded_job_data = urllib.parse.unquote(job_value)

                    ### Parse the decoded job data
                    try:
                        jobs = json.loads(decoded_job_data)
                    except json.JSONDecodeError:
                        print(f"Failed to parse job data: {decoded_job_data[:500]}")
                        continue

                    ### Process each job
                    for job in jobs:
                        title = job.get('JobTitle', 'No title')
                        location = job.get('u_b_jobs_xxx__userfield1', 'No location')
                        link = job.get('PublicationUrlAbacusJobPortal', '#')

                        ### Check if any keyword is in the title and location is in Ostschweiz
                        if (any(keyword.lower() in title.lower() for keyword in keywords) and 
                            crawler_instance.is_location_in_ostschweiz(location) and
                            crawler_instance.is_it_job(title)):

                            job_entry = {
                                'title': title,
                                'link': link,
                                'company': 'Abacus',
                                'location': location,
                            }

                            content.append(job_entry)
                            print(f"Found matching job: {title}")
                        else:
                            print(f"Skipping non-matching job: {title}")

                except Exception as e:
                    print(f"Error processing job element: {e}")

            ### No pagination for this specific API
            next_url = None

            print(f"Found {len(content)} matching jobs")
            return content, next_url

        except requests.RequestException as e:
            print(f"Request error: {e}")
            return [], None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return [], None