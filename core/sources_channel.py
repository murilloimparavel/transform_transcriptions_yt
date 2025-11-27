import os
import json
import isodate
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Carrega as variáveis do .env
load_dotenv()

# Configura a API Key da YouTube Data API v3 usando a chave do .env
api_key = os.environ["YOUTUBE_API_KEY"]

# Inicializa o cliente da API
youtube = build("youtube", "v3", developerKey=api_key)

def get_channel_videos(channel_id):
    """
    Recebe o ID de um canal do YouTube e retorna uma lista com as informações dos vídeos,
    incluindo duração em segundos. Shorts (< 60s) são ignorados.
    Os vídeos retornados são ordenados do mais longo para o mais curto.
    """
    video_infos = []
    next_page_token = None

    while True:
        # Busca vídeos do canal
        request = youtube.search().list(
            part="snippet",
            channelId=channel_id,
            maxResults=50,
            pageToken=next_page_token,
            order="date",
            type="video"
        )
        response = request.execute()

        video_ids = [item["id"]["videoId"] for item in response.get("items", []) if item["id"]["kind"] == "youtube#video"]

        if video_ids:
            # Busca detalhes de duração
            details_request = youtube.videos().list(
                part="contentDetails,snippet",
                id=",".join(video_ids)
            )
            details_response = details_request.execute()

            for item in details_response.get("items", []):
                duration_iso = item["contentDetails"]["duration"]
                duration_seconds = int(isodate.parse_duration(duration_iso).total_seconds())

                # Ignora vídeos curtos (< 60s)
                if duration_seconds < 60:
                    continue

                video_info = {
                    "title": item["snippet"]["title"],
                    "url": f"https://www.youtube.com/watch?v={item['id']}",
                    "publishedAt": item["snippet"]["publishedAt"],
                    "description": item["snippet"].get("description", ""),
                    "duration_seconds": duration_seconds
                }
                video_infos.append(video_info)

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    # Ordena do mais longo para o mais curto
    video_infos.sort(key=lambda x: x["duration_seconds"], reverse=True)

    return video_infos

def save_channel_videos_to_json(channel_id, output_file=None):
    """
    Salva as informações dos vídeos de um canal do YouTube em um arquivo JSON.
    """
    video_infos = get_channel_videos(channel_id)

    data = {
        "channel_id": channel_id,
        "videos": video_infos
    }

    if output_file is None:
        output_dir = os.path.join("data", "playlists")
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "channel_videos.json")

    with open(output_file, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

    print(f"Informações dos vídeos do canal salvas com sucesso em '{output_file}'")
    print(f"Total de vídeos encontrados e salvos (≥ 60s): {len(video_infos)}")

def get_channel_id_by_name(channel_name):
    """
    Recebe o nome de um canal do YouTube e retorna o ID do canal.
    """
    request = youtube.search().list(
        part="snippet",
        q=channel_name,
        type="channel",
        maxResults=1
    )
    response = request.execute()

    if "items" in response and len(response["items"]) > 0:
        return response["items"][0]["snippet"]["channelId"]
    else:
        print(f"Não foi possível encontrar o canal com o nome: {channel_name}")
        return None

if __name__ == "__main__":
    channel_name = input("Digite o nome do canal do YouTube: ")
    channel_id = get_channel_id_by_name(channel_name)

    if channel_id:
        save_channel_videos_to_json(channel_id)
    else:
        print("Nenhum canal encontrado com o nome fornecido.")
