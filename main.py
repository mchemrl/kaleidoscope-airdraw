import logging

from app import KaleidoscopeApp
from config import build_config

def main():
    config = build_config()
    logging.basicConfig(level=getattr(logging, config.log_level),
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    app = KaleidoscopeApp(config)
    app.run()

if __name__ == '__main__':
    main()