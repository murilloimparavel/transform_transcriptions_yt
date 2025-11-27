import os
import json
from pytube import Playlist
import ssl

def get_video_urls_from_playlist(playlist_url):
    """
    Recebe a URL de uma playlist do YouTube e retorna uma lista com as URLs dos vídeos.
    
    :param playlist_url: URL da playlist do YouTube
    :return: Lista de URLs dos vídeos na playlist
    """
    # Ignorar a verificação SSL
    ssl._create_default_https_context = ssl._create_unverified_context

    # Cria uma instância da Playlist
    playlist = Playlist(playlist_url)

    # Garante que todos os vídeos sejam carregados
    playlist._video_regex = r"\"url\":\"(/watch\?v=[\w-]*)"

    # Extrai as URLs completas dos vídeos (corrige URLs duplicadas)
    video_urls = []
    for video_url in playlist.video_urls:
        # Se já tiver o domínio completo, usa direto
        if video_url.startswith("https://"):
            video_urls.append(video_url)
        else:
            # Caso contrário, adiciona o domínio
            video_urls.append(f"https://www.youtube.com{video_url}")
    
    return video_urls

def save_playlist_to_json(playlist_url, language='en', output_file=None):
    """
    Salva as URLs dos vídeos de uma playlist do YouTube em um arquivo JSON.
    
    :param playlist_url: URL da playlist do YouTube
    :param language: Código do idioma desejado para a transcrição (ex: 'pt' para português, 'en' para inglês)
    :param output_file: Nome do arquivo JSON de saída
    """
    video_urls = get_video_urls_from_playlist(playlist_url)
    
    # Cria um dicionário com os dados
    data = {
        'playlist_url': playlist_url,
        'language': language,
        'videos': video_urls
    }

    # Define o diretório de saída e o nome do arquivo
    if output_file is None:
        output_dir = os.path.join('data', 'playlists')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'playlist_videos.json')

    # Salva o dicionário em um arquivo JSON
    with open(output_file, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)
    
    print(f"URLs dos vídeos e idioma salvos com sucesso em '{output_file}'")
    print(f"Total de vídeos salvos: {len(video_urls)}")

if __name__ == "__main__":
    # Solicita a URL da playlist e o idioma ao usuário
    playlist_url = input("Digite a URL da playlist do YouTube: ")
    language = input("Digite o código do idioma desejado (ex: 'pt' para português, 'en' para inglês): ")
    
    # Salva as URLs dos vídeos e o idioma em um arquivo JSON
    save_playlist_to_json(playlist_url, language)
