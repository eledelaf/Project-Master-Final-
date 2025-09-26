import requests
from bs4 import BeautifulSoup

def scrape_and_save_to_word(url, filename):
    try:
        # Realizar la solicitud HTTP a la URL
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Lanza un error para respuestas HTTP no exitosas

        # Analizar el contenido HTML de la página
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extraer todo el texto de la página como str
        text = soup.get_text(separator='\n', strip=True)

        # Devolver título y texto juntos
        return text

    except requests.exceptions.RequestException as e:
        print(f"Error al intentar acceder a la URL: {e}")
    except Exception as e:
        print(f"Ha ocurrido un error inesperado: {e}")
