import requests
from bs4 import BeautifulSoup
import os
import pathlib
from track.helperFunctions import generate_random_vehicle_id

HOME_PATH = pathlib.Path(__file__).parent.parent

class GetLicensePlateDemo:
    IMAGE_PATH = HOME_PATH / 'public' / 'images'

    def __init__(self, isSimulate = False):
        self.isSimulate = isSimulate
        self.session = requests.Session() 
        self.token = self.get_free_token()
        self.licenses = {

        }
        
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
    
    def format_license(self, license):
        return license[:4] + "-" + license[4:]

    def get_licenses_by_key(self, key):
        if self.isSimulate:
            return generate_random_vehicle_id()
        # print("len ===========", len(os.listdir(GetLicensePlateDemo.IMAGE_PATH)))
        key = key % len(os.listdir(GetLicensePlateDemo.IMAGE_PATH))
        if key in self.licenses: return self.licenses[key]
        image_path = GetLicensePlateDemo.IMAGE_PATH / f'{key}.jpg'
        licenses = self.get_license_img(image_path)
        if licenses == []:
            print("May be you reach daily limit from web api")
            license = generate_random_vehicle_id()
        else:
            license = self.format_license(licenses[0])
        self.licenses[key] = license
        return license

if __name__ == "__main__":
    app = GetLicensePlateDemo()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(current_dir, 'public', 'images', '0.jpg')
    app.get_license_img(image_path)
    print("Finished")
