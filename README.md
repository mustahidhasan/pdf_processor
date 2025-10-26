# pdf_processor
Processes the pdf and move forward to other site

# set up 
- `python3 -m venv env`
- `pip install -r requirements.txt`
- `cd document_processor`
- `python manage.py makemigrations`
- `python manage.py migrate`
- `python manage.py createsuperuser` (for the admin set up) 
- `python manage.py runserver`

# System dependency 👇

```bash
sudo apt update && sudo apt upgrade -y

# Core tools
sudo apt install -y python3 python3-pip python3-venv git nginx curl

# PDF & image processing dependencies
sudo apt install -y poppler-utils ghostscript libjpeg-dev zlib1g-dev libpng-dev

# Optional: for handling heavy PDFs or OCR
sudo apt install -y tesseract-ocr
```
