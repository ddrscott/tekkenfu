import hashlib
import logging
import json
import os
import urllib.request
from urllib.parse import urljoin

from bs4 import BeautifulSoup

start_url = 'https://tekken.fandom.com/wiki/Category:Tekken_5_Move_Lists'
move_selector = ','.join(
    ['.page-content table#moves tr',
     '.page-content table#attacks tr',
     '.page-content table#throws tr'
])
thumb_selector = 'img.pi-image-thumbnail'

tmp_dir = '.tmp'

def fetch(url):
    tmp_path = f"{tmp_dir}/{hashlib.md5(url.encode('utf-8')).hexdigest()}"
    if not os.path.isfile(tmp_path) or os.path.getsize(tmp_path) < 100:
        logging.info(f"downloading: {url}")
        urllib.request.urlretrieve(url, tmp_path)
    with open(tmp_path) as f:
        return f.read()


def fetch_characters(url=start_url):
    soup = BeautifulSoup(fetch(start_url), 'html.parser')
    links = soup.select('a.category-page__member-link')

    return [
      dict(
         name=u['title'].split('/')[0],
         href=urljoin(start_url, u['href']),
         snake=f"{u['href'].split('/')[2].lower()}"
      ) for u in links
    ]


def clean(elm):
    if elm and elm.text:
        return elm.text.strip()


def parse_moves(body):
    soup = BeautifulSoup(body, 'html.parser')
    for row in soup.select(move_selector):
        trs = row.select('th')
        move, command, damage, ranges, detail = [None] * 5
        if len(trs) == 4:
            move, command, damage, ranges = trs
            detail = move.select('a')
        elif len(trs) == 3:
            command, damage, ranges = trs
            detail = command.select('a')

        if detail:
            move_url = urljoin(start_url, detail[0]['href'])
            yield {
               'name': clean(detail[0]),
               'detail': move_url,
               'command': clean(command),
               'damage': clean(damage),
               'ranges': clean(ranges),
            }


def parse_image_url(body):
    soup = BeautifulSoup(body, 'html.parser')
    for img in soup.select(thumb_selector):
        yield img['src']
        break


def fetch_image_urls(moves):
    for move in moves:
        defail = fetch(move['detail'])
        for src in parse_image_url(defail):
            yield {**move, 'image_url': src}


def fetch_moves(url):
    move_page = fetch(url)
    moves = parse_moves(move_page)
    return list(fetch_image_urls(moves))


def image_path(href, image_dir='images'):
    base_name = hashlib.md5(href.encode('utf-8')).hexdigest()
    return os.path.join(image_dir, f"{base_name}.gif")


def ensure_local_image(href, image_dir='images'):
    dst = image_path(href, image_dir=image_dir)
    if not os.path.isfile(dst) or os.path.getsize(dst) < 100:
        logging.info(f'downloading: {href} to {dst}')
        urllib.request.urlretrieve(href, dst)
    return dst

def generate_json(src, dst):
    moves = fetch_moves(src)
    with open(dst, 'w') as f:
        json.dump(moves, f, indent=4)

def generate_html(src, dst, dst_json=None):
    logging.info(f"generating: {src}")
    moves = fetch_moves(src)
    if dst_json:
        with open(dst_json, 'w') as f:
            json.dump(moves, f, indent=4)

    with open(dst, 'w') as f:
        f.write(""" <!DOCTYPE html>
  <html>
    <head>
      <!--Import Google Icon Font-->
      <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
      <!--Import materialize.css-->
      <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0/css/materialize.min.css">

      <!--Let browser know website is optimized for mobile-->
      <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
      <style>
      .command {
          font-family: monospace;
          font-size: 1.25em;
          font-weight: bold;
      }
      </style>
    </head>
    <body>

      <!--JavaScript at end of body for optimized loading-->
      <script src="https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0/js/materialize.min.js"></script>
    <div class="row">
""")
        for move in moves:
            f.write(f"""
    <div class="col s12 m6 l4">
      <div class="card">
        <div class="card-image">
          <img src="../{ensure_local_image(move['image_url'])}" loading="lazy">
          <span class="card-title">{move['name']}</span>
        </div>
        <div class="card-content">
          <div class="command">{move['command']}</div>
          {move['ranges'].upper()}&nbsp;&nbsp;//&nbsp;&nbsp;{move['damage']}
        </div>
      </div>
    </div>
            """)

        f.write("""
</div>
</body>
</html>
    """)

def single():
    generate_json('https://tekken.fandom.com/wiki/Ganryu/Tekken_5_Movelist', f'pages/ganryu.json')

def main():
    logging.basicConfig(filename='run.log', filemode='a', level=logging.DEBUG)
    for character in fetch_characters():
        try:
            generate_json(character['href'], f'tekken5/{character["snake"]}.json')
        except Exception as e:
            logging.exception(e)

if __name__ == "__main__":
    main()
