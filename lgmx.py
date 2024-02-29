import os
import requests
from tqdm import tqdm


class ResourceDownloader:
    @staticmethod
    def download_json(url):
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception("Failed to download JSON.")

    @staticmethod
    def download_file(url, path):
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_size_in_bytes = int(r.headers.get('content-length', 0))
            block_size = 1024  # 1 Kibibyte
            progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
            with open(path, 'wb') as file:
                for data in r.iter_content(block_size):
                    progress_bar.update(len(data))
                    file.write(data)
            progress_bar.close()
            if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
                raise Exception("ERROR, something went wrong")

    @staticmethod
    def process_file(gamefile, data, gamejson, assets_path):
        d = 0
        for i in range(gamejson['decjson'][gamefile]):
            b = data[d:d + 64]
            nl = int.from_bytes(b[:4], byteorder='big')
            n = b[4:4 + nl].decode('utf-8')
            fl = int.from_bytes(b[4 + nl:4 + nl + 4], byteorder='big')
            f = b[4 + nl + 4:4 + nl + 4 + fl].decode('utf-8')
            s = int.from_bytes(b[4 + nl + 4 + fl:4 + nl + 4 + fl + 4], byteorder='big')
            d += 4 + nl + 4 + fl + 4
            n = os.path.join(assets_path, f, n)
            dec = data[d:d + s]

            if dec.startswith(b'UnityFS'):
                deca = dec[:0x32]
                decb = dec[0x32:0x32 + 50]
                decc = dec[0x32 + 50:]
                key = decb[1]
                decd = bytes([decb[j] ^ key for j in range(50)])
                dec = deca + decd + decc

            os.makedirs(os.path.dirname(n), exist_ok=True)
            with open(n, 'wb') as file:
                file.write(dec)

            d += s


def main():
    url = 'https://l1-prod-patch-lgmx.bilibiligame.net/resource/AssetVersions/Android/CN/s657/packet_config'
    download_path = 'download_assets'
    assets_path = os.path.join(download_path, 'processed_assets')
    os.makedirs(assets_path, exist_ok=True)

    packet_config = ResourceDownloader.download_json(url)
    fileList = packet_config['list'][0]['fileList']

    gamejson = {'decjson': {}, 'gamepath': assets_path, 'gamename': 'game'}

    for file_info in fileList:
        name = file_info['name']
        count = file_info['count']
        gamejson['decjson'][name] = count

    for file_info in fileList:
        name = file_info['name']
        file_url = f'https://l1-prod-patch-lgmx.bilibiligame.net/resource/AssetVersions/Android/CN/s657/{name}'
        file_path = os.path.join(download_path, name)
        print(f"Downloading {name}...")
        ResourceDownloader.download_file(file_url, file_path)

        with open(file_path, 'rb') as f:
            data = f.read()

        ResourceDownloader.process_file(name, data, gamejson, assets_path)
        os.remove(file_path)


if __name__ == "__main__":
    main()
