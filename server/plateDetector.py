import requests
from bs4 import BeautifulSoup
import os

class GetLicensePlateDemo:
    def __init__(self):
        self.session = requests.Session() 
        self.token = self.get_free_token()
        # print("Token generated:",self.token)   
        
    def get_free_token(self):
        res = self.session.get('https://app.platerecognizer.com/alpr-demo')
        soup = BeautifulSoup(res.text, 'html.parser')
        token = soup.find('input', {'name': 'csrfmiddlewaretoken'})["value"]
        return str(token) if token else None

    def get_license_img(self, file_src = None):
        if file_src == None:
            file_src = self.file_src
        files = {'upload': open(file_src,'rb')}
        data = {'csrfmiddlewaretoken': self.token}
        response  = self.session.post(
            "https://app.platerecognizer.com/alpr-demo", 
            params = data,
            files=files)
        soup = BeautifulSoup(response.text, 'html.parser')
        licenses = soup.find_all('ul', {'class': 'plate-items'})
        all_found_licenses = []
        for license in licenses:
            print(license.span.findAll("li")[1].text.strip())
            all_found_licenses.append(license.span.findAll("li")[1].text.strip())
        return all_found_licenses

if __name__ == "__main__":
    app = GetLicensePlateDemo()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(current_dir, 'public', 'images', 'bike.jpg')
    app.get_license_img(image_path)
    print("Finished")

    
